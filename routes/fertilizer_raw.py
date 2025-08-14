from flask import Blueprint, request, jsonify
from config.user_data import USER_DATA
from services.soil_fertilizer_service import SoilFertilizerService
from config.crop_codes import get_crop_code

fertilizer_raw_bp = Blueprint('fertilizer_raw', __name__)

@fertilizer_raw_bp.route('/api/fertilizer-raw', methods=['POST'])
def get_fertilizer_raw():
    data = request.get_json() if request.is_json else {}
    crop_name = data.get('cropName', USER_DATA.get('crop', {}).get('name', '맥주보리'))
    soil_data = data.get('soil', USER_DATA.get('soil', {}))
    farm = USER_DATA.get('farm', {})
    area_sqm = farm.get('area_m2', 25000)
    farm_size_a = area_sqm / 100
    crop_code = get_crop_code(crop_name)
    farm_info = {
        'crop_name': crop_name,
        'crop_code': crop_code,
        'soil': soil_data,
        'farm_size_a': farm_size_a
    }
    service = SoilFertilizerService()
    # API 호출 및 파싱
    raw_result = service.get_raw_public_api_result(farm_info)
    import xml.etree.ElementTree as ET
    root = ET.fromstring(raw_result)
    item = root.find('.//item')
    def get_float(tag):
        if item is None:
            return 0.0
        val = item.findtext(tag)
        try:
            return float(val)
        except:
            return 0.0
    def get_text(tag, default=None):
        if item is None:
            return default
        return item.findtext(tag, default)

    # 퇴비 4종류
    total_area_10a = area_sqm / 1000
    compost = {
        "cattle_kg": get_float("pre_Compost_Cattl") * total_area_10a,
        "chicken_kg": get_float("pre_Compost_Chick") * total_area_10a,
        "mixed_kg": get_float("pre_Compost_Mix") * total_area_10a,
        "pig_kg": get_float("pre_Compost_Pig") * total_area_10a
    }

    # 비료 추천 로직 (함수 scope 밖으로 이동)
    base_fertilizers = []
    topdress_fertilizers = []
    composts = []

    # 밑거름 추천
    for fert in service.get_fertilizer_recommendations(crop_name, area_sqm).get('base', [])[:3]:
        base_fertilizers.append({
            "name": fert.get("name"),
            "amount": fert.get("amount"),
            "unit": fert.get("unit"),
            "nutrient": fert.get("nutrient"),
            "type": "base"
        })

    # 웃거름 추천
    for fert in service.get_fertilizer_recommendations(crop_name, area_sqm).get('topdress', [])[:3]:
        topdress_fertilizers.append({
            "name": fert.get("name"),
            "amount": fert.get("amount"),
            "unit": fert.get("unit"),
            "nutrient": fert.get("nutrient"),
            "type": "topdress"
        })

    # 퇴비 추천
    for comp in compost.items():
        composts.append({
            "name": comp[0],
            "amount": comp[1],
            "unit": "kg",
            "type": "compost"
        })

    result_json = {
        "compost": compost,
        "crop": {"name": get_text("crop_Nm", crop_name)},
            "fertilizer": {
                "basal": base_fertilizers,
                "topdress": topdress_fertilizers
            },
        "field": {
            "area_sqm": area_sqm,
            "id": farm.get("_id", "farm001")
        }
    }
    return jsonify(result_json)
