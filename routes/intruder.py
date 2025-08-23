from flask import Blueprint, request, jsonify
import os
import pymongo
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import re

intruder_bp = Blueprint('intruder', __name__)


def _get_db():
    mongo_uri = os.getenv("MONGO_URI")
    db_name = os.getenv("DB_NAME")
    if not mongo_uri or not db_name:
        raise RuntimeError("MONGO_URI/DB_NAME not set in environment")
    client = pymongo.MongoClient(mongo_uri)
    return client, client[db_name]


def _parse_datetime(datetime_str: str) -> Optional[datetime]:
    """침입자 데이터의 datetime 형식을 파싱 (20250822-173720)"""
    try:
        return datetime.strptime(datetime_str, "%Y%m%d-%H%M%S")
    except Exception:
        return None


def _to_iso(dt: Any) -> Optional[str]:
    if isinstance(dt, datetime):
        return dt.isoformat()
    try:
        return dt.isoformat()
    except Exception:
        return None


def _get_blob_image_url(datetime_str: str, detected_class: str) -> str:
    """Blob Storage 이미지 URL 생성"""
    blob_base_url = os.getenv("AZURE_BLOB_BASE_URL", "https://yourstorage.blob.core.windows.net/images")
    # full_20250822-101810_wild_rabbit.jpg 형식으로 추정
    filename = f"full_{datetime_str}_{detected_class}.jpg"
    return f"{blob_base_url}/{filename}"


def _find_intruder_data(db, farm_id: Optional[str], hours_limit: int = 24) -> List[Dict[str, Any]]:
    """침입자 감지 데이터 조회"""
    intruders = db.get_collection("intrusion_info")
    
    # 시간 필터 (24시간 전부터)
    cutoff_time = datetime.utcnow() - timedelta(hours=hours_limit)
    
    # 쿼리 조건
    query = {}
    if farm_id:
        query["farm_id"] = farm_id
    
    # 모든 문서 가져와서 datetime 필터링 (문자열 형태이므로)
    all_docs = list(intruders.find(query).sort("datetime", pymongo.DESCENDING))
    
    filtered_docs = []
    for doc in all_docs:
        doc_datetime = _parse_datetime(doc.get("datetime", ""))
        if doc_datetime and doc_datetime >= cutoff_time:
            filtered_docs.append(doc)
    
    return filtered_docs


@intruder_bp.route('/api/intruder/recent', methods=['GET'])
def get_recent_intruders():
    """최근 24시간 내 침입자 감지 데이터 반환 (프론트엔드용 - 이미지 포함)"""
    farm_id = request.args.get('farmid') or os.getenv('FARM_ID')
    hours_param = request.args.get('hours', '24')
    
    try:
        hours_limit = int(hours_param) if hours_param and hours_param.isdigit() else 24
    except ValueError:
        hours_limit = 24
    
    client, db = _get_db()
    try:
        intruder_docs = _find_intruder_data(db, farm_id, hours_limit)
        
        # 프론트엔드용 데이터 구성 (이미지 URL 포함)
        results = []
        for doc in intruder_docs:
            datetime_str = doc.get("datetime", "")
            detected_class = doc.get("class", "unknown")
            
            result_item = {
                "id": doc.get("_id"),
                "class": detected_class,
                "confidence": doc.get("confidence", "0%"),
                "datetime": datetime_str,
                "datetime_iso": _to_iso(_parse_datetime(datetime_str)),
                "farm_id": doc.get("farm_id"),
                "image_url": _get_blob_image_url(datetime_str, detected_class)
            }
            results.append(result_item)
        
        # 클래스별 카운트
        class_counts = {}
        for item in results:
            class_name = item["class"]
            class_counts[class_name] = class_counts.get(class_name, 0) + 1
        
        return jsonify({
            "farm_id": farm_id,
            "hours_filter": hours_limit,
            "total_count": len(results),
            "class_counts": class_counts,
            "data": results
        })
    
    finally:
        client.close()



