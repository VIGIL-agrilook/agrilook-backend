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
from services.soil_fertilizer_service import SoilFertilizerService
from services.weather_service import weather_service, get_current_weather_data
from services.multiple_crop_service import MultipleCropFertilizerService

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
    try:
        # 기본 사용자 데이터에 작물 코드 추가
        user_info = USER_DATA.copy()
        
        # 주 작물의 코드 추가
        crop_name = user_info["crop"]["name"]
        crop_code = get_crop_code(crop_name)
        if crop_code:
            user_info["crop"]["code"] = crop_code
        
        return jsonify({
            "status": "success",
            "data": user_info
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"사용자 정보 조회 실패: {str(e)}"
        }), 500


@app.route('/api/fertilizer-prescription', methods=['POST'])
def get_fertilizer_prescription():
    """토양-비료 처방 API - 모든 등록된 작물 처리"""
    try:
        data = request.get_json() if request.is_json else {}
        
        # 토양 데이터
        soil_data = data.get('soil', USER_DATA['soil'])
        
        # 다중 작물 서비스 사용
        multi_service = MultipleCropFertilizerService()
        result = multi_service.get_user_crops_recommendation(soil_data)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"비료 처방 실패: {str(e)}"
        }), 500


@app.route('/api/fertilizer-prescription/test', methods=['GET'])
def test_fertilizer_prescription():
    """테스트용 비료 처방 API - 모든 등록된 작물 사용"""
    try:
        multi_service = MultipleCropFertilizerService()
        result = multi_service.get_user_crops_recommendation()
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"테스트 비료 처방 실패: {str(e)}"
        }), 500


@app.route('/api/fertilizer-prescription/multiple', methods=['POST'])
def get_multiple_fertilizer_prescription():
    """다중 작물 비료 처방 API - 최대 3개 작물 처리"""
    try:
        data = request.get_json() if request.is_json else {}
        
        # 작물 목록 받기
        crop_names = data.get('crop_names', USER_DATA.get('crop', {}).get('current_crops', []))
        
        if not crop_names:
            return jsonify({
                "status": "error",
                "message": "작물 목록이 필요합니다. crop_names 배열을 제공해주세요."
            }), 400
        
        if len(crop_names) > 3:
            return jsonify({
                "status": "error", 
                "message": "작물은 최대 3개까지만 처리 가능합니다."
            }), 400
        
        # 토양 데이터
        soil_data = data.get('soil', USER_DATA['soil'])
        
        # 다중 작물 서비스 사용
        multi_service = MultipleCropFertilizerService()
        result = multi_service.get_multiple_fertilizer_recommendations(crop_names, soil_data)
        
        # 프론트엔드 최적화 형태로 포맷팅
        formatted_result = multi_service.format_for_frontend(result)
        
        return jsonify(formatted_result)
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"다중 작물 비료 처방 실패: {str(e)}"
        }), 500


@app.route('/api/fertilizer-prescription/user-crops', methods=['GET', 'POST'])
def get_user_crops_fertilizer_prescription():
    """사용자 등록 작물들에 대한 비료 처방"""
    try:
        # POST인 경우 토양 데이터 받기
        soil_data = None
        if request.method == 'POST' and request.is_json:
            data = request.get_json()
            soil_data = data.get('soil')
        
        multi_service = MultipleCropFertilizerService()
        result = multi_service.get_user_crops_recommendation(soil_data)
        
        # 프론트엔드 최적화 형태로 포맷팅
        formatted_result = multi_service.format_for_frontend(result)
        
        return jsonify(formatted_result)
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"사용자 작물 비료 처방 실패: {str(e)}"
        }), 500


@app.route('/api/weather/current', methods=['GET'])
def get_current_weather():
    """현재 기상 정보 조회 (기온, 강수량, 습도 포함)"""
    try:
        # 기본값을 USER_DATA에서 가져오기
        default_station = USER_DATA["location"]["station"]
        station = request.args.get('station', default_station)
        
        # 기상 데이터 업데이트 및 조회
        weather_data = weather_service.get_current_weather(station)
        global_weather = get_current_weather_data()
        
        if not weather_data and global_weather["status"] != "connected":
            return jsonify({
                "status": "error",
                "message": "기상 정보를 가져올 수 없습니다"
            }), 500
            
        return jsonify({
            "status": "success",
            "data": {
                "temperature": global_weather["temperature"],
                "precipitation": global_weather["precipitation"], 
                "humidity": global_weather["humidity"],
                "location": global_weather["location"],
                "last_updated": global_weather["last_updated"],
                "summary": weather_service.get_weather_summary(),
                "detailed": weather_data  # 전체 기상 정보도 포함
            }
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"기상 정보 조회 실패: {str(e)}"
        }), 500


@app.route('/api/weather/update', methods=['POST', 'GET'])
def update_weather():
    """기상 데이터 수동 업데이트"""
    try:
        # 기본값을 USER_DATA에서 가져오기
        default_station = USER_DATA["location"]["station"]
        
        if request.method == 'POST':
            data = request.get_json() or {}
            station = data.get('station', default_station)
        else:  # GET
            station = request.args.get('station', default_station)
        
        success = weather_service.update_weather_data(station)
        
        if success:
            global_weather = get_current_weather_data()
            return jsonify({
                "status": "success",
                "message": "기상 데이터가 업데이트되었습니다.",
                "data": {
                    "temperature": global_weather["temperature"],
                    "precipitation": global_weather["precipitation"],
                    "humidity": global_weather["humidity"],
                    "location": global_weather["location"],
                    "last_updated": global_weather["last_updated"],
                    "status": global_weather["status"]
                }
            })
        else:
            return jsonify({
                "status": "error",
                "message": "기상 데이터 업데이트에 실패했습니다."
            }), 500
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"기상 데이터 업데이트 실패: {str(e)}"
        }), 500



if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)