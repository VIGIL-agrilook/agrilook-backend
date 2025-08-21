import os
from typing import Dict, Any, Optional
from datetime import datetime

import pymongo
import re


def _get_mongo_client() -> pymongo.MongoClient:
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        raise RuntimeError("MONGO_URI not set in environment")
    return pymongo.MongoClient(mongo_uri)


def _find_user(db, user_id: Optional[str], user_email: Optional[str]):
    users = db.get_collection("users")
    # 1) by id
    if user_id:
        doc = users.find_one({"_id": user_id}) or users.find_one({"user_id": user_id})
        if doc:
            return doc
    # 2) by email
    if user_email:
        doc = users.find_one({"email": user_email})
        if doc:
            return doc
    return None


def _find_farm(db, farm_id: Optional[str], user: Optional[Dict[str, Any]]):
    farms = db.get_collection("farms")
    if farm_id:
        doc = farms.find_one({"_id": farm_id}) or farms.find_one({"farm_id": farm_id})
        if doc:
            return doc
    # fallback by user ownership
    if user:
        uid = user.get("_id") or user.get("user_id") or user.get("id")
        if uid:
            doc = (
                farms.find_one({"owner_id": uid})
                or farms.find_one({"user_id": uid})
                or farms.find_one({"ownerId": uid})
                or farms.find_one({"userId": uid})
                or farms.find_one({"user": uid})
            )
            if doc:
                return doc
    # any farm as last resort
    return farms.find_one({})


def _find_latest_soiltest(db, farm: Optional[Dict[str, Any]]):
    if not farm:
        return None
    farm_id = farm.get("_id") or farm.get("farm_id") or farm.get("farmId") or farm.get("id")

    # 선호 소스 우선: 기본은 sensor, 그 다음 satellite
    preferred = os.getenv("PREFERRED_SOIL_SRC", "sensor,satellite")
    preferred_list = [s.strip().lower() for s in preferred.split(",") if s.strip()]

    # farm id 키 후보들
    farm_filters = []
    if farm_id:
        farm_filters = [
            {"farmid": farm_id},
            {"farm_id": farm_id},
            {"farmId": farm_id},
        ]

    # 컬렉션명: soiltest (단수)
    soiltests = db.get_collection("soiltest")

    # 1) 선호 소스 + farm 매칭 순회
    for src in preferred_list:
        regex_src = {"$regex": f"^{re.escape(src)}$", "$options": "i"}
        for base_filter in (farm_filters or [{}]):
            q = dict(base_filter)
            q.update({"src": regex_src})
            doc = soiltests.find_one(q, sort=[("tested_at", pymongo.DESCENDING)])
            if doc:
                return doc

    # 2) farm만 기준으로 최신값
    if farm_id:
        doc = soiltests.find_one({"farmid": farm_id}, sort=[("tested_at", pymongo.DESCENDING)])
        if doc:
            return doc
        # some schemas might use farm_id key name
        doc = soiltests.find_one({"farm_id": farm_id}, sort=[("tested_at", pymongo.DESCENDING)])
        if doc:
            return doc
        doc = soiltests.find_one({"farmId": farm_id}, sort=[("tested_at", pymongo.DESCENDING)])
        if doc:
            return doc

    # 3) 선호 소스만으로 전체 중 최신값
    for src in preferred_list:
        regex_src = {"$regex": f"^{re.escape(src)}$", "$options": "i"}
        doc = soiltests.find_one({"src": regex_src}, sort=[("tested_at", pymongo.DESCENDING)])
        if doc:
            return doc

    # 4) 최종 폴백: 아무거나 최신
    doc = soiltests.find_one({}, sort=[("tested_at", pymongo.DESCENDING)])
    if doc:
        return doc

    return None


def _normalize_soil_result(soil: Dict[str, Any]) -> Dict[str, Any]:
    """
    흙토람 API 파라미터 키에 맞게 토양 결과를 정규화.
    입력 키 예: pH, OM, EC, P, K, Ca, Mg
    출력에 다음 키를 추가: ph, om, selc(EC), vldpha(P), posifert_K(K), posifert_Ca(Ca), posifert_Mg(Mg)
    원본 키는 그대로 유지하며, 숫자 변환을 시도.
    """
    if not isinstance(soil, dict):
        return {}

    def _parse_number_or_range(value: Any, default=None):
        """문자열에서 숫자 또는 범위를 파싱. 범위면 평균 반환."""
        if value is None:
            return default
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            # 숫자 추출 (부호, 소수 포함)
            nums = re.findall(r"[-+]?\d*\.?\d+", value.replace(",", ""))
            if not nums:
                return default
            try:
                floats = [float(n) for n in nums]
            except Exception:
                return default
            if len(floats) == 1:
                return floats[0]
            # 범위일 경우 평균값
            return sum(floats[:2]) / 2.0
        return default

    out = dict(soil)
    # 표준화 매핑
    out.setdefault("ph", _parse_number_or_range(soil.get("ph", soil.get("pH"))))
    out.setdefault("om", _parse_number_or_range(soil.get("om", soil.get("OM"))))
    out.setdefault("selc", _parse_number_or_range(soil.get("selc", soil.get("EC"))))
    out.setdefault("vldpha", _parse_number_or_range(soil.get("vldpha", soil.get("P"))))
    out.setdefault("posifert_K", _parse_number_or_range(soil.get("posifert_K", soil.get("K"))))
    out.setdefault("posifert_Ca", _parse_number_or_range(soil.get("posifert_Ca", soil.get("Ca"))))
    out.setdefault("posifert_Mg", _parse_number_or_range(soil.get("posifert_Mg", soil.get("Mg"))))
    return out


def load_user_data_from_db(user_id: Optional[str] = None, farm_id: Optional[str] = None, user_email: Optional[str] = None) -> Dict[str, Any]:
    """
    CosmosDB(Mongo API)에서 사용자 컨텍스트를 로드하여 USER_DATA 형태로 반환.
    - collections: users, farms, soiltests (관례적 기본값)
    - env: MONGO_URI, DB_NAME
    - 선택 env: USER_ID, FARM_ID
    """
    db_name = os.getenv("DB_NAME")
    if not db_name:
        raise RuntimeError("DB_NAME not set in environment")

    # env overrides
    user_id = user_id or os.getenv("USER_ID")
    farm_id = farm_id or os.getenv("FARM_ID")
    user_email = user_email or os.getenv("USER_EMAIL")

    client = _get_mongo_client()
    try:
        db = client[db_name]

        user = _find_user(db, user_id, user_email)
        farm = _find_farm(db, farm_id, user)
        soiltest = _find_latest_soiltest(db, farm)

        # 기본 방어값
        farm = farm or {}
        soil_raw = (soiltest or {}).get("result") or {}
        soil = _normalize_soil_result(soil_raw)

        # 위치 정보 유도 필드
        location = {
            "station": farm.get("stn"),
            "address": farm.get("address"),
            "coord": farm.get("coord"),
        }

        return {
            "farm": farm,
            "user": user or {},
            "soil": soil,
            "location": location,
            "weather": {},
        }
    finally:
        client.close()


def initialize_user_data_from_db(user_id: Optional[str] = None, farm_id: Optional[str] = None, user_email: Optional[str] = None) -> Dict[str, Any]:
    """
    DB에서 불러온 데이터를 `config.user_data.USER_DATA`에 주입하여
    기존 코드가 동일한 인터페이스로 동작하도록 초기화.
    """
    from config import user_data as user_data_module

    loaded = load_user_data_from_db(user_id=user_id, farm_id=farm_id, user_email=user_email)

    # 기존 모듈의 USER_DATA 내용을 교체 (참조 유지)
    user_data_module.USER_DATA.clear()
    user_data_module.USER_DATA.update(loaded)
    return user_data_module.USER_DATA


