# 사용자 정보 (추후 DB에서 불러올 데이터)
USER_DATA = {
    # 농장 기본 정보
    "farm_size_a": 250,  # 농장 크기 (a, 250a = 25,000㎡ = 2.5ha)
    
    # 위치 정보
    "location": {
        "name": "구리시",
        "station": "108",                                # 기상 관측소 번호 (서울 108번)
        "full_address": "경기도 구리시 인창동 123-45",   # 상세 주소
    },
    
    "crop": {
        "name": "맥주보리",                    # 주 작물명 (매핑으로 코드 자동 생성)
        "current_crops": ["맥주보리", "콩", "양파"],         # 현재 재배 중인 작물들 (최대 3개)
        "planting_date": {
            "맥주보리": "2025-04-01",
            "콩": "2025-05-15", 
            "양파": "2025-10-20"
        },
        "growth_stage": {
            "맥주보리": "생육기",
            "콩": "개화기",
            "양파": "구근비대기"
        }
    },
    "soil": {
        "ph": 6.5,              # 산도(acid)
        "om": 22,               # 유기물(om, g/kg)
        "vldpha": 10,           # 유효인산(vldpha, mg/kg)
        "posifert_K": 4,        # 칼륨(posifert_K, cmol+/kg)
        "posifert_Ca": 6,       # 칼슘(posifert_Ca, cmol+/kg)
        "posifert_Mg": 13,      # 마그네슘(posifert_Mg, cmol+/kg)
        "selc": 6,              # 전기전도도(selc, dS/m)
        "last_test_date": "2025-07-01"
    },
    "intruder": {
        "recent_incidents": [
            {
                "time": "2025-08-11 22:30",
                "type": "person"
            }
        ]
    }
}
