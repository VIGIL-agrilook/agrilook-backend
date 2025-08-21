import os
import requests
import xmltodict
from dotenv import load_dotenv
import sys
import re
import traceback
import logging
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.user_data import USER_DATA
from config.crop_codes import get_crop_code
import pymongo
import math


load_dotenv()
logger = logging.getLogger(__name__)

class SoilFertilizerService:
    def __init__(self):
        self.api_key = os.getenv('FERTILIZER_API_KEY')
        if not self.api_key:
            raise RuntimeError("FERTILIZER_API_KEY not set in environment")
        self.api_url = "http://apis.data.go.kr/1390802/SoilEnviron/FrtlzrUseExp/getSoilFrtlzrExprnInfo"
        self.debug = os.getenv('FERTILIZER_API_DEBUG', '0') == '1'

    # ====== 내부 유틸 ======
    def _parse_number_or_range(self, value, default=None):
        if value is None:
            return default
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            nums = re.findall(r"[-+]?\d*\.?\d+", value.replace(",", ""))
            if not nums:
                return default
            try:
                floats = [float(n) for n in nums]
            except Exception:
                return default
            if len(floats) == 1:
                return floats[0]
            return sum(floats[:2]) / 2.0
        return default

    def _soil_value(self, soil: dict, candidate_keys, default=None):
        for k in candidate_keys:
            if k in soil and soil.get(k) not in (None, ""):
                return self._parse_number_or_range(soil.get(k), default)
        return default

    # (구) 라우트 호환 유틸은 제거되었습니다.

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
        # 현실적인 안전 기본값(센서 부재 시 재시도용)
        typical = {
            'acid': 6.5,     # pH
            'om': 22.0,      # g/kg
            'vldpha': 120.0, # mg/kg (유효인산)
            'posifert_K': 0.55, # cmol+/kg (치환성칼리)
            'posifert_Ca': 6.8, # cmol+/kg
            'posifert_Mg': 2.1, # cmol+/kg
            'selc': 1.2,        # dS/m (EC)
        }

        params = {
            'serviceKey': self.api_key,
            'crop_Code': farm_info.get('crop_code'),
            'acid': self._soil_value(soil, ['ph', 'pH'], typical['acid']),
            'om': self._soil_value(soil, ['om', 'OM'], typical['om']),
            'vldpha': self._soil_value(soil, ['vldpha', 'P'], typical['vldpha']),
            'posifert_K': self._soil_value(soil, ['posifert_K', 'K'], typical['posifert_K']),
            'posifert_Ca': self._soil_value(soil, ['posifert_Ca', 'Ca'], typical['posifert_Ca']),
            'posifert_Mg': self._soil_value(soil, ['posifert_Mg', 'Mg'], typical['posifert_Mg']),
            'selc': self._soil_value(soil, ['selc', 'EC'], typical['selc']),
        }
        try:
            if self.debug:
                safe_params = dict(params)
                if 'serviceKey' in safe_params:
                    safe_params['serviceKey'] = '***'
                logger.debug("[FERT_API] params: %s", safe_params)
            r = requests.get(self.api_url, params=params, timeout=10)
            if self.debug:
                logger.debug("[FERT_API] status: %s, bytes: %s", r.status_code, len(r.text))
            r.raise_for_status()
            parsed = self.parse_fertilizer_response(r.text)
            ok = bool(parsed and parsed.get('success'))
            if self.debug:
                logger.debug("[FERT_API] parsed success: %s", ok)
                if not ok:
                    # 응답 전문을 일부 노출해 원인 파악
                    snippet = r.text[:500]
                    logger.debug("[FERT_API] response snippet: %s", snippet)
            if ok:
                return parsed

            # 재시도: 전부 전형값으로 강제
            retry_params = {
                'serviceKey': self.api_key,
                'crop_Code': farm_info.get('crop_code'),
                'acid': typical['acid'],
                'om': typical['om'],
                'vldpha': typical['vldpha'],
                'posifert_K': typical['posifert_K'],
                'posifert_Ca': typical['posifert_Ca'],
                'posifert_Mg': typical['posifert_Mg'],
                'selc': typical['selc'],
            }
            if self.debug:
                safe_retry_params = dict(retry_params)
                if 'serviceKey' in safe_retry_params:
                    safe_retry_params['serviceKey'] = '***'
                logger.debug("[FERT_API] RETRY with typical params: %s", safe_retry_params)
            r2 = requests.get(self.api_url, params=retry_params, timeout=10)
            if self.debug:
                logger.debug("[FERT_API] retry status: %s, bytes: %s", r2.status_code, len(r2.text))
            r2.raise_for_status()
            parsed2 = self.parse_fertilizer_response(r2.text)
            ok2 = bool(parsed2 and parsed2.get('success'))
            if self.debug:
                logger.debug("[FERT_API] retry parsed success: %s", ok2)
                if not ok2:
                    logger.debug("[FERT_API] retry response snippet: %s", r2.text[:500])
            return parsed2 if ok2 else {}
        except Exception as e:
            if self.debug:
                logger.exception("[FERT_API] ERROR during fetch")
            return {}

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
        except Exception as e:
            if getattr(self, 'debug', False):
                logger.exception("[FERT_API] parse error")
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
        return {
            'base': {
                'N': f('pre_Fert_N'),
                'P': f('pre_Fert_P'),
                'K': f('pre_Fert_K'),
            },
            'additional': {
                'N': f('post_Fert_N'),
                'P': f('post_Fert_P'),
                'K': f('post_Fert_K'),
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

            total_target = target_n + target_p + target_k
            if total_target <= 0:
                return []
            tn, tp, tk = target_n/total_target, target_p/total_target, target_k/total_target

            results = []
            for fert in docs:
                g = fert.get("grade", {}) or {}
                try:
                    n = float(g.get('N', 0) or 0)
                    p = float(g.get('P2O5', 0) or 0)
                    k = float(g.get('K2O', 0) or 0)
                    bag = float(fert.get('bag_kg', 20) or 20)
                except Exception:
                    continue
                if (n+p+k) <= 0:
                    continue

                # 성분 비율 정규화 및 거리 계산 (내부 계산용)
                ft = n+p+k
                fn, fp, fk = n/ft, p/ft, k/ft
                dist = math.sqrt((tn-fn)**2 + (tp-fp)**2 + (tk-fk)**2)

                # 실제 사용량/포대수/부족량 계산
                usage_kg = target_n / (n/100.0) if n > 0 else 0.0
                bags = usage_kg / bag if bag > 0 else 0.0
                supplied_p = usage_kg * (p/100.0)
                supplied_k = usage_kg * (k/100.0)
                short_p = max(0.0, target_p - supplied_p)
                short_k = max(0.0, target_k - supplied_k)

                # 부족분이 0보다 작은 경우(과잉) 추천에서 제외
                if short_p < 0 or short_k < 0:
                    continue
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

            # 거리 기준 정렬
            def npk_distance(x):
                g = x['grade']
                n = float(g.get('N', 0) or 0)
                p = float(g.get('P2O5', 0) or 0)
                k = float(g.get('K2O', 0) or 0)
                total = n + p + k
                if total <= 0:
                    return float('inf')
                fn, fp, fk = n/total, p/total, k/total
                return math.sqrt((tn-fn)**2 + (tp-fp)**2 + (tk-fk)**2)
            results.sort(key=npk_distance)
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
