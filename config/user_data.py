# USER_DATA 구조 설명 및 활용 목적
# ---------------------------------
# 1. 샘플/기본값 제공: DB 연동 전에도 API가 정상 동작하도록 함
# 2. 구조 변환: 실제 DB 구조와 API 응답 구조를 매핑
# 3. 테스트/개발 편의: 프론트엔드 연동 및 예시 응답 검증에 사용
# 4. 동적 데이터 활용: 농장, 위치, 작물, 토양 등 다양한 정보 통합
# ---------------------------------
# 테스트용 샘플 데이터 (실제로는 DB에서 조회)
# 새로운 DB 스키마 구조에 맞춘 샘플 데이터

# users 컬렉션 샘플
SAMPLE_USER = {
    "_id": "user001",
    "name": "김농부",
    "email": "farmer@example.com"
}

# farm 컬렉션 샘플  
SAMPLE_FARM = {
    "_id": "farm001",
    "name": "김농부네 농장",
    "address": "경기도 구리시 인창동 123-45",
    "stn": 108,
    "area_m2": 25000,  # 25,000㎡ = 250a
    "coord": { 
        "lon": 127.1295,  # 구리시 경도
        "lat": 37.5943    # 구리시 위도
    },
    "is_geocoded": True,
    "crops": [
        {
            "_id": "crop001",
            "cropname": "맥주보리", 
            "planted_at": "2025-04-01T00:00:00Z",
            "status": "growing"
        },
        {
            "_id": "crop002", 
            "cropname": "콩",
            "planted_at": "2025-05-15T00:00:00Z", 
            "status": "growing"
        },
        {
            "_id": "crop003",
            "cropname": "양파",
            "planted_at": "2025-10-20T00:00:00Z",
            "status": "growing" 
        }
    ]
}

# soiltest 컬렉션 샘플
SAMPLE_SOILTEST = {
    "_id": "soiltest001",
    "farmid": "farm001", 
    "tested_at": "2025-07-01T09:00:00Z",
    "src": "흙토람",
    "result": {
        "pH": 6.5,
        "OM": 22.0,     # 유기물 g/kg
        "EC": 6.0,      # 전기전도도 dS/m  
        "P": 10.0,      # 유효인산 mg/kg
        "K": 4.0,       # 치환성칼리 cmol+/kg
        "Ca": 6.0,      # 치환성칼슘 cmol+/kg
        "Mg": 13.0      # 치환성마그네슘 cmol+/kg
    }
}

# 헬퍼 함수들
def get_sample_farm():
    """샘플 농장 데이터 반환"""
    return SAMPLE_FARM

def get_sample_soiltest():
    """샘플 토양검사 데이터 반환"""  
    return SAMPLE_SOILTEST

def get_growing_crops(farm_data=None):
    """재배 중인 작물 목록 반환"""
    farm = farm_data or SAMPLE_FARM
    return [crop for crop in farm["crops"] if crop["status"] == "growing"]

# 실제 서비스에서 사용하는 통합 사용자 데이터
USER_DATA = {
    "farm": SAMPLE_FARM,
    "user": SAMPLE_USER,
    "soil": SAMPLE_SOILTEST["result"],
    "location": {
        "station": SAMPLE_FARM["stn"],
        "address": SAMPLE_FARM["address"],
        "coord": SAMPLE_FARM["coord"]
    },
    "weather": {},  # 실시간 날씨 정보는 서비스에서 업데이트
    # 필요한 모든 주요 필드가 USER_DATA에 포함되도록 보장
}
