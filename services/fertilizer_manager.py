"""
다중 작물 비료 추천 관리 시스템
최대 3개 작물까지 지원하며 각 작물별 비료 추천 내용을 전역 변수로 관리
"""
import json
from datetime import datetime
from typing import List, Dict, Optional
from config.user_data import USER_DATA
from config.crop_codes import get_crop_code, get_crop_name
from services.soil_fertilizer_service import SoilFertilizerService

# 전역 변수: 작물별 비료 추천 데이터 저장
FERTILIZER_RECOMMENDATIONS = {
    "crops": [],  # 최대 3개 작물 정보
    "last_updated": None,
    "soil_info": None,
    "farm_size_a": 0
}

class FertilizerManager:
    """다중 작물 비료 추천 관리자"""
    
    def __init__(self):
        self.soil_service = SoilFertilizerService()
        
    def update_crop_list(self, crop_names: List[str]) -> Dict:
        """
        작물 목록 업데이트 (최대 3개)
        
        Args:
            crop_names: 작물명 리스트 (최대 3개)
            
        Returns:
            업데이트 결과
        """
        global FERTILIZER_RECOMMENDATIONS
        
        if len(crop_names) > 3:
            return {
                "status": "error",
                "message": "작물은 최대 3개까지만 등록 가능합니다."
            }
        
        # 작물 코드 검증 및 매핑
        crop_data = []
        for crop_name in crop_names:
            crop_code = get_crop_code(crop_name)
            if not crop_code:
                return {
                    "status": "error",
                    "message": f"지원하지 않는 작물입니다: {crop_name}"
                }
            
            crop_data.append({
                "name": crop_name,
                "code": crop_code,
                "fertilizer_data": None,
                "last_updated": None
            })
        
        FERTILIZER_RECOMMENDATIONS["crops"] = crop_data
        FERTILIZER_RECOMMENDATIONS["last_updated"] = datetime.now().isoformat()
        
        return {
            "status": "success",
            "message": f"{len(crop_names)}개 작물이 등록되었습니다.",
            "crops": [crop["name"] for crop in crop_data]
        }
    
    def get_fertilizer_recommendation_for_crop(self, crop_name: str, soil_data: Dict = None) -> Dict:
        """
        특정 작물에 대한 비료 추천
        
        Args:
            crop_name: 작물명
            soil_data: 토양 데이터 (None이면 USER_DATA 사용)
            
        Returns:
            비료 추천 결과
        """
        crop_code = get_crop_code(crop_name)
        if not crop_code:
            return {
                "status": "error",
                "message": f"지원하지 않는 작물입니다: {crop_name}"
            }
        
        # 토양 데이터 준비
        if soil_data is None:
            soil_data = USER_DATA["soil"]
        
        # 농장 정보 준비
        farm_info = {
            "crop_code": crop_code,
            "crop_name": crop_name,
            "farm_size_a": USER_DATA.get("farm_size_a", 250),
            "soil": soil_data
        }
        
        try:
            # 비료 API 호출
            fertilizer_result = self.soil_service.call_fertilizer_api(farm_info)
            
            if fertilizer_result and fertilizer_result.get("success"):
                return {
                    "status": "success",
                    "crop_name": crop_name,
                    "crop_code": crop_code,
                    "fertilizer_data": fertilizer_result,
                    "updated_at": datetime.now().isoformat()
                }
            else:
                return {
                    "status": "error",
                    "message": f"{crop_name}에 대한 비료 추천 데이터를 가져올 수 없습니다.",
                    "crop_name": crop_name
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"비료 추천 처리 중 오류 발생: {str(e)}",
                "crop_name": crop_name
            }
    
    def update_all_fertilizer_recommendations(self, soil_data: Dict = None) -> Dict:
        """
        등록된 모든 작물에 대한 비료 추천 업데이트
        
        Args:
            soil_data: 토양 데이터 (None이면 USER_DATA 사용)
            
        Returns:
            전체 업데이트 결과
        """
        global FERTILIZER_RECOMMENDATIONS
        
        if not FERTILIZER_RECOMMENDATIONS["crops"]:
            return {
                "status": "error",
                "message": "등록된 작물이 없습니다. 먼저 작물을 등록해주세요."
            }
        
        updated_crops = []
        failed_crops = []
        
        for crop_info in FERTILIZER_RECOMMENDATIONS["crops"]:
            crop_name = crop_info["name"]
            result = self.get_fertilizer_recommendation_for_crop(crop_name, soil_data)
            
            if result["status"] == "success":
                crop_info["fertilizer_data"] = result["fertilizer_data"]
                crop_info["last_updated"] = result["updated_at"]
                updated_crops.append(crop_name)
            else:
                failed_crops.append({
                    "crop": crop_name,
                    "error": result["message"]
                })
        
        # 전역 변수 업데이트
        FERTILIZER_RECOMMENDATIONS["last_updated"] = datetime.now().isoformat()
        FERTILIZER_RECOMMENDATIONS["soil_info"] = soil_data or USER_DATA["soil"]
        FERTILIZER_RECOMMENDATIONS["farm_size_a"] = USER_DATA.get("farm_size_a", 250)
        
        return {
            "status": "success" if updated_crops else "error",
            "message": f"{len(updated_crops)}개 작물 업데이트 완료",
            "updated_crops": updated_crops,
            "failed_crops": failed_crops,
            "total_crops": len(FERTILIZER_RECOMMENDATIONS["crops"])
        }
    
    def get_current_recommendations(self) -> Dict:
        """
        현재 저장된 모든 비료 추천 데이터 반환
        
        Returns:
            전체 비료 추천 데이터
        """
        global FERTILIZER_RECOMMENDATIONS
        
        return {
            "status": "success",
            "data": FERTILIZER_RECOMMENDATIONS,
            "summary": {
                "total_crops": len(FERTILIZER_RECOMMENDATIONS["crops"]),
                "crops_with_data": len([crop for crop in FERTILIZER_RECOMMENDATIONS["crops"] if crop["fertilizer_data"]]),
                "last_updated": FERTILIZER_RECOMMENDATIONS["last_updated"]
            }
        }
    
    def get_crop_recommendation(self, crop_name: str) -> Dict:
        """
        특정 작물의 저장된 비료 추천 데이터 반환
        
        Args:
            crop_name: 작물명
            
        Returns:
            해당 작물의 비료 추천 데이터
        """
        global FERTILIZER_RECOMMENDATIONS
        
        for crop_info in FERTILIZER_RECOMMENDATIONS["crops"]:
            if crop_info["name"] == crop_name:
                return {
                    "status": "success",
                    "crop_name": crop_name,
                    "crop_code": crop_info["code"],
                    "fertilizer_data": crop_info["fertilizer_data"],
                    "last_updated": crop_info["last_updated"]
                }
        
        return {
            "status": "error",
            "message": f"등록되지 않은 작물입니다: {crop_name}"
        }
    
    def remove_crop(self, crop_name: str) -> Dict:
        """
        작물 제거
        
        Args:
            crop_name: 제거할 작물명
            
        Returns:
            제거 결과
        """
        global FERTILIZER_RECOMMENDATIONS
        
        original_count = len(FERTILIZER_RECOMMENDATIONS["crops"])
        FERTILIZER_RECOMMENDATIONS["crops"] = [
            crop for crop in FERTILIZER_RECOMMENDATIONS["crops"] 
            if crop["name"] != crop_name
        ]
        
        if len(FERTILIZER_RECOMMENDATIONS["crops"]) < original_count:
            FERTILIZER_RECOMMENDATIONS["last_updated"] = datetime.now().isoformat()
            return {
                "status": "success",
                "message": f"{crop_name} 작물이 제거되었습니다.",
                "remaining_crops": [crop["name"] for crop in FERTILIZER_RECOMMENDATIONS["crops"]]
            }
        else:
            return {
                "status": "error",
                "message": f"제거할 작물을 찾을 수 없습니다: {crop_name}"
            }


# 전역 매니저 인스턴스
fertilizer_manager = FertilizerManager()

# 초기 설정: USER_DATA의 작물들로 초기화
def initialize_from_user_data():
    """USER_DATA의 작물 정보로 초기화"""
    if USER_DATA.get("crop", {}).get("current_crops"):
        crop_names = USER_DATA["crop"]["current_crops"]
        result = fertilizer_manager.update_crop_list(crop_names)
        print(f"🌱 초기 작물 설정: {result}")

# 모듈 로드 시 초기화 실행
initialize_from_user_data()
