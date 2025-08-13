# 사용자 정보 (추후 DB에서 불러올 데이터)
USER_DATA = {
    # 농장 기본 정보
    "farm_size_a": 250,  # 농장 크기 (a, 250a = 25,000㎡ = 2.5ha)
    
    "crop": {
        "code": "01001",  # 맥주보리 코드
        "name": "맥주보리",
        "current_crops": ["맥주보리"],
        "planting_date": {
            "맥주보리": "2025-04-01"
        },
        "growth_stage": {
            "맥주보리": "생육기"
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
