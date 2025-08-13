"""
다중 작물 비료 추천 서비스
한 번의 API 호출로 최대 3개 작물의 비료 추천을 처리
"""
from typing import List, Dict
from config.user_data import USER_DATA
from config.crop_codes import get_crop_code, get_crop_name
from services.soil_fertilizer_service import SoilFertilizerService

class MultipleCropFertilizerService:
    """다중 작물 비료 추천 서비스"""
    
    def __init__(self):
        self.soil_service = SoilFertilizerService()
    
    def get_multiple_fertilizer_recommendations(self, crop_names: List[str], soil_data: Dict = None) -> Dict:
        """
        여러 작물에 대한 비료 추천을 한 번에 처리
        
        Args:
            crop_names: 작물명 리스트 (최대 3개)
            soil_data: 토양 데이터 (None이면 USER_DATA 사용)
            
        Returns:
            모든 작물의 비료 추천 결과
        """
        if len(crop_names) > 3:
            return {
                "status": "error",
                "message": "작물은 최대 3개까지만 처리 가능합니다."
            }
        
        # 토양 데이터 준비
        if soil_data is None:
            soil_data = USER_DATA["soil"]
        
        farm_size_a = USER_DATA.get("farm_size_a", 250)
        
        results = {
            "status": "success",
            "total_crops": len(crop_names),
            "farm_size_a": farm_size_a,
            "soil_info": soil_data,
            "crops": [],
            "summary": {
                "successful": 0,
                "failed": 0,
                "errors": []
            }
        }
        
        for crop_name in crop_names:
            crop_result = self._get_single_crop_recommendation(crop_name, soil_data, farm_size_a)
            results["crops"].append(crop_result)
            
            if crop_result["status"] == "success":
                results["summary"]["successful"] += 1
            else:
                results["summary"]["failed"] += 1
                results["summary"]["errors"].append({
                    "crop": crop_name,
                    "error": crop_result.get("message", "Unknown error")
                })
        
        return results
    
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
        try:
            # 작물 코드 검증
            crop_code = get_crop_code(crop_name)
            if not crop_code:
                return {
                    "status": "error",
                    "crop_name": crop_name,
                    "crop_code": None,
                    "message": f"지원하지 않는 작물입니다: {crop_name}",
                    "fertilizer_data": None
                }
            
            # 농장 정보 준비 (단일 작물 API와 동일한 구조)
            farm_info = self.soil_service.get_farm_info()
            farm_info['crop_name'] = crop_name
            farm_info['crop_code'] = crop_code
            farm_info['soil'].update(soil_data)
            farm_info['farm_size_a'] = farm_size_a
            
            # 비료 API 호출
            fertilizer_result = self.soil_service.call_fertilizer_api(farm_info)
            
            if not fertilizer_result or not fertilizer_result.get("success"):
                return {
                    "status": "error",
                    "crop_name": crop_name,
                    "crop_code": crop_code,
                    "message": f"{crop_name}에 대한 비료 추천 데이터를 가져올 수 없습니다.",
                    "fertilizer_data": fertilizer_result
                }
            
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
                        nutrient_needs[fert_type]['N'],
                        nutrient_needs[fert_type]['P'], 
                        nutrient_needs[fert_type]['K'],
                        farm_info['farm_size_10a']
                    )
                    fertilizers.append(usage_data)
                return fertilizers
            
            base_fertilizers = _process_fertilizers(base_recommendations, 'base')
            additional_fertilizers = _process_fertilizers(additional_recommendations, 'additional')
            
            return {
                "status": "success",
                "crop_name": crop_name,
                "crop_code": crop_code,
                "farm_info": {
                    "crop_name": crop_name,
                    "crop_code": crop_code,
                    "farm_size_a": farm_size_a,
                    "farm_size_10a": farm_size_a / 10
                },
                "soil_analysis": soil_data,
                "fertilizer_prescription": {
                    "standard_per_1000sqm": {
                        "base": {
                            "N": float(fertilizer_result.get("pre_Fert_N", 0)),
                            "P": float(fertilizer_result.get("pre_Fert_P", 0)),
                            "K": float(fertilizer_result.get("pre_Fert_K", 0))
                        },
                        "additional": {
                            "N": float(fertilizer_result.get("add_Fert_N", 0)),
                            "P": float(fertilizer_result.get("add_Fert_P", 0)),
                            "K": float(fertilizer_result.get("add_Fert_K", 0))
                        }
                    },
                    "total_farm_needs": nutrient_needs
                },
                "fertilizer_recommendations": {
                    "base_fertilizers": base_fertilizers,
                    "additional_fertilizers": additional_fertilizers
                },
                "compost_recommendations": compost_needs,
                "message": "비료 추천 성공"
            }
                
        except Exception as e:
            return {
                "status": "error",
                "crop_name": crop_name,
                "crop_code": get_crop_code(crop_name),
                "message": f"처리 중 오류 발생: {str(e)}",
                "fertilizer_data": None
            }
    
    def get_user_crops_recommendation(self, soil_data: Dict = None) -> Dict:
        """
        USER_DATA에 등록된 작물들에 대한 비료 추천
        
        Args:
            soil_data: 토양 데이터 (None이면 USER_DATA 사용)
            
        Returns:
            사용자 작물들의 비료 추천 결과
        """
        current_crops = USER_DATA.get("crop", {}).get("current_crops", [])
        
        if not current_crops:
            return {
                "status": "error",
                "message": "등록된 작물이 없습니다.",
                "crops": []
            }
        
        return self.get_multiple_fertilizer_recommendations(current_crops, soil_data)
    
    def format_for_frontend(self, recommendations: Dict) -> Dict:
        """
        프론트엔드에 최적화된 형태로 데이터 포맷팅
        
        Args:
            recommendations: 비료 추천 결과
            
        Returns:
            프론트엔드 최적화된 데이터
        """
        if recommendations["status"] != "success":
            return recommendations
        
        formatted_data = {
            "status": "success",
            "farm_info": {
                "size_a": recommendations["farm_size_a"],
                "soil": recommendations["soil_info"]
            },
            "crops": [],
            "summary": recommendations["summary"]
        }
        
        for crop in recommendations["crops"]:
            if crop["status"] == "success" and crop["fertilizer_data"]:
                fertilizer = crop["fertilizer_data"]
                formatted_crop = {
                    "name": crop["crop_name"],
                    "code": crop["crop_code"],
                    "status": "success",
                    "fertilizer": {
                        "nitrogen": {
                            "pre_fert": fertilizer.get("pre_Fert_N", "0"),
                            "add_fert": fertilizer.get("add_Fert_N", "0"),
                            "total": fertilizer.get("fert_N", "0")
                        },
                        "phosphorus": {
                            "pre_fert": fertilizer.get("pre_Fert_P", "0"),
                            "add_fert": fertilizer.get("add_Fert_P", "0"),
                            "total": fertilizer.get("fert_P", "0")
                        },
                        "potassium": {
                            "pre_fert": fertilizer.get("pre_Fert_K", "0"),
                            "add_fert": fertilizer.get("add_Fert_K", "0"),
                            "total": fertilizer.get("fert_K", "0")
                        },
                        "lime": fertilizer.get("lime_Rec", "0"),
                        "compost": fertilizer.get("cmpst_Rec", "0")
                    }
                }
            else:
                formatted_crop = {
                    "name": crop["crop_name"],
                    "code": crop.get("crop_code"),
                    "status": "error",
                    "message": crop.get("message", "데이터 없음"),
                    "fertilizer": None
                }
            
            formatted_data["crops"].append(formatted_crop)
        
        return formatted_data
