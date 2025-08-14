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
    # 무조건 USER_DATA의 stn 값 반환
    stn = str(USER_DATA["farm"].get("stn", ""))
    return {"station": stn}

# 날씨 분류 함수 (간단 예시)
def classify_weather(ca_tot, precipitation, temperature):
    """
    간단한 날씨 분류 예시 (실제 로직은 필요에 따라 수정)
    """
    if precipitation > 0:
        return "비"
    elif ca_tot > 7:
        return "흐림"
    elif temperature > 30:
        return "더움"
    else:
        return "맑음"
