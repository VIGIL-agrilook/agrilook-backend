"""
Per-crop potassium (K) split overrides between basal(밑거름) and topdress(웃거름).

When the upstream API returns skewed K distribution (e.g., 10:0),
we can apply these domain rules to re-split the total K for the crop.

Values are ratios (0.0~1.0) and must sum to 1.0: (base_ratio, additional_ratio)

Populate/extend as domain knowledge becomes available.
"""

from typing import Optional, Tuple


# You can key by crop code (preferred) or crop name as fallback.
K_SPLIT_OVERRIDES = {
    # Examples (adjust with real agronomic guidance):
    # 맥주보리
    "01001": (0.4, 0.6),
    "맥주보리": (0.4, 0.6),
    # 토마토
    "07030": (0.3, 0.7),
    "토마토": (0.3, 0.7),
    # 양파
    "06010": (0.5, 0.5),
    "양파": (0.5, 0.5),
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



