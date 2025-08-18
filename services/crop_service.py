"""
단일 작물 비료 추천 서비스
요청 받은 작물에 대해서만 비료 추천을 간소화하여 처리
"""
from typing import Dict
from config.user_data import USER_DATA
from config.crop_codes import get_crop_code
from services.soil_fertilizer_service import SoilFertilizerService

class FertilizerRecommendationService:
    """작물 비료 추천 서비스 (요청 받은 작물만 추천)"""
    def __init__(self):
        self.soil_service = SoilFertilizerService()

    def get_fertilizer_recommendation(self, crop_name: str, soil_data: Dict = None) -> Dict:
        """
        단일 작물에 대한 비료 추천 처리 (간소화 구조)
        """
        if soil_data is None:
            soil_data = USER_DATA["soil"]
        farm = USER_DATA.get("farm", {})
        farm_size_a = USER_DATA.get("farm_size_a", 250)
        area_sqm = farm.get("area_m2", farm_size_a * 100)
        field_id = farm.get("_id", "farm001")
        # SoilFertilizerService에서 통합 추천 결과 반환
        self.soil_service.get_farm_info()['crop_name'] = crop_name
        result = self.soil_service.get_recommendation_bundle()
        compost = result.get("compost_recommendations", {})
        ferts = result.get("fertilizer_recommendations", {})
        def simple_fert_list(fert_list):
            return [
                {
                    "id": item.get("fertilizer_id", ""),
                    "name": item.get("fertilizer_name", ""),
                    "N": item.get("N_ratio", 0),
                    "P2O5": item.get("P_ratio", 0),
                    "K2O": item.get("K_ratio", 0),
                    "bags": item.get("bags", 0),
                    "usage_kg": item.get("usage_kg", 0)
                }
                for item in fert_list if item
            ]
        return {
            "crop": {"name": crop_name},
            "field": {"id": field_id, "area_sqm": area_sqm},
            "fertilizer": {
                "base": simple_fert_list(ferts.get("base_fertilizers", [])),
                "additional": simple_fert_list(ferts.get("additional_fertilizers", []))
            },
            "compost": {
                "cattle_kg": float(compost.get("cattle_kg", 0)),
                "chicken_kg": float(compost.get("chicken_kg", 0)),
                "mixed_kg": float(compost.get("mixed_kg", 0)),
                "pig_kg": float(compost.get("pig_kg", 0))
            }
        }


    def _get_single_crop_recommendation(self, crop_name: str, soil_data: Dict, farm_size_a: int) -> Dict:
        """
        단일 작물에 대한 상세한 비료 추천 (단일 작물 API와 동일한 수준)
        
        Args:
            crop_name: 작물명
            soil_data: 토양 데이터
            farm_size_a: 농장 면적 (a)
            
        Returns:
            상세한 단일 작물 비료 추천 결과
        """
        # 작물 코드 검증
        crop_code = get_crop_code(crop_name)
        if not crop_code:
            return {}
        # 농장 정보 준비 (단일 작물 API와 동일한 구조)
        farm_info = self.soil_service.get_farm_info()
        farm_info['crop_name'] = crop_name
        farm_info['crop_code'] = crop_code
        farm_info['soil'].update(soil_data)
        farm_info['farm_size_a'] = farm_size_a
        # 비료 API 호출
        fertilizer_result = self.soil_service.call_fertilizer_api(farm_info)
        if not fertilizer_result or not fertilizer_result.get("success"):
            return {}
        # 영양분 요구량 계산
        nutrient_needs = self.soil_service.calculate_total_nutrients(fertilizer_result, farm_info)
        # 비료 제품 추천
        base_recommendations = self.soil_service.recommend_fertilizers(
            nutrient_needs['base']['N'],
            nutrient_needs['base']['P'], 
            nutrient_needs['base']['K'],
            "base", 3
        )
        additional_recommendations = self.soil_service.recommend_fertilizers(
            nutrient_needs['additional']['N'],
            nutrient_needs['additional']['P'], 
            nutrient_needs['additional']['K'],
            "additional", 3
        )
        # 퇴비 추천 계산
        compost_needs = self.soil_service.calculate_compost_needs(fertilizer_result, farm_info)
        # 비료 사용량 계산 (헬퍼 함수)
        def _process_fertilizers(recommendations, fert_type):
            fertilizers = []
            for rec in recommendations:
                usage_data = self.soil_service.calculate_fertilizer_usage(
                    rec, 
                    nutrient_needs[fert_type]['N'],   # 전체 농장 필요량 (kg)
                    nutrient_needs[fert_type]['P'],  # 전체 농장 필요량 (kg)
                    nutrient_needs[fert_type]['K']   # 전체 농장 필요량 (kg)
                )
                fertilizers.append(usage_data)
            return fertilizers
        base_fertilizers = _process_fertilizers(base_recommendations, 'base')
        additional_fertilizers = _process_fertilizers(additional_recommendations, 'additional')
        return {
            "crop_name": crop_name,
            "crop_code": crop_code,
            "fertilizer_prescription": {
                "standard_per_1000sqm": {
                    "base": {
                        "N": float(fertilizer_result.get("pre_Fert_N", 0)),
                        "P": float(fertilizer_result.get("pre_Fert_P", 0)),
                        "K": float(fertilizer_result.get("pre_Fert_K", 0))
                    },
                    "additional": {
                        "N": float(fertilizer_result.get("post_Fert_N", 0)),
                        "P": float(fertilizer_result.get("post_Fert_P", 0)),
                        "K": float(fertilizer_result.get("post_Fert_K", 0))
                    }
                },
                "total_farm_needs": nutrient_needs
            },
            "fertilizer_recommendations": {
                "base_fertilizers": base_fertilizers,
                "additional_fertilizers": additional_fertilizers
            },
            "compost_recommendations": compost_needs
        }
