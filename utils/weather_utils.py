"""
기상 관련 유틸리티 함수들
"""

# 날씨 분류 함수
def classify_weather(ca_tot, precipitation, temperature):
    """
    구름량, 강수량, 온도를 기반으로 날씨를 분류합니다.
    
    Args:
        ca_tot (float): 총 구름량 (0-10 스케일)
        precipitation (float): 강수량 (mm)
        temperature (float): 온도 (°C)
    
    Returns:
        str: 날씨 분류 ('비', '눈', '흐림', '조금 흐림', '맑음')
    """
    if precipitation > 0:
        if temperature <= 0:
            return "눈"
        else:
            return "비"
    elif ca_tot >= 8:
        return "흐림"
    elif ca_tot >= 4:
        return "조금 흐림"
    else:
        return "맑음"