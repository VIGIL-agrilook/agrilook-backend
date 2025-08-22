from flask import Blueprint, request, jsonify
from config.user_data import USER_DATA
from services.soil_fertilizer_service import SoilFertilizerService
from config.crop_codes import get_crop_code

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
    # 표준 파서/계산 사용
    prescription = service.fetch_fertilizer_api(farm_info)
    total_area_10a = area_sqm / 1000
    compost = service.get_compost_amounts(prescription, {"farm_size_10a": total_area_10a})

    # 비료 추천 로직
    base_fertilizers = []
    topdress_fertilizers = []

    # 처방 API 호출 및 필요량 추출 (위에서 이미 호출됨)
    from utils.fertilizer_recommender import recommend_fertilizers
    base_fertilizers = recommend_fertilizers(service, prescription, "base", 3)
    topdress_fertilizers = recommend_fertilizers(service, prescription, "topdress", 3)

    # 작물 코드
    crop_code = get_crop_code(crop_name)

    # 밑거름 비료 목록
    base_list = []
    for fert in base_fertilizers:
        base_list.append({
            "K_ratio": round(float(fert.get("K_ratio", 0) or 0), 2),
            "N_ratio": round(float(fert.get("N_ratio", 0) or 0), 2),
            "P_ratio": round(float(fert.get("P_ratio", 0) or 0), 2),
            "bags": round(float(fert.get("bags", 0) or 0), 2),
            "fertilizer_id": fert.get("fertilizer_id", fert.get("_id", "")),
            "fertilizer_name": fert.get("fertilizer_name", fert.get("name", "")),
            "need_K_kg": round(float(fert.get("need_K_kg", 0) or 0), 2),
            "need_N_kg": round(float(fert.get("need_N_kg", 0) or 0), 2),
            "need_P_kg": round(float(fert.get("need_P_kg", 0) or 0), 2),
            "shortage_K_kg": round(float(fert.get("shortage_K_kg", 0) or 0), 2),
            "shortage_P_kg": round(float(fert.get("shortage_P_kg", 0) or 0), 2),
            "usage_kg": round(float(fert.get("usage_kg", fert.get("amount", fert.get("bag_kg", 0)) ) or 0), 2)
        })

    # 웃거름 비료 목록
    additional_list = []
    for fert in topdress_fertilizers:
        additional_list.append({
            "K_ratio": round(float(fert.get("K_ratio", 0) or 0), 2),
            "N_ratio": round(float(fert.get("N_ratio", 0) or 0), 2),
            "P_ratio": round(float(fert.get("P_ratio", 0) or 0), 2),
            "bags": round(float(fert.get("bags", 0) or 0), 2),
            "fertilizer_id": fert.get("fertilizer_id", fert.get("_id", "")),
            "fertilizer_name": fert.get("fertilizer_name", fert.get("name", "")),
            "need_K_kg": round(float(fert.get("need_K_kg", 0) or 0), 2),
            "need_N_kg": round(float(fert.get("need_N_kg", 0) or 0), 2),
            "need_P_kg": round(float(fert.get("need_P_kg", 0) or 0), 2),
            "shortage_K_kg": round(float(fert.get("shortage_K_kg", 0) or 0), 2),
            "shortage_P_kg": round(float(fert.get("shortage_P_kg", 0) or 0), 2),
            "usage_kg": round(float(fert.get("usage_kg", fert.get("amount", fert.get("bag_kg", 0)) ) or 0), 2)
        })

    result_json = {
        "_id": farm.get("_id", "farm001"),
        "crop": {
            "code": crop_code,
            "name": prescription.get("crop_Nm", crop_name)
        },
        "compost": {
            "cattle_kg": round(float(compost["cattle_kg"] or 0), 2),
            "chicken_kg": round(float(compost["chicken_kg"] or 0), 2),
            "mixed_kg": round(float(compost["mixed_kg"] or 0), 2),
            "pig_kg": round(float(compost["pig_kg"] or 0), 2)
        },
        "fertilizer": {
            "base": base_list,
            "additional": additional_list
        }
    }
    return jsonify(result_json)
