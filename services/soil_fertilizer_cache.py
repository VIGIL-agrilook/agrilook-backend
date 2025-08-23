import os, copy, logging

from config.user_data import USER_DATA
import time
from services.soil_fertilizer_service import SoilFertilizerService

logger = logging.getLogger(__name__)

fertilizer_cache = {}
_last_built_at = 0.0

def initialize_fertilizer_cache():
    """
    - 가능하면 SoilFertilizerService.build_front_payload(cropname, farmid) 사용 (전역 USER_DATA 변경 없음)
    - 없으면 기존 get_recommendation_bundle()로 폴백 (전역 USER_DATA를 일시 변경 후 복구)
    - 작물별로 캐시에 저장: key = f"{farm_id}_{cropname}"
    """
    logger.info("[INIT] Starting fertilizer cache initialization...")
    service = SoilFertilizerService()
    farm = USER_DATA.get("farm", {})
    farm_id = farm.get("_id", "farm")
    crops = farm.get("crops", [])

    # 원본 백업(폴백 루트에서만 사용)
    farm_backup = copy.deepcopy(farm)

    for crop in crops:
        cropname = crop.get("cropname")
        if not cropname:
            continue

        cache_key = f"{farm_id}_{cropname}"

        try:
            if hasattr(service, "build_front_payload"):
                # ✅ 선호 경로: 전역 USER_DATA 변경 없이 안전하게 계산
                payload = service.build_front_payload(cropname=cropname, farmid=farm_id)
                fertilizer_cache[cache_key] = payload
            else:
                # ⚠️ 폴백: 기존 번들 메서드 (전역 USER_DATA 일시 수정 → 복구)
                USER_DATA["farm"]["cropname"] = cropname
                USER_DATA["farm"]["crops"] = [crop]
                payload = service.get_recommendation_bundle()
                fertilizer_cache[cache_key] = payload

        except Exception as e:
            # 실패 시 캐시에 에러 상태를 기록 (챗봇에서 안내 가능)
            fertilizer_cache[cache_key] = {
                "status": "error",
                "message": f"{e.__class__.__name__}: {e}"
            }
            # 디버깅이 필요하면 로그 출력
            logger.exception("Fertilizer cache build failed for %s", cache_key)
        finally:
            # 폴백 경로를 탔을 때만 복구 (build_front_payload 경로는 USER_DATA 미변경)
            if not hasattr(service, "build_front_payload"):
                USER_DATA["farm"] = copy.deepcopy(farm_backup)


def initialize_fertilizer_cache_if_stale(ttl_seconds: int = 3600) -> bool:
    """캐시가 오래되었을 때만 재구축. 재빌드 시 True 반환."""
    global _last_built_at
    now = time.time()
    if now - _last_built_at < ttl_seconds:
        return False
    try:
        initialize_fertilizer_cache()
        _last_built_at = now
        return True
    except Exception:
        logger.exception("initialize_fertilizer_cache failed")
        return False