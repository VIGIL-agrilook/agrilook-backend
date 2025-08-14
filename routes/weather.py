from flask import Blueprint, request, jsonify
from config.user_data import USER_DATA
from services.weather_service import weather_service
from utils.weather_utils import classify_weather

weather_bp = Blueprint('weather', __name__)

@weather_bp.route('/api/weather/current', methods=['GET'])
def get_current_weather():
    default_station = USER_DATA["location"]["station"]
    station = request.args.get('station', default_station)
    weather_data = weather_service.get_current_weather(station)
    USER_DATA['weather'] = weather_data if weather_data else {}
    if not weather_data:
        return jsonify({
            "temperature": None,
            "humidity": None,
            "precipitation": None,
            "weather": None
        })
    ca_tot = weather_data.get("ca_tot", 0)
    rn = weather_data.get("precipitation", 0)
    ta = weather_data.get("temperature", 0)
    weather = classify_weather(ca_tot, rn, ta)
    return jsonify({
        "temperature": ta,
        "humidity": weather_data.get("humidity", 0),
        "precipitation": rn,
        "weather": weather
    })
