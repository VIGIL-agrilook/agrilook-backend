import requests
import os
import json
import xmltodict
from dotenv import load_dotenv
from config.user_data import USER_DATA

# 환경변수 로드
load_dotenv()

class SoilFertilizerService:
    def __init__(self):
        """토양-비료 처방 서비스 (흙토람 스타일)"""
        self.api_key = os.getenv('FERTILIZER_API_KEY')
        self.api_url = "http://apis.data.go.kr/1390802/SoilEnviron/FrtlzrUseExp/getSoilFrtlzrExprnInfo"
    
    def parse_fertilizer_response(self, xml_content):
        """비료 추천 API의 XML 응답을 파싱하여 구조화된 데이터로 변환"""
        try:
            json_content = xmltodict.parse(xml_content)
            
            # response 구조로 파싱
            response_data = json_content.get('response', {})
            
            # 헤더 체크
            header = response_data.get('header', {})
            if header.get('result_Code') != '200':
                print(f"⚠️ API 오류: {header.get('result_Msg', 'Unknown error')}")
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
            
            result = {
                'success': True,
                'result_Code': header.get('result_Code', '200'),
                'result_Msg': header.get('result_Msg', 'OK'),
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
        """농장 정보 가져오기"""
        farm_size_a = USER_DATA.get('farm_size_a', 100)  # a 단위
        farm_size_10a = farm_size_a / 10  # 10a 단위로 변환 (10a = 1ha = 1000㎡)
        
        return {
            'farm_size_a': farm_size_a,
            'farm_size_10a': farm_size_10a,
            'crop_code': USER_DATA.get('crop', {}).get('code', '01001'),
            'crop_name': USER_DATA.get('crop', {}).get('name', '맥주보리'),
            'soil': USER_DATA.get('soil', {})
        }
    
    def call_fertilizer_api(self, farm_info):
        """공공데이터 API 호출"""
        print(f"🌐 API 호출 중... 작물: {farm_info['crop_name']} (코드: {farm_info['crop_code']})")
        
        # 실제 API 호출
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
                print("✅ API 호출 성공!")
                parsed_data = self.parse_fertilizer_response(response.text)
                if parsed_data:
                    return parsed_data
                else:
                    print("⚠️ 응답 파싱 실패, 테스트 데이터 사용")
                    return self._get_test_data()
            else:
                print(f"⚠️  API 응답 오류: {response.status_code}")
                return self._get_test_data()
                
        except Exception as e:
            print(f"⚠️ API 호출 실패: {str(e)}")
            print("� 테스트 데이터로 진행합니다")
            return self._get_test_data()
    
    def _get_test_data(self):
        """테스트용 비료 데이터"""
        return {
            'pre_Fert_N': '4.9',
            'pre_Fert_P': '24.8', 
            'pre_Fert_K': '3.0',
            'post_Fert_N': '3.2',
            'post_Fert_P': '0.0',
            'post_Fert_K': '0.0',
            'pre_Compost_Cattl': '1500',
            'pre_Compost_Pig': '330', 
            'pre_Compost_Chick': '255',
            'pre_Compost_Mix': '541'
        }
    
    def display_soil_analysis(self, farm_info):
        """토양 분석 결과 출력 (흙토람 스타일)"""
        print("🧪 토양 분석 결과")
        print("=" * 50)
        
        soil = farm_info['soil']
        print(f"📊 토양 화학성")
        print(f"   산도(pH): {soil.get('ph', 6.5)}")
        print(f"   유기물(OM): {soil.get('om', 22)} g/kg")
        print(f"   유효인산: {soil.get('vldpha', 10)} mg/kg")
        print(f"   치환성 칼륨: {soil.get('posifert_K', 4)} cmol+/kg")
        print(f"   치환성 칼슘: {soil.get('posifert_Ca', 6)} cmol+/kg")
        print(f"   치환성 마그네슘: {soil.get('posifert_Mg', 13)} cmol+/kg")
        print(f"   전기전도도: {soil.get('selc', 6)} dS/m")
    
    def display_fertilizer_prescription(self, fertilizer_data, farm_info):
        """비료 처방량 출력 (흙토람 스타일)"""
        print(f"\n💊 비료 처방량")
        print("=" * 50)
        
        # 10a당 처방량
        print(f"📊 표준 처방량 (1,000㎡당)")
        print(f"🌱 밑거름: N-{fertilizer_data.get('pre_Fert_N', '0')}kg P-{fertilizer_data.get('pre_Fert_P', '0')}kg K-{fertilizer_data.get('pre_Fert_K', '0')}kg")
        print(f"🌿 웃거름: N-{fertilizer_data.get('post_Fert_N', '0')}kg P-{fertilizer_data.get('post_Fert_P', '0')}kg K-{fertilizer_data.get('post_Fert_K', '0')}kg")
        
        # 농장 전체 필요량 계산
        farm_size_10a = farm_info['farm_size_10a']
        print(f"\n📊 농장 전체 필요량 ({farm_info['farm_size_a']}a)")
        
        # 밑거름 총량
        base_n = float(fertilizer_data.get('pre_Fert_N', '0')) * farm_size_10a
        base_p = float(fertilizer_data.get('pre_Fert_P', '0')) * farm_size_10a
        base_k = float(fertilizer_data.get('pre_Fert_K', '0')) * farm_size_10a
        
        print(f"� 밑거름 총 필요량")
        print(f"   질소(N): {base_n:.1f}kg")
        print(f"   인산(P): {base_p:.1f}kg") 
        print(f"   칼리(K): {base_k:.1f}kg")
        
        # 웃거름 총량
        add_n = float(fertilizer_data.get('post_Fert_N', '0')) * farm_size_10a
        add_p = float(fertilizer_data.get('post_Fert_P', '0')) * farm_size_10a
        add_k = float(fertilizer_data.get('post_Fert_K', '0')) * farm_size_10a
        
        print(f"\n🌿 웃거름 총 필요량")
        print(f"   질소(N): {add_n:.1f}kg")
        print(f"   인산(P): {add_p:.1f}kg")
        print(f"   칼리(K): {add_k:.1f}kg")
        
        return {
            'base': {'N': base_n, 'P': base_p, 'K': base_k},
            'additional': {'N': add_n, 'P': add_p, 'K': add_k}
        }
    
    def display_compost_prescription(self, fertilizer_data, farm_info):
        """퇴비 처방량 출력 (흙토람 스타일)"""
        print(f"\n🐄 퇴비 처방량")
        print("=" * 50)
        
        farm_size_10a = farm_info['farm_size_10a']
        
        # 농장 전체 필요량만 출력
        cattl_total = float(fertilizer_data.get('pre_Compost_Cattl', '0')) * farm_size_10a
        pig_total = float(fertilizer_data.get('pre_Compost_Pig', '0')) * farm_size_10a
        chick_total = float(fertilizer_data.get('pre_Compost_Chick', '0')) * farm_size_10a
        mix_total = float(fertilizer_data.get('pre_Compost_Mix', '0')) * farm_size_10a
        
        print(f"📦 농장 전체 필요량 ({farm_info['farm_size_a']}a)")
        print(f"   우분퇴비: {cattl_total:.0f}kg ({cattl_total/1000:.1f}톤)")
        print(f"   돈분퇴비: {pig_total:.0f}kg ({pig_total/1000:.1f}톤)")
        print(f"   계분퇴비: {chick_total:.0f}kg ({chick_total/1000:.1f}톤)")
        print(f"   혼합퇴비: {mix_total:.0f}kg ({mix_total/1000:.1f}톤)")
        
        return {
            'cattle_compost': {'kg': cattl_total, 'tons': round(cattl_total/1000, 1)},
            'pig_compost': {'kg': pig_total, 'tons': round(pig_total/1000, 1)},
            'chicken_compost': {'kg': chick_total, 'tons': round(chick_total/1000, 1)},
            'mixed_compost': {'kg': mix_total, 'tons': round(mix_total/1000, 1)}
        }
    
    def calculate_compost_needs(self, fertilizer_data, farm_info):
        """퇴비 필요량 계산 (API용)"""
        farm_size_10a = farm_info['farm_size_10a']
        
        cattl_total = float(fertilizer_data.get('pre_Compost_Cattl', '0')) * farm_size_10a
        pig_total = float(fertilizer_data.get('pre_Compost_Pig', '0')) * farm_size_10a
        chick_total = float(fertilizer_data.get('pre_Compost_Chick', '0')) * farm_size_10a
        mix_total = float(fertilizer_data.get('pre_Compost_Mix', '0')) * farm_size_10a
        
        return {
            'cattle_compost': {'kg': cattl_total, 'tons': round(cattl_total/1000, 1)},
            'pig_compost': {'kg': pig_total, 'tons': round(pig_total/1000, 1)},
            'chicken_compost': {'kg': chick_total, 'tons': round(chick_total/1000, 1)},
            'mixed_compost': {'kg': mix_total, 'tons': round(mix_total/1000, 1)}
        }
    
    def calculate_total_nutrients(self, fertilizer_data, farm_info):
        """농장 전체 양분 필요량 계산 (API용)"""
        farm_size_10a = farm_info['farm_size_10a']
        
        # 밑거름 총량
        base_n = float(fertilizer_data.get('pre_Fert_N', '0')) * farm_size_10a
        base_p = float(fertilizer_data.get('pre_Fert_P', '0')) * farm_size_10a
        base_k = float(fertilizer_data.get('pre_Fert_K', '0')) * farm_size_10a
        
        # 웃거름 총량
        add_n = float(fertilizer_data.get('post_Fert_N', '0')) * farm_size_10a
        add_p = float(fertilizer_data.get('post_Fert_P', '0')) * farm_size_10a
        add_k = float(fertilizer_data.get('post_Fert_K', '0')) * farm_size_10a
        
        return {
            'base': {'N': base_n, 'P': base_p, 'K': base_k},
            'additional': {'N': add_n, 'P': add_p, 'K': add_k}
        }
    
    def load_fertilizer_database(self):
        """비료 데이터베이스 로드"""
        try:
            with open('data/밑거름.json', 'r', encoding='utf-8') as f:
                base_fertilizers = json.load(f)
            with open('data/웃거름.json', 'r', encoding='utf-8') as f:
                additional_fertilizers = json.load(f)
            return base_fertilizers, additional_fertilizers
        except FileNotFoundError:
            print("⚠️ 비료 데이터베이스 파일이 없습니다. utils/csv_to_json.py를 먼저 실행해주세요.")
            return [], []
    
    def recommend_fertilizers(self, target_n, target_p, target_k, fertilizer_type="base", top_n=2):
        """NPK 기준 비료 추천"""
        base_fertilizers, additional_fertilizers = self.load_fertilizer_database()
        
        if fertilizer_type == "base":
            fertilizers = base_fertilizers
        else:
            fertilizers = additional_fertilizers
        
        if not fertilizers:
            return []
        
        # 질소 함량이 있는 비료만 필터링
        nitrogen_fertilizers = [f for f in fertilizers if float(f.get('질소', 0)) > 0]
        
        # NPK 비율 점수 계산
        scored_fertilizers = []
        for fert in nitrogen_fertilizers:
            n_diff = abs(float(fert.get('질소', 0)) - target_n)
            p_diff = abs(float(fert.get('인산', 0)) - target_p) 
            k_diff = abs(float(fert.get('칼리', 0)) - target_k)
            score = n_diff + p_diff + k_diff
            
            fert_copy = fert.copy()
            fert_copy['추천점수'] = round(score, 1)
            scored_fertilizers.append(fert_copy)
        
        # 점수 순 정렬
        scored_fertilizers.sort(key=lambda x: x['추천점수'])
        return scored_fertilizers[:top_n]
    
    def calculate_fertilizer_usage(self, fertilizer, target_n, target_p, target_k, total_area_10a):
        """질소 기준 비료 사용량 계산"""
        try:
            fert_n = float(fertilizer.get('질소', 0))
            if fert_n == 0:
                return None
            
            # 질소 기준 사용량
            usage_per_10a = target_n / (fert_n / 100)  # kg per 1000㎡
            total_usage = usage_per_10a * total_area_10a
            
            # 포대 수 계산
            bag_weight = float(fertilizer.get('1포대당 무게', 20))
            bags_needed = total_usage / bag_weight
            
            # 실제 공급 성분
            actual_n = total_usage * fert_n / 100
            actual_p = total_usage * float(fertilizer.get('인산', 0)) / 100
            actual_k = total_usage * float(fertilizer.get('칼리', 0)) / 100
            
            # 부족/과잉 성분
            target_total_p = target_p * total_area_10a
            target_total_k = target_k * total_area_10a
            
            shortage_p = max(0, target_total_p - actual_p)
            shortage_k = max(0, target_total_k - actual_k)
            
            return {
                'usage_kg': round(total_usage, 1),
                'bags': round(bags_needed, 1),
                'shortage_p': round(shortage_p, 1),
                'shortage_k': round(shortage_k, 1)
            }
        except:
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
    
    def run_soil_analysis(self):
        """토양-비료 처방 시스템 실행 (흙토람 스타일)"""
        print("🌾 토양-비료 처방 시스템")
        print("=" * 60)
        
        # 1. 농장 정보 가져오기
        farm_info = self.get_farm_info()
        print(f"🏡 농장 기본정보")
        print(f"   작물: {farm_info['crop_name']} (코드: {farm_info['crop_code']})")
        print(f"   면적: {farm_info['farm_size_a']}a\n")
        
        # 2. 토양 분석 결과 출력
        self.display_soil_analysis(farm_info)
        
        # 3. API 호출 및 응답 처리
        fertilizer_data = self.call_fertilizer_api(farm_info)
        
        if not fertilizer_data or not fertilizer_data.get('success'):
            print("❌ 처방 계산 실패")
            return
        
        # 4. 처방 결과 출력
        nutrient_needs = self.display_fertilizer_prescription(fertilizer_data, farm_info)
        compost_needs = self.display_compost_prescription(fertilizer_data, farm_info)
        
        # 5. 비료 추천
        self.display_fertilizer_recommendations(nutrient_needs)
        
        # 6. 결과 요약
        print(f"\n📋 처방 결과 요약")
        print("=" * 50)
        print(f"✅ 작물: {fertilizer_data.get('crop_Nm', '맥주보리')}")
        print(f"✅ 결과: {fertilizer_data.get('result_Msg', 'OK')}")
        print(f"✅ 농장면적: {farm_info['farm_size_a']}a")

# 테스트 실행
if __name__ == "__main__":
    service = SoilFertilizerService()
    service.run_soil_analysis()
