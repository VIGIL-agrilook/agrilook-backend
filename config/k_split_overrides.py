"""
Per-crop potassium (K) split overrides between basal(밑거름) and topdress(웃거름).

When the upstream API returns skewed K distribution (e.g., 10:0),
we can apply these domain rules to re-split the total K for the crop.

Values are ratios (0.0~1.0) and must sum to 1.0: (base_ratio, additional_ratio)

Populate/extend as domain knowledge becomes available.
"""

from typing import Optional, Tuple


# 작물별 K 밑거름/웃거름 비율 (비율 합은 1.0)
K_SPLIT_OVERRIDES = {
    # 대파
    "05011": (8.6/(8.6+5.7), 5.7/(8.6+5.7)),
    "대파": (8.6/(8.6+5.7), 5.7/(8.6+5.7)),
    # 부추
    "05013": (9.4/(9.4+9.4), 9.4/(9.4+9.4)),
    "부추": (9.4/(9.4+9.4), 9.4/(9.4+9.4)),
    # 고추
    "07020": (13.8/(13.8+9.2), 9.2/(13.8+9.2)),
    "고추": (13.8/(13.8+9.2), 9.2/(13.8+9.2)),
    # 기타 예시
    # "맥주보리": (0.4, 0.6),
    # "토마토": (0.3, 0.7),
    # "양파": (0.5, 0.5),
}


def get_k_split_override(crop_name: Optional[str] = None, crop_code: Optional[str] = None) -> Optional[Tuple[float, float]]:
    """Return per-crop K split override ratios if known.

    Preference order: crop_code → crop_name. None if not available.
    """
    if crop_code and crop_code in K_SPLIT_OVERRIDES:
        return K_SPLIT_OVERRIDES[crop_code]
    if crop_name and crop_name in K_SPLIT_OVERRIDES:
        return K_SPLIT_OVERRIDES[crop_name]
    return None



