"""
기상 관련 유틸리티 함수들
"""
from config.user_data import USER_DATA


def parse_city_from_address(full_address: str) -> str:
    """
    전체 주소에서 시/구 정보 추출
    예: "경기도 구리시 인창동 123-45" -> "구리시"
    """
    try:
        parts = full_address.split()
        for part in parts:
            if part.endswith(('시', '구', '군')):
                return part
        return parts[1] if len(parts) > 1 else ""
    except:
        return ""


def safe_float(value: str) -> float:
    """문자열을 안전하게 float로 변환"""
    try:
        if value and value.strip() != '':
            return float(value)
        return None
    except ValueError:
        return None


def get_location_codes_by_city(city: str) -> dict:
    """
    도시명으로 기상청 관련 코드들 조회
    나중에 DB나 설정 파일에서 불러올 수 있도록 확장 가능
    """
    location_mapping = {
        "구리시": {
            "station": "108",  # 서울 관측소
            "forecast_region": "11B20501",  # 구리시 예보구역
            "grid_x": 62,  # 격자 X (임시값)
            "grid_y": 126  # 격자 Y (임시값)
        },
        "서울": {
            "station": "108",
            "forecast_region": "11B10101",
            "grid_x": 60,
            "grid_y": 127
        },
        "인천": {
            "station": "112", 
            "forecast_region": "11B20201",
            "grid_x": 55,
            "grid_y": 124
        },
        # 나중에 더 많은 지역 추가 가능
    }
    
    return location_mapping.get(city, {})
