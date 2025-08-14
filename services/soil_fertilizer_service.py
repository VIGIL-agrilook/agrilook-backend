import requests
import os
import json
import xmltodict
from dotenv import load_dotenv
from config.user_data import USER_DATA

# 환경변수 로드
load_dotenv()

class SoilFertilizerService:
    def get_raw_public_api_result(self, farm_info):
        """공공데이터포털 API 원본 결과 반환"""
        try:
            soil = farm_info['soil']
            params = {
                'serviceKey': self.api_key,
                'crop_Code': farm_info['crop_code'],
                'acid': soil.get('ph', 6.5),
                'om': soil.get('om', 22),
                'vldpha': soil.get('vldpha', 10),
                'posifert_K': soil.get('posifert_K', 4),
                'posifert_Ca': soil.get('posifert_Ca', 6),
                'posifert_Mg': soil.get('posifert_Mg', 13),
                'selc': soil.get('selc', 6)
            }
            response = requests.get(self.api_url, params=params, timeout=10)
            if response.status_code == 200:
                return response.text
            else:
                return {"error": "API response error", "status_code": response.status_code}
        except Exception as e:
            return {"error": str(e)}
    def get_recommendation_bundle(self):
        print("[DEBUG] get_recommendation_bundle called")
        """비료 추천 결과를 통합 구조로 반환 (프론트엔드용)"""
        farm_info = self.get_farm_info()
        fertilizer_data = self.fetch_fertilizer_api(farm_info)
        compost = self.get_compost_amounts(fertilizer_data, farm_info)
        nutrients = self.get_nutrient_requirements(fertilizer_data, farm_info)
        def simple_fert_list(fert_list):
            return [
                {
                    "id": fert.get("_id"),
                    "name": fert.get("name"),
                    "N": fert.get("grade", {}).get("N"),
                    "P2O5": fert.get("grade", {}).get("P2O5"),
                    "K2O": fert.get("grade", {}).get("K2O"),
                    "bag_kg": fert.get("bag_kg")
                }
                for fert in fert_list
            ]
        base_ferts = simple_fert_list(self.recommend_products(
            nutrients['base']['N'], nutrients['base']['P'], nutrients['base']['K'], "base", 3))
        add_ferts = simple_fert_list(self.recommend_products(
            nutrients['additional']['N'], nutrients['additional']['P'], nutrients['additional']['K'], "additional", 3))
        crop_name = farm_info.get('crop_name', '')
        farm = USER_DATA.get('farm', {})
        area_sqm = farm.get('area_m2', 0)
        farm_id = farm.get('_id', '')
        return {
            "compost": compost,
            "crop": {"name": crop_name},
            "fertilizer": {
                "base": base_ferts,
                "additional": add_ferts
            },
            "field": {
                "area_sqm": area_sqm,
                "id": farm_id
            }
        }
    def get_compost_amounts(self, fertilizer_data, farm_info):
        """퇴비 필요량 반환"""
        farm_size_10a = farm_info['farm_size_10a']
        print(f"[DEBUG] farm_size_10a: {farm_size_10a}")
        return {
            "cattle_kg": float(fertilizer_data.get('pre_Compost_Cattl', '0')) * farm_size_10a,
            "chicken_kg": float(fertilizer_data.get('pre_Compost_Chick', '0')) * farm_size_10a,
            "mixed_kg": float(fertilizer_data.get('pre_Compost_Mix', '0')) * farm_size_10a,
            "pig_kg": float(fertilizer_data.get('pre_Compost_Pig', '0')) * farm_size_10a,
        }
    def get_nutrient_requirements(self, fertilizer_data, farm_info):
        """농장 전체 양분 필요량 반환"""
        farm_size_10a = farm_info['farm_size_10a']
        return {
            'base': {
                'N': float(fertilizer_data.get('pre_Fert_N', '0')) * farm_size_10a,
                'P': float(fertilizer_data.get('pre_Fert_P', '0')) * farm_size_10a,
                'K': float(fertilizer_data.get('pre_Fert_K', '0')) * farm_size_10a
            },
            'additional': {
                'N': float(fertilizer_data.get('post_Fert_N', '0')) * farm_size_10a,
                'P': float(fertilizer_data.get('post_Fert_P', '0')) * farm_size_10a,
                'K': float(fertilizer_data.get('post_Fert_K', '0')) * farm_size_10a
            }
        }
    def fetch_fertilizer_api(self, farm_info):
        """공공데이터 API 호출"""
        try:
            soil = farm_info['soil']
            params = {
                'serviceKey': self.api_key,
                'crop_Code': farm_info['crop_code'],
                'acid': soil.get('ph', 6.5),
                'om': soil.get('om', 22),
                'vldpha': soil.get('vldpha', 10),
                'posifert_K': soil.get('posifert_K', 4),
                'posifert_Ca': soil.get('posifert_Ca', 6),
                'posifert_Mg': soil.get('posifert_Mg', 13),
                'selc': soil.get('selc', 6)
            }
            response = requests.get(self.api_url, params=params, timeout=10)
            if response.status_code == 200:
                parsed_data = self.parse_fertilizer_response(response.text)
                if parsed_data and parsed_data.get('success'):
                    return parsed_data
                else:
                    return self._get_test_data()
            else:
                return self._get_test_data()
        except Exception:
            return self._get_test_data()
    def __init__(self):
        """토양-비료 처방 서비스 (흙토람 스타일)"""
        self.api_key = os.getenv('FERTILIZER_API_KEY')
        self.api_url = "http://apis.data.go.kr/1390802/SoilEnviron/FrtlzrUseExp/getSoilFrtlzrExprnInfo"
    
    def parse_fertilizer_response(self, xml_content):
        """비료 추천 API의 XML 응답을 파싱하여 구조화된 데이터로 변환"""
        try:
            json_content = xmltodict.parse(xml_content)
            
            # 두 가지 응답 형태 처리
            if 'response' in json_content:
                # 일반적인 response 구조
                response_data = json_content.get('response', {})
                header = response_data.get('header', {})
                result_code = header.get('result_Code') or header.get('resultCode')
                result_msg = header.get('result_Msg') or header.get('resultMsg')
                
                if result_code != '200' and result_code != 200:
                    return None
                
                # body에서 items 추출
                body = response_data.get('body', {})
                items = body.get('items', {})
                
                if isinstance(items, dict) and 'item' in items:
                    item_data = items['item']
                    if isinstance(item_data, list) and len(item_data) > 0:
                        item = item_data[0]
                    else:
                        item = item_data
                else:
                    item = items
                    
            elif 'OpenAPI_ServiceResponse' in json_content:
                # OpenAPI 응답 구조
                service_response = json_content.get('OpenAPI_ServiceResponse', {})
                header = service_response.get('cmmMsgHeader', {})
                
                error_msg = header.get('errMsg', '')
                
                if error_msg == 'SERVICE ERROR':
                    return None
                
                # OpenAPI body 처리
                body = service_response.get('body', {})
                items = body.get('items', {})
                
                if isinstance(items, dict) and 'item' in items:
                    item = items['item']
                else:
                    item = items
            else:
                return None
            
            # item이 비어있거나 None인 경우 처리
            if not item:
                return None
            
            result = {
                'success': True,
                'result_Code': '200',
                'result_Msg': 'OK',
                'crop_Code': item.get('crop_Code', ''),
                'crop_Nm': item.get('crop_Nm', ''),
                'pre_Fert_N': item.get('pre_Fert_N', '0'),
                'pre_Fert_P': item.get('pre_Fert_P', '0'),
                'pre_Fert_K': item.get('pre_Fert_K', '0'),
                'post_Fert_N': item.get('post_Fert_N', '0'),
                'post_Fert_P': item.get('post_Fert_P', '0'),
                'post_Fert_K': item.get('post_Fert_K', '0'),
                'pre_Compost_Cattl': item.get('pre_Compost_Cattl', '0'),
                'pre_Compost_Pig': item.get('pre_Compost_Pig', '0'),
                'pre_Compost_Chick': item.get('pre_Compost_Chick', '0'),
                'pre_Compost_Mix': item.get('pre_Compost_Mix', '0')
            }
            
            return result
            
        except Exception as e:
            return None
    
    def get_farm_info(self):
        """농장 정보 가져오기 (면적 a 단위 직접 계산)"""
        farm = USER_DATA.get('farm', {})
        area_m2 = farm.get('area_m2', 25000)  # 기본값 25,000㎡
        farm_size_a = area_m2 / 100  # 100㎡ = 1a
        farm_size_10a = farm_size_a / 10  # 10a 단위로 변환
        crops = farm.get('crops', [])
        current_crop = crops[0] if crops else {}
        from config.crop_codes import get_crop_code
        crop_name = current_crop.get('cropname', '맥주보리')
        crop_code = get_crop_code(crop_name) or '01001'
        return {
            'farm_size_a': farm_size_a,
            'farm_size_10a': farm_size_10a,
            'crop_code': crop_code,
            'crop_name': crop_name,
            'soil': USER_DATA.get('soil', {})
        }
    
    def recommend_products(self, target_n, target_p, target_k, fertilizer_type="base", top_n=2):
        """NPK 기준 비료 추천"""
        try:
            fertilizer_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'fertilizers.json')
            
            if not os.path.exists(fertilizer_file):
                return []
            
            with open(fertilizer_file, 'r', encoding='utf-8') as f:
                all_fertilizers = json.load(f)
            
            # 단계에 따른 비료 필터링
            filtered_fertilizers = []
            stage_key = "basal" if fertilizer_type == "base" else "topdress"
            
            for fert in all_fertilizers:
                if stage_key in fert.get("stage", []):
                    filtered_fertilizers.append(fert)
            
            if not filtered_fertilizers:
                return []
            
            # 질소 함량이 있는 비료만 필터링
            nitrogen_fertilizers = [f for f in filtered_fertilizers 
                                   if float(f.get('grade', {}).get('N', 0)) > 0]
            
            # NPK 비율 점수 계산
            scored_fertilizers = []
            for fert in nitrogen_fertilizers:
                grade = fert.get('grade', {})
                n_diff = abs(float(grade.get('N', 0)) - target_n)
                p_diff = abs(float(grade.get('P2O5', 0)) - target_p) 
                k_diff = abs(float(grade.get('K2O', 0)) - target_k)
                score = n_diff + p_diff + k_diff
                
                fert_copy = fert.copy()
                fert_copy['추천점수'] = round(score, 1)
                scored_fertilizers.append(fert_copy)
            
            # 점수 순 정렬
            scored_fertilizers.sort(key=lambda x: x['추천점수'])
            return scored_fertilizers[:top_n]
            
        except Exception as e:
            print(f"⚠️ 비료 추천 오류: {e}")
            return []
    
    def get_fertilizer_usage(self, fertilizer, total_n_needed, total_p_needed, total_k_needed, farm_size_a=None):
        """전체 농장 양분 기준 비료 사용량 반환"""
        try:
            # 새 구조에서 데이터 추출
            grade = fertilizer.get('grade', {})
            fert_n = float(grade.get('N', 0))
            fert_p = float(grade.get('P2O5', 0))  
            fert_k = float(grade.get('K2O', 0))
            bag_weight = float(fertilizer.get('bag_kg', 20))
            fertilizer_id = fertilizer.get('_id', '')
            fertilizer_name = fertilizer.get('name', '')
            
            if fert_n == 0:
                return None
            
            # 질소 기준으로 총 비료 사용량 계산
            total_usage_kg = total_n_needed / (fert_n / 100)
            bags = total_usage_kg / bag_weight
            
            # 부족분 계산
            supplied_p = total_usage_kg * (fert_p / 100)
            supplied_k = total_usage_kg * (fert_k / 100)
            shortage_p = max(0, total_p_needed - supplied_p)
            shortage_k = max(0, total_k_needed - supplied_k)
            
            return {
                'fertilizer_id': fertilizer_id,
                'fertilizer_name': fertilizer_name,
                'usage_kg': round(total_usage_kg, 1),
                'bags': round(bags, 1),
                'shortage_p': round(shortage_p, 1),
                'shortage_k': round(shortage_k, 1)
            }
        except Exception as e:
            print(f"비료 사용량 계산 오류: {e}")
            return None
    
    def display_fertilizer_recommendations(self, nutrient_needs):
        """비료 추천 출력"""
        print(f"\n🎯 추천 비료")
        print("=" * 50)
        
        # 밑거름 추천
        base_recs = self.recommend_fertilizers(
            nutrient_needs['base']['N'], 
            nutrient_needs['base']['P'], 
            nutrient_needs['base']['K'],
            "base", 3
        )
        
        print(f"🌱 밑거름 추천")
        for i, fert in enumerate(base_recs, 1):
            usage = self.calculate_fertilizer_usage(
                fert, 
                float(nutrient_needs['base']['N']) / 250,  # 1a당 필요량으로 변환
                float(nutrient_needs['base']['P']) / 250,
                float(nutrient_needs['base']['K']) / 250,
                250  # 250a
            )
            
            print(f"  {i}. {fert['비료종류']} (N-{fert['질소']}% P-{fert['인산']}% K-{fert['칼리']}%)")
            if usage:
                print(f"     사용량: {usage['usage_kg']}kg ({usage['bags']}포대)")
                if usage['shortage_p'] > 0 or usage['shortage_k'] > 0:
                    shortages = []
                    if usage['shortage_p'] > 0:
                        shortages.append(f"인산 {usage['shortage_p']}kg")
                    if usage['shortage_k'] > 0:
                        shortages.append(f"칼륨 {usage['shortage_k']}kg")
                    print(f"     추가필요: {', '.join(shortages)}")
        
        # 웃거름 추천
        add_recs = self.recommend_fertilizers(
            nutrient_needs['additional']['N'],
            nutrient_needs['additional']['P'], 
            nutrient_needs['additional']['K'],
            "additional", 3
        )
        
        print(f"\n🌿 웃거름 추천")
        for i, fert in enumerate(add_recs, 1):
            usage = self.calculate_fertilizer_usage(
                fert,
                float(nutrient_needs['additional']['N']) / 250,
                float(nutrient_needs['additional']['P']) / 250,
                float(nutrient_needs['additional']['K']) / 250,
                250
            )
            
            print(f"  {i}. {fert['비료종류']} (N-{fert['질소']}% P-{fert['인산']}% K-{fert['칼리']}%)")
            if usage:
                print(f"     사용량: {usage['usage_kg']}kg ({usage['bags']}포대)")
                if usage['shortage_p'] > 0 or usage['shortage_k'] > 0:
                    shortages = []
                    if usage['shortage_p'] > 0:
                        shortages.append(f"인산 {usage['shortage_p']}kg")
                    if usage['shortage_k'] > 0:
                        shortages.append(f"칼륨 {usage['shortage_k']}kg")
                    print(f"     추가필요: {', '.join(shortages)}")
