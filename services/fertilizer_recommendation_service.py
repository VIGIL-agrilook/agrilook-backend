"""
작물 비료 추천 서비스
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
        return result

    # 상세 추천 함수는 더 이상 사용하지 않음 (통합 추천으로 대체)
