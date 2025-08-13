"""
농업 토양-비료 처방 API 시스템
메인 Flask 애플리케이션
"""
from flask import Flask, jsonify, request
import os
from dotenv import load_dotenv

from config.user_data import USER_DATA
from config.crop_codes import get_crop_code, get_crop_name, get_available_crops
from services.chat_service import chat_bp
from soil_fertilizer_service import SoilFertilizerService

# 환경변수 로드
load_dotenv()

app = Flask(__name__)

# 블루프린트 등록 (챗봇 기능)
app.register_blueprint(chat_bp)


@app.route('/health', methods=['GET'])
def health_check():
    """헬스 체크 엔드포인트"""
    return jsonify({
        "status": "healthy", 
        "message": "농업 AI 시스템이 정상 작동 중입니다.",
        "version": "1.0.0"
    })


@app.route('/api/crops', methods=['GET'])
def get_crops():
    """사용 가능한 작물 목록 조회"""
    try:
        crops = get_available_crops()
        return jsonify({
            "status": "success",
            "crops": crops,
            "count": len(crops)
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"작물 목록 조회 실패: {str(e)}"
        }), 500


@app.route('/user-info', methods=['GET'])
def get_user_info():
    """사용자 정보 조회"""
    return jsonify({
        "status": "success",
        "data": USER_DATA
    })


@app.route('/api/fertilizer-prescription', methods=['POST'])
def get_fertilizer_prescription():
    """토양-비료 처방 API - 메인 기능"""
    try:
        # 요청 데이터에서 작물 정보 받기
        data = request.get_json() if request.is_json else {}
        crop_name = data.get('crop_name', USER_DATA['crop']['name'])  # 기본값은 USER_DATA에서
        
        # 작물 코드 조회
        crop_code = get_crop_code(crop_name)
        if not crop_code:
            return jsonify({
                "status": "error",
                "message": f"지원하지 않는 작물입니다: {crop_name}. /api/crops 엔드포인트에서 지원 작물을 확인하세요."
            }), 400
        
        # 토양 정보는 요청에서 받거나 USER_DATA 기본값 사용
        soil_data = data.get('soil', USER_DATA['soil'])
        
        service = SoilFertilizerService()
        farm_info = service.get_farm_info()
        
        # 작물 정보 업데이트
        farm_info['crop_name'] = crop_name
        farm_info['crop_code'] = crop_code
        farm_info['soil'].update(soil_data)
        
        fertilizer_data = service.call_fertilizer_api(farm_info)
        nutrient_needs = service.calculate_total_nutrients(fertilizer_data, farm_info)
        compost_needs = service.calculate_compost_needs(fertilizer_data, farm_info)
        
        # 비료 추천 (밑거름 3개, 웃거름 3개)
        base_recommendations = service.recommend_fertilizers(
            nutrient_needs['base']['N'], 
            nutrient_needs['base']['P'], 
            nutrient_needs['base']['K'],
            "base", 3
        )
        
        additional_recommendations = service.recommend_fertilizers(
            nutrient_needs['additional']['N'],
            nutrient_needs['additional']['P'], 
            nutrient_needs['additional']['K'],
            "additional", 3
        )
        
        # 사용량 계산 및 응답 데이터 구성
        base_fertilizers = _process_fertilizers(base_recommendations, fertilizer_data, farm_info, 'pre')
        additional_fertilizers = _process_fertilizers(additional_recommendations, fertilizer_data, farm_info, 'post')
        
        response_data = {
            "status": "success",
            "farm_info": {
                "crop_name": farm_info['crop_name'],
                "crop_code": farm_info['crop_code'], 
                "farm_size_a": farm_info['farm_size_a'],
                "farm_size_10a": farm_info['farm_size_10a']
            },
            "soil_analysis": farm_info['soil'],
            "fertilizer_prescription": {
                "standard_per_1000sqm": {
                    "base": {
                        "N": float(fertilizer_data.get('pre_Fert_N', '0')),
                        "P": float(fertilizer_data.get('pre_Fert_P', '0')),
                        "K": float(fertilizer_data.get('pre_Fert_K', '0'))
                    },
                    "additional": {
                        "N": float(fertilizer_data.get('post_Fert_N', '0')),
                        "P": float(fertilizer_data.get('post_Fert_P', '0')),
                        "K": float(fertilizer_data.get('post_Fert_K', '0'))
                    }
                },
                "total_farm_needs": nutrient_needs
            },
            "compost_recommendations": compost_needs,
            "fertilizer_recommendations": {
                "base_fertilizers": base_fertilizers,
                "additional_fertilizers": additional_fertilizers
            }
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({
            "status": "error", 
            "message": str(e),
            "type": "fertilizer_prescription_error"
        }), 500


def _process_fertilizers(recommendations, fertilizer_data, farm_info, fert_type):
    """비료 처리 헬퍼 함수"""
    service = SoilFertilizerService()
    fertilizers = []
    
    prefix = 'pre_Fert' if fert_type == 'pre' else 'post_Fert'
    
    for fert in recommendations:
        usage = service.calculate_fertilizer_usage(
            fert,
            float(fertilizer_data.get(f'{prefix}_N', '0')),
            float(fertilizer_data.get(f'{prefix}_P', '0')),
            float(fertilizer_data.get(f'{prefix}_K', '0')),
            farm_info['farm_size_10a']
        )
        fertilizers.append({
            'name': fert['비료종류'],
            'npk': f"N-{fert['질소']}% P-{fert['인산']}% K-{fert['칼리']}%",
            'nitrogen': fert['질소'],
            'phosphorus': fert['인산'],
            'potassium': fert['칼리'],
            'usage_kg': usage['usage_kg'] if usage else 0,
            'bags': usage['bags'] if usage else 0,
            'shortage_p': usage['shortage_p'] if usage else 0,
            'shortage_k': usage['shortage_k'] if usage else 0
        })
    
    return fertilizers


@app.route('/api/fertilizer-prescription/test', methods=['GET'])
def test_fertilizer_prescription():
    """테스트용 비료 처방 API - 기본 작물 사용"""
    try:
        service = SoilFertilizerService()
        farm_info = service.get_farm_info()
        fertilizer_data = service.call_fertilizer_api(farm_info)
        nutrient_needs = service.calculate_total_nutrients(fertilizer_data, farm_info)
        compost_needs = service.calculate_compost_needs(fertilizer_data, farm_info)
        
        # 비료 추천 (밑거름 3개, 웃거름 3개)
        base_recommendations = service.recommend_fertilizers(
            nutrient_needs['base']['N'], 
            nutrient_needs['base']['P'], 
            nutrient_needs['base']['K'],
            "base", 3
        )
        
        additional_recommendations = service.recommend_fertilizers(
            nutrient_needs['additional']['N'],
            nutrient_needs['additional']['P'], 
            nutrient_needs['additional']['K'],
            "additional", 3
        )
        
        # 사용량 계산 및 응답 데이터 구성
        base_fertilizers = _process_fertilizers(base_recommendations, fertilizer_data, farm_info, 'pre')
        additional_fertilizers = _process_fertilizers(additional_recommendations, fertilizer_data, farm_info, 'post')
        
        response_data = {
            "status": "success",
            "farm_info": {
                "crop_name": farm_info['crop_name'],
                "crop_code": farm_info['crop_code'], 
                "farm_size_a": farm_info['farm_size_a'],
                "farm_size_10a": farm_info['farm_size_10a']
            },
            "soil_analysis": farm_info['soil'],
            "fertilizer_prescription": {
                "standard_per_1000sqm": {
                    "base": {
                        "N": nutrient_needs['base']['N'],
                        "P": nutrient_needs['base']['P'],
                        "K": nutrient_needs['base']['K']
                    },
                    "additional": {
                        "N": nutrient_needs['additional']['N'],
                        "P": nutrient_needs['additional']['P'],
                        "K": nutrient_needs['additional']['K']
                    }
                },
                "compost_per_1000sqm": compost_needs,
                "recommended_fertilizers": {
                    "base_fertilizers": base_fertilizers,
                    "additional_fertilizers": additional_fertilizers
                }
            }
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"비료 처방 실패: {str(e)}"
        }), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)