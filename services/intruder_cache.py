"""
침입자 감지 데이터 캐시 서비스
챗봇 프롬프트에 포함할 침입자 정보를 관리
"""
import os
import pymongo
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

class IntruderCache:
    def __init__(self):
        self.cache_data = []
        self.last_updated = None
        self.cache_duration = 300  # 5분 캐시
    
    def _get_db(self):
        """MongoDB 연결"""
        mongo_uri = os.getenv("MONGO_URI")
        db_name = os.getenv("DB_NAME")
        if not mongo_uri or not db_name:
            return None, None
        client = pymongo.MongoClient(mongo_uri)
        return client, client[db_name]
    
    def _parse_datetime(self, datetime_str: str) -> Optional[datetime]:
        """침입자 데이터의 datetime 형식을 파싱 (20250822-173720)"""
        try:
            return datetime.strptime(datetime_str, "%Y%m%d-%H%M%S")
        except Exception:
            return None
    
    def _fetch_recent_intruders(self, hours_limit: int = 24) -> List[Dict[str, Any]]:
        """최근 침입자 데이터 조회"""
        client, db = self._get_db()
        if not client or not db:
            return []
        
        try:
            farm_id = os.getenv('FARM_ID')
            intruders = db.get_collection("intrusion_info")
            cutoff_time = datetime.utcnow() - timedelta(hours=hours_limit)
            
            # farm_id로 조회
            query = {}
            if farm_id:
                query["farm_id"] = farm_id
                
            all_docs = list(intruders.find(query).sort("datetime", pymongo.DESCENDING))
            
            # datetime 문자열을 파싱해서 필터링
            filtered_docs = []
            for doc in all_docs:
                datetime_str = doc.get("datetime", "")
                try:
                    doc_datetime = self._parse_datetime(datetime_str)
                    if doc_datetime and doc_datetime >= cutoff_time:
                        # 챗봇용이므로 필요한 정보만 추출
                        filtered_docs.append({
                            "class": doc.get("class", "unknown"),
                            "confidence": doc.get("confidence", "0%"),
                            "datetime": datetime_str,
                            "farm_id": doc.get("farm_id")
                        })
                except Exception:
                    continue
            
            return filtered_docs
            
        except Exception as e:
            logging.error(f"Failed to fetch intruder data: {e}")
            return []
        finally:
            if client:
                client.close()
    
    def get_intruder_summary(self, force_refresh: bool = False) -> str:
        """챗봇 프롬프트용 침입자 요약 텍스트 반환"""
        now = datetime.utcnow()
        
        # 캐시 갱신 필요 여부 체크
        if (force_refresh or 
            self.last_updated is None or 
            (now - self.last_updated).seconds > self.cache_duration):
            
            self.cache_data = self._fetch_recent_intruders()
            self.last_updated = now
            logging.info(f"Intruder cache updated: {len(self.cache_data)} records")
        
        if not self.cache_data:
            return "최근 24시간 내 침입자 감지 기록이 없습니다."
        
        # 클래스별 카운트
        class_counts = {}
        recent_detections = []
        
        for item in self.cache_data:
            class_name = item["class"]
            class_counts[class_name] = class_counts.get(class_name, 0) + 1
            recent_detections.append(f"{item['datetime']}: {class_name} (신뢰도: {item['confidence']})")
        
        # 요약 텍스트 생성
        summary_parts = []
        summary_parts.append(f"최근 24시간 내 총 {len(self.cache_data)}건의 침입자가 감지되었습니다.")
        
        if class_counts:
            count_text = ", ".join([f"{cls}: {count}건" for cls, count in class_counts.items()])
            summary_parts.append(f"감지된 대상: {count_text}")
        
        if recent_detections:
            summary_parts.append("최근 감지 기록:")
            summary_parts.extend(recent_detections[:5])  # 최근 5건만 표시
        
        return "\n".join(summary_parts)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """캐시 상태 정보 반환"""
        return {
            "cached_records": len(self.cache_data),
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "cache_duration_seconds": self.cache_duration
        }

# 글로벌 캐시 인스턴스
intruder_cache = IntruderCache()

def initialize_intruder_cache():
    """앱 시작 시 침입자 캐시 초기화"""
    try:
        intruder_cache.get_intruder_summary(force_refresh=True)
        logging.info("Intruder cache initialized")
    except Exception as e:
        logging.error(f"Failed to initialize intruder cache: {e}")

def get_intruder_context() -> str:
    """챗봇 컨텍스트용 침입자 정보 반환"""
    return intruder_cache.get_intruder_summary()
