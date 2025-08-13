"""
작물 매핑 유틸리티
작물명을 농업기술실용화재단 API 코드로 변환
"""

# 작물명 → API 코드 매핑 테이블
CROP_CODE_MAPPING = {
    # 맥류
    "맥주보리": "01001",
    "쌀보리": "01002", 
    "밀": "01003",
    "귀리": "01004",
    "호밀": "01005",
    
    # 벼류
    "쌀": "02001",
    "찰벼": "02002",
    "흑미": "02003",
    
    # 콩류
    "대두": "03001",
    "팥": "03002", 
    "녹두": "03003",
    "강낭콩": "03004",
    
    # 서류
    "감자": "04001",
    "고구마": "04002",
    
    # 채소류
    "배추": "05001",
    "무": "05002",
    "당근": "05003",
    "양파": "05004",
    "마늘": "05005",
    "생강": "05006",
    "토마토": "05007",
    "오이": "05008",
    "호박": "05009",
    "가지": "05010",
    "고추": "05011",
    "파프리카": "05012",
    
    # 과수류
    "사과": "06001",
    "배": "06002",
    "복숭아": "06003",
    "자두": "06004",
    "감": "06005",
    "포도": "06006",
    "키위": "06007",
    "딸기": "06008",
    
    # 특용작물
    "참깨": "07001",
    "들깨": "07002",
    "땅콩": "07003",
    "해바라기": "07004",
    
    # 사료작물
    "옥수수": "08001",
    "수수": "08002",
    "알팔파": "08003",
    
    # 화훼류
    "국화": "09001",
    "장미": "09002",
    "카네이션": "09003"
}

# API 코드 → 작물명 역매핑
CODE_TO_CROP_MAPPING = {code: name for name, code in CROP_CODE_MAPPING.items()}


def get_crop_code(crop_name: str) -> str:
    """
    작물명을 API 코드로 변환
    
    Args:
        crop_name: 작물명 (예: "맥주보리")
        
    Returns:
        API 코드 (예: "01001") 또는 None
    """
    return CROP_CODE_MAPPING.get(crop_name)


def get_crop_name(crop_code: str) -> str:
    """
    API 코드를 작물명으로 변환
    
    Args:
        crop_code: API 코드 (예: "01001")
        
    Returns:
        작물명 (예: "맥주보리") 또는 None
    """
    return CODE_TO_CROP_MAPPING.get(crop_code)


def get_all_supported_crops() -> list:
    """
    지원하는 모든 작물 목록 반환
    
    Returns:
        작물명 리스트
    """
    return list(CROP_CODE_MAPPING.keys())


def is_supported_crop(crop_name: str) -> bool:
    """
    해당 작물이 지원되는지 확인
    
    Args:
        crop_name: 작물명
        
    Returns:
        지원 여부 (bool)
    """
    return crop_name in CROP_CODE_MAPPING


def get_crop_category(crop_name: str) -> str:
    """
    작물의 카테고리 반환
    
    Args:
        crop_name: 작물명
        
    Returns:
        카테고리명
    """
    code = get_crop_code(crop_name)
    if not code:
        return None
        
    category_map = {
        "01": "맥류",
        "02": "벼류", 
        "03": "콩류",
        "04": "서류",
        "05": "채소류",
        "06": "과수류",
        "07": "특용작물",
        "08": "사료작물",
        "09": "화훼류"
    }
    
    return category_map.get(code[:2], "기타")


# 사용 예시
if __name__ == "__main__":
    print("=== 작물 매핑 테스트 ===")
    print(f"맥주보리 코드: {get_crop_code('맥주보리')}")
    print(f"01001 작물명: {get_crop_name('01001')}")
    print(f"맥주보리 카테고리: {get_crop_category('맥주보리')}")
    print(f"지원 작물 수: {len(get_all_supported_crops())}개")
