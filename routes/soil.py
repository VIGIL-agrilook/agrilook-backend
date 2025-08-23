from flask import Blueprint, request, jsonify
import os
import pymongo
from typing import Optional, Dict, Any
from datetime import datetime

soil_bp = Blueprint('soil', __name__)


def _get_db():
	mongo_uri = os.getenv("MONGO_URI")
	db_name = os.getenv("DB_NAME")
	if not mongo_uri or not db_name:
		raise RuntimeError("MONGO_URI/DB_NAME not set in environment")
	client = pymongo.MongoClient(mongo_uri)
	return client, client[db_name]


def _find_latest_soil(db, farm_id: Optional[str], src_exact: str) -> Optional[Dict[str, Any]]:
	soiltests = db.get_collection("soiltest")
	farm_filters = []
	if farm_id:
		farm_filters = [
			{"farmid": farm_id},
			{"farm_id": farm_id},
			{"farmId": farm_id},
		]
	for base in (farm_filters or [{}]):
		q = dict(base)
		q.update({"src": {"$regex": f"^{src_exact}$", "$options": "i"}})
		doc = soiltests.find_one(q, sort=[("tested_at", pymongo.DESCENDING)])
		if doc:
			return doc
	return None


def _to_iso(dt: Any) -> Optional[str]:
	if isinstance(dt, datetime):
		return dt.isoformat()
	try:
		# pymongo might return tz-aware datetime; isoformat handles both
		return dt.isoformat()  # type: ignore[attr-defined]
	except Exception:
		return None


def _respond_latest(src_exact: str):
	farm_id = request.args.get('farmid') or os.getenv('FARM_ID')
	client, db = _get_db()
	try:
		row = _find_latest_soil(db, farm_id, src_exact=src_exact)
		if not row:
			return jsonify({
				"message": "해당 조건의 토양검사 데이터가 없습니다.",
				"farm_id": farm_id,
				"source": src_exact
			})
		
		# DB 구조 그대로 반환 (tested_at은 ISO 형식으로 변환)
		result = dict(row)
		if row.get("tested_at"):
			result["tested_at"] = _to_iso(row["tested_at"])
		
		return jsonify(result)
	finally:
		client.close()


@soil_bp.route('/api/soil/sensor', methods=['GET'])
def get_sensor_soil():
	"""최신 센서 기반 토양검사 결과 반환"""
	return _respond_latest("sensor")


# 위성 기반: 표준 철자(satellite)만 지원 (통일)
@soil_bp.route('/api/soil/satellite', methods=['GET'])
def get_satellite_soil():
	"""최신 위성 기반 토양검사 결과 반환"""
	return _respond_latest("satellite")
