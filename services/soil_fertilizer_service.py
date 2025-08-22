import os
import requests
import xmltodict
from dotenv import load_dotenv
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.user_data import USER_DATA
from config.crop_codes import get_crop_code
import pymongo
import math
import logging

logging.basicConfig(level=logging.INFO)

load_dotenv()

class SoilFertilizerService:
    def __init__(self):
        self.api_key = os.getenv('FERTILIZER_API_KEY')
        if not self.api_key:
            raise RuntimeError("FERTILIZER_API_KEY not set in environment")
        self.api_url = "http://apis.data.go.kr/1390802/SoilEnviron/FrtlzrUseExp/getSoilFrtlzrExprnInfo"

    # ====== 공개 메인 ======
    def get_recommendation_bundle(self):
        """프론트에서 바로 쓰는 통합 구조"""
        farm_info = self.get_farm_info()
        fert_api = self.fetch_fertilizer_api(farm_info)  # XML→dict (kg/10a 단위)
        compost = self.get_compost_amounts(fert_api, farm_info)
        needs = self.get_nutrient_requirements(fert_api, farm_info)  # 전체 면적 스케일링 반영

        # 추천 (부족분 총합 최솟값 기준)
        base_raw = self.recommend_products(needs['base']['N'], needs['base']['P'], needs['base']['K'], "base", 3)
        add_raw  = self.recommend_products(needs['additional']['N'], needs['additional']['P'], needs['additional']['K'], "additional", 3)

        # 프론트가 필요한 핵심 수치 포함해서 내보냄
        def to_simple(items):
            out = []
            for f in items:
                g = f.get("grade", {})
                out.append({
                    "id": f.get("_id"),
                    "name": f.get("name"),
                    "N": g.get("N"),
                    "P2O5": g.get("P2O5"),
                    "K2O": g.get("K2O"),
                    "bag_kg": f.get("bag_kg"),
                    "usage_kg": f.get("usage_kg"),
                    "bags": f.get("bags"),
                    "shortage_P_kg": f.get("shortage_P_kg"),
                    "shortage_K_kg": f.get("shortage_K_kg"),
                    "total_shortage": f.get("total_shortage"),
                })
            return out

        return {
            "compost": compost,
            "crop": {"name": farm_info.get("crop_name", "")},
            "fertilizer": {
                "base": to_simple(base_raw),
                "additional": to_simple(add_raw),
            },
            "field": {
                "area_sqm": farm_info.get("area_m2", 0),
                "area_a": farm_info.get("farm_size_a", 0),     # 편의 파생값
                "area_10a": farm_info.get("farm_size_10a", 0), # 편의 파생값
                "id": USER_DATA.get("farm", {}).get("_id", "")
            }
        }

    # ====== API 호출/파싱 ======
    def fetch_fertilizer_api(self, farm_info):
        """흙토람 체험 API 호출 → dict (단위: kg/10a)"""
        soil = farm_info['soil']
        ph = float(soil.get('pH', 6.5) or 6.5)
        om = float(soil.get('OM', 22) or 22)
        vldpha = float(soil.get('P', 10) or 10)
        posifert_K = float(soil.get('K', 4) or 4)
        posifert_Ca = float(soil.get('Ca', 6) or 6)
        posifert_Mg = float(soil.get('Mg', 13) or 13)
        selc = float(soil.get('EC', 6) or 6)
        # crop_code를 str로 변환 (API에는 문자열 코드로 전달)
        crop_code_raw = farm_info.get('crop_code')
        crop_code = str(crop_code_raw)
        params = {
            'serviceKey': self.api_key,
            'crop_Code': crop_code,
            'acid': ph,
            'om': om,
            'vldpha': vldpha,
            'posifert_K': posifert_K,
            'posifert_Ca': posifert_Ca,
            'posifert_Mg': posifert_Mg,
            'selc': max(3, selc),
        }
        r = requests.get(self.api_url, params=params, timeout=10)
        # logging.debug 수준의 디버그 로그 제거
        r.raise_for_status()
        parsed = self.parse_fertilizer_response(r.text)
        # logging.debug 수준의 디버그 로그 제거
        return parsed if parsed and parsed.get('success') else {}

    def parse_fertilizer_response(self, xml_content):
        """XML → dict (키 대소문자 혼용 대비)"""
        try:
            j = xmltodict.parse(xml_content)

            # 공통적으로 item 노드를 찾아 꺼내기
            item = None
            if 'response' in j:
                body = j['response'].get('body', {})
                items = body.get('items', {})
                item = items.get('item', items)
                if isinstance(item, list):
                    item = item[0] if item else None
            elif 'OpenAPI_ServiceResponse' in j:
                body = j['OpenAPI_ServiceResponse'].get('body', {})
                items = body.get('items', {})
                item = items.get('item', items)
            if not item:
                return None

            # 대소문자 키 혼용 대비
            def g(d, *keys, default='0'):
                for k in keys:
                    if k in d: return d[k]
                return default

            result = {
                'success': True,
                'result_Code': '200',
                'result_Msg': 'OK',
                'crop_Code': g(item, 'crop_Code', 'Crop_Code', default=''),
                'crop_Nm':   g(item, 'crop_Nm',   'Crop_Nm',   default=''),
                'pre_Fert_N': g(item, 'pre_Fert_N'),
                'pre_Fert_P': g(item, 'pre_Fert_P'),
                'pre_Fert_K': g(item, 'pre_Fert_K'),
                'post_Fert_N': g(item, 'post_Fert_N'),
                'post_Fert_P': g(item, 'post_Fert_P'),
                'post_Fert_K': g(item, 'post_Fert_K'),
                'pre_Compost_Cattl': g(item, 'pre_Compost_Cattl'),
                'pre_Compost_Pig':   g(item, 'pre_Compost_Pig'),
                'pre_Compost_Chick': g(item, 'pre_Compost_Chick'),
                'pre_Compost_Mix':   g(item, 'pre_Compost_Mix'),
            }
            return result
        except Exception:
            return None

    # ====== 면적/요구량 계산 ======
    def get_farm_info(self):
        """면적 환산 포함 (a, 10a 파생값 제공)"""
        farm = USER_DATA.get('farm', {})
        area_m2 = farm.get('area_m2', 250)   # 기본 250㎡(=2.5a)로 안전값
        farm_size_a = area_m2 / 100.0
        farm_size_10a = farm_size_a / 10.0
        crops = farm.get('crops', [])
        cur = crops[0] if crops else {}
        crop_name = cur.get('cropname', '맥주보리')
        crop_code = get_crop_code(crop_name) or '01001'
        return {
            'area_m2': area_m2,
            'farm_size_a': farm_size_a,
            'farm_size_10a': farm_size_10a,
            'crop_code': crop_code,
            'crop_name': crop_name,
            'soil': USER_DATA.get('soil', {})
        }

    def get_compost_amounts(self, api_data, farm_info):
        """퇴비 kg → 면적 스케일링 (API는 kg/10a 기준)"""
        s = farm_info['farm_size_10a']
        f = lambda v: float(api_data.get(v, '0')) * s
        return {
            "cattle_kg": f('pre_Compost_Cattl'),
            "chicken_kg": f('pre_Compost_Chick'),
            "pig_kg": f('pre_Compost_Pig'),
            "mixed_kg": f('pre_Compost_Mix'),

        }

    def get_nutrient_requirements(self, api_data, farm_info):
        """N, P2O5, K2O 필요량(kg) → 전체 면적 스케일링"""
        s = farm_info['farm_size_10a']
        f = lambda k: float(api_data.get(k, '0')) * s
        base_N = f('pre_Fert_N')
        base_P = f('pre_Fert_P')
        base_K = f('pre_Fert_K')
        add_N = f('post_Fert_N')
        add_P = f('post_Fert_P')
        add_K = f('post_Fert_K')
        # logging.debug 수준의 디버그 로그 제거
        return {
            'base': {
                'N': base_N,
                'P': base_P,
                'K': base_K,
            },
            'additional': {
                'N': add_N,
                'P': add_P,
                'K': add_K,
            }
        }

    # ====== 비료 추천(DB) ======
    def recommend_products(self, target_n, target_p, target_k, fertilizer_type="base", top_n=3):
        MONGO_URI = os.getenv("MONGO_URI")
        DB_NAME = os.getenv("DB_NAME")
        client = pymongo.MongoClient(MONGO_URI)
        try:
            db = client[DB_NAME]
            col = db["fertilizers"]

            stage_keys = ["basal","base","밑거름"] if fertilizer_type=="base" else ["topdress","additional","추비"]
            query = {"stage": {"$in": stage_keys}, "grade.N": {"$exists": True}}
            docs = list(col.find(query))

            # 디버그 프린트 제거
            results = []
            for fert in docs:
                g = fert.get("grade", {}) or {}
                try:
                    n = float(g.get('N', 0) or 0)
                    p = float(g.get('P2O5', 0) or 0)
                    k = float(g.get('K2O', 0) or 0)
                    bag = float(fert.get('bag_kg', 20) or 20)
                except Exception as e:
                    # 디버그 로그 제거
                    continue
                if (n+p+k) <= 0:
                    # 디버그 로그 제거
                    continue

                # 성분 비율 정규화 및 거리 계산 (내부 계산용)
                ft = n+p+k
                fn, fp, fk = n/ft, p/ft, k/ft

                # 실제 사용량/포대수/부족량 계산
                usage_kg = target_n / (n/100.0) if n > 0 else 0.0
                bags = usage_kg / bag if bag > 0 else 0.0
                supplied_p = usage_kg * (p/100.0)
                supplied_k = usage_kg * (k/100.0)
                short_p = max(0.0, target_p - supplied_p)
                short_k = max(0.0, target_k - supplied_k)
                if short_p < 0 or short_k < 0:
                    # 디버그 로그 제거
                    continue
                # 디버그 로그 제거
                results.append({
                    "_id": fert.get("_id",""),
                    "name": fert.get("name",""),
                    "grade": g,
                    "bag_kg": bag,
                    "usage_kg": round(usage_kg, 2),
                    "bags": round(bags, 2),
                    "shortage_P_kg": round(short_p, 2),
                    "shortage_K_kg": round(short_k, 2),
                    "total_shortage": round(short_p + short_k, 2)
                })

            # 거리 기준 정렬 제거, 단순 부족분/사용량/포대수 기준 정렬
            results.sort(key=lambda x: (x["shortage_P_kg"], x["shortage_K_kg"], x["bags"], x["usage_kg"]))
            return results[:top_n]
        finally:
            client.close()

    def build_front_payload(self, cropname: str, farmid: str) -> dict:
        """
        프론트 요구 스키마로 변환:
        - 밑거름 3개, 웃거름 3개 추천 (usage_kg, bags, shortage_* 포함)
        - 성분비(질량비) N_ratio/P_ratio/K_ratio 포함 (예: 13% -> 0.13)
        - need_*_kg: 해당 단계(stage)의 '필요량(kg)'을 그대로 표기
        """
        # 1) 농장/작물 컨텍스트
        farm_info = self.get_farm_info()
        # 호출자가 준 cropname/farmid를 반영 (get_farm_info 기본값 보정)
        farm_info["crop_name"] = cropname
        farm_info["crop_code"] = get_crop_code(cropname) or farm_info.get("crop_code")
        area_10a = farm_info["farm_size_10a"]

        # 2) API 호출 (단위: kg/10a)
        fert_api = self.fetch_fertilizer_api(farm_info)

        # 3) 퇴비/필요양분 계산 (면적 스케일링 반영)
        compost = self.get_compost_amounts(fert_api, farm_info)
        needs = self.get_nutrient_requirements(fert_api, farm_info)  # {'base':{N,P,K}, 'additional':{...}}

        # 4) 추천 비료 목록 조회
        base_raw = self.recommend_products(needs['base']['N'], needs['base']['P'], needs['base']['K'], "base", 3)
        add_raw  = self.recommend_products(needs['additional']['N'], needs['additional']['P'], needs['additional']['K'], "additional", 3)

        # 5) 공통 변환기: 추천 결과 → 프론트 카드
        def to_cards(items, needN, needP, needK):
            cards = []
            for f in items:
                g = f.get("grade", {})
                n = float(g.get("N", 0) or 0)
                p = float(g.get("P2O5", 0) or 0)
                k = float(g.get("K2O", 0) or 0)
                bag = float(f.get("bag_kg", 20) or 20)

                usage_kg = needN / (n/100.0) if n > 0 else 0.0
                bags = usage_kg / bag if bag > 0 else 0.0
                supplied_p = usage_kg * (p/100.0)
                supplied_k = usage_kg * (k/100.0)
                shortage_p = max(0.0, needP - supplied_p)
                shortage_k = max(0.0, needK - supplied_k)

                card = {
                    "K_ratio": round(k/100.0, 4),
                    "N_ratio": round(n/100.0, 4),
                    "P_ratio": round(p/100.0, 4),
                    "bags": round(bags, 2),
                    "fertilizer_id": str(f.get("_id") or ""),
                    "fertilizer_name": f.get("name"),
                    "need_K_kg": round(float(needK), 3),
                    "need_N_kg": round(float(needN), 3),
                    "need_P_kg": round(float(needP), 3),
                    "shortage_K_kg": round(shortage_k, 3),
                    "shortage_P_kg": round(shortage_p, 3),
                    "usage_kg": round(usage_kg, 2),
                }
                # Ensure crop name is not included in card
                card.pop("crop_name", None)
                cards.append(card)
            return cards

        base_cards = to_cards(base_raw, needs['base']['N'], needs['base']['P'], needs['base']['K'])
        add_cards  = to_cards(add_raw,  needs['additional']['N'], needs['additional']['P'], needs['additional']['K'])

        # 6) 최종 스키마 조립
        payload = {
            "_id": f"{farmid}_{farm_info.get('crop_code','')}",
            "crop": {
                "code": farm_info.get("crop_code", ""),
                "name": farm_info.get("crop_name", cropname)
            },
            "compost": {
                "cattle_kg": round(float(compost["cattle_kg"]), 3),
                "chicken_kg": round(float(compost["chicken_kg"]), 3),
                "mixed_kg": round(float(compost["mixed_kg"]), 3),
                "pig_kg": round(float(compost["pig_kg"]), 3)
            },
            "fertilizer": {
                "base": base_cards,
                "additional": add_cards
            }
        }
        return payload
