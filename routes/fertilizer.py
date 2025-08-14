from flask import Blueprint, request, jsonify
from config.user_data import USER_DATA
from services.soil_fertilizer_service import SoilFertilizerService
from utils.crop_mapper import get_crop_code
import os, json
import xml.etree.ElementTree as ET

fertilizer_bp = Blueprint('fertilizer', __name__)

@fertilizer_bp.route('/api/fertilizer-recommendation', methods=['POST'])
def get_fertilizer_recommendation():
    data = request.get_json() if request.is_json else {}
    crop_name = data.get('cropname', USER_DATA.get('crop', {}).get('name', '맥주보리'))
    field_id = data.get('farmid', 'farm001')
    farm_list = USER_DATA.get('farms', [])
    farm = next((f for f in farm_list if f.get('_id') == field_id), USER_DATA.get('farm', {}))
    area_sqm = farm.get('area_m2', USER_DATA.get('farm_size_a', 250) * 100)
    soil_data = farm.get('soil', USER_DATA.get('soil', {}))
    farm_size_a = area_sqm / 100
    crop_code = get_crop_code(crop_name)
    farm_info = {
        'crop_name': crop_name,
        'crop_code': crop_code,
        'soil': soil_data,
        'farm_size_a': farm_size_a
    }
    service = SoilFertilizerService()
    raw_result = service.get_raw_public_api_result(farm_info)
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


    # 비료 추천 로직
    service = SoilFertilizerService()
    base_fertilizers = []
    topdress_fertilizers = []
    composts = []

    # 처방 API 호출 및 필요량 추출
    prescription = service.fetch_fertilizer_api(farm_info)

    from utils.fertilizer_recommender import recommend_fertilizers
    base_fertilizers = recommend_fertilizers(service, prescription, "base", 3)
    topdress_fertilizers = recommend_fertilizers(service, prescription, "topdress", 3)

    # 퇴비 추천
    for comp in compost.items():
        composts.append({
            "name": comp[0],
            "amount": comp[1],
            "unit": "kg",
            "type": "compost"
        })

    # 작물 코드
    crop_code = get_crop_code(crop_name)

    # 밑거름 비료 목록
    base_list = []
    for fert in base_fertilizers:
        base_list.append({
            "K_ratio": fert.get("K_ratio", 0),
            "N_ratio": fert.get("N_ratio", 0),
            "P_ratio": fert.get("P_ratio", 0),
            "bags": fert.get("bags", 0),
            "fertilizer_id": fert.get("fertilizer_id", fert.get("_id", "")),
            "fertilizer_name": fert.get("fertilizer_name", fert.get("name", "")),
            "need_K_kg": fert.get("need_K_kg", 0),
            "need_N_kg": fert.get("need_N_kg", 0),
            "need_P_kg": fert.get("need_P_kg", 0),
            "shortage_K_kg": fert.get("shortage_K_kg", 0),
            "shortage_P_kg": fert.get("shortage_P_kg", 0),
            "usage_kg": fert.get("usage_kg", fert.get("amount", fert.get("bag_kg", 0)))
        })

    # 웃거름 비료 목록
    additional_list = []
    for fert in topdress_fertilizers:
        additional_list.append({
            "K_ratio": fert.get("K_ratio", 0),
            "N_ratio": fert.get("N_ratio", 0),
            "P_ratio": fert.get("P_ratio", 0),
            "bags": fert.get("bags", 0),
            "fertilizer_id": fert.get("fertilizer_id", fert.get("_id", "")),
            "fertilizer_name": fert.get("fertilizer_name", fert.get("name", "")),
            "need_K_kg": fert.get("need_K_kg", 0),
            "need_N_kg": fert.get("need_N_kg", 0),
            "need_P_kg": fert.get("need_P_kg", 0),
            "shortage_K_kg": fert.get("shortage_K_kg", 0),
            "shortage_P_kg": fert.get("shortage_P_kg", 0),
            "usage_kg": fert.get("usage_kg", fert.get("amount", fert.get("bag_kg", 0)))
        })

    result_json = {
        "_id": farm.get("_id", "farm001"),
        "crop": {
            "code": crop_code,
            "name": get_text("crop_Nm", crop_name)
        },
        "compost": {
            "cattle_kg": compost["cattle_kg"],
            "chicken_kg": compost["chicken_kg"],
            "mixed_kg": compost["mixed_kg"],
            "pig_kg": compost["pig_kg"]
        },
        "fertilizer": {
            "base": base_list,
            "additional": additional_list
        }
    }
    return jsonify(result_json)
