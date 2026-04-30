"""
Python-layer base type evaluation — no LLM involved.
All boolean decisions (is base high-value? does influence exception apply?)
are computed here so the LLM only needs to handle mod quality analysis.
"""

# High-value bases: English name → Chinese name(s) pairs.
# Keys are lowercase for case-insensitive matching.
HIGH_VALUE_BASES: dict[str, str] = {
    # Claw
    "eagle claw": "鷹爪刃",
    "gemini claw": "雙子爪",
    "hellion's paw": "獄犬爪",
    "imperial claw": "帝國爪",
    "noble claw": "貴族爪",
    "terror claw": "恐懼爪",
    "twin claw": "雙爪",
    # One Hand Sword
    "battered foil": "破損細劍", "corsair Sword": "海盜劍",
    "elegant foil": "優雅細劍", "fancy foil": "華麗細劍",
    "jewelled foil": "寶石細劍", "poignard": "短劍",
    "serrated foil": "鋸齒細劍", "spiraled foil": "螺旋細劍",
    "stiletto": "匕首", "whalebone rapier": "鯨骨劍",
    "wyrmbone rapier": "飛龍骨劍",
    # One Hand Axe
    "despot axe": "暴君斧", "reaver axe": "掠奪者斧",
    # Two Hand Axe
    "apex cleaver": "頂點劈刀", "honed cleaver": "磨製劈刀",
    "infernal blade": "地獄刃", "psychotic axe": "狂亂斧",
    "vaal axe": "瓦爾斧",
    # One Hand Mace
    "boom mace": "爆裂錘", "crack mace": "破裂錘", "piledriver": "打樁錘",
    # Dagger
    "pneumatic dagger": "氣動匕首", "pressurised dagger": "加壓匕首",
    # Wand
    "blasting wand": "爆破法杖", "calling wand": "召喚法杖",
    "congregator wand": "聚集法杖", "convoking wand": "召集法杖",
    "kinetic wand": "動能法杖", "opal wand": "蛋白石法杖",
    "profane wand": "褻瀆法杖", "prophecy wand": "預言法杖",
    "somatic wand": "軀體法杖", "tornado wand": "龍捲法杖",
    # Staff
    "battery staff": "電池法杖", "eventuality rod": "終局之杖",
    "ezomyte staff": "艾佐邁特法杖", "potentiality rod": "潛能之杖",
    "reciprocation staff": "互惠法杖",
    # Bow
    "foundry bow": "熔爐弓", "grove bow": "林地弓",
    "harbinger bow": "先兆弓", "highborn bow": "貴族弓",
    "imperial bow": "帝國弓", "ivory bow": "象牙弓",
    "maraketh bow": "馬拉凱斯弓", "reflex bow": "反射弓",
    "short bow": "短弓", "solarine bow": "索拉林弓",
    "spine bow": "脊刺弓", "steelwood bow": "鋼木弓",
    "thicket bow": "灌木弓",
    # Ring
    "amethyst ring": "紫晶戒指", "cerulean ring": "蔚藍戒指",
    "diamond ring": "鑽石戒指", "opal ring": "蛋白石戒指",
    "prismatic ring": "稜鏡戒指", "steel ring": "鋼鐵戒指",
    "vermillion ring": "辰砂戒指",
    # Amulet
    "agate amulet": "瑪瑙護符", "jade amulet": "翡翠護符",
    "lapis amulet": "天青石護符", "onyx amulet": "縞瑪瑙護符",
    "turquoise amulet": "綠松石護符",
    # Belt
    "crystal belt": "水晶腰帶", "heavy belt": "重型腰帶",
    "stygian vise": "冥河腰帶",
}

# Reverse map: Chinese → English (built automatically)
_ZH_TO_EN: dict[str, str] = {zh: en for en, zh in HIGH_VALUE_BASES.items()}

# All names (lower-cased) in a fast lookup set
_ALL_HIGH_VALUE: set[str] = set(HIGH_VALUE_BASES.keys()) | {zh.lower() for zh in HIGH_VALUE_BASES.values()}


# 武器廢詞關鍵字（出現即嚴重扣分）
WASTE_MOD_KEYWORDS = [
    "魔力回復率", "魔力回生速度", "光源範圍", "暈眩持續時間", "屬性需求",
    "mana recovery rate", "mana regeneration rate", "light radius",
    "stun duration", "attribute requirements",
]

# 武器高價值詞綴關鍵字
ATTACK_SPEED_KEYWORDS = ["攻擊速度", "attack speed"]
PHYS_PCT_KEYWORDS = ["增加", "物理傷害"]  # 同時出現才算


def analyze_weapon_mods(item_text: str) -> dict:
    text_lower = item_text.lower()
    found_waste = [kw for kw in WASTE_MOD_KEYWORDS if kw.lower() in text_lower]

    has_attack_speed = any(kw.lower() in text_lower for kw in ATTACK_SPEED_KEYWORDS)

    # 物傷% 需要「增加」+「物理傷害」同時出現在同一行
    has_phys_pct = any(
        "增加" in line and "物理傷害" in line
        for line in item_text.splitlines()
    )

    return {
        "waste_mods": found_waste,
        "has_waste": len(found_waste) > 0,
        "has_attack_speed": has_attack_speed,
        "has_phys_pct": has_phys_pct,
    }


WEAPON_ITEM_TYPES = ["爪", "劍", "斧", "錘", "匕首", "法杖", "弓", "魔杖", "杖",
                     "claw", "sword", "axe", "mace", "dagger", "staff", "bow", "wand"]

_VERDICT_LEVELS = ["沒價值", "過渡裝", "低價值", "高價值"]


def is_weapon(item_text: str) -> bool:
    for line in item_text.splitlines():
        if "物品種類" in line or "item class" in line.lower():
            return any(t in line for t in WEAPON_ITEM_TYPES)
    return False


def is_high_value_base(base_type: str) -> bool:
    return base_type.strip().lower() in _ALL_HIGH_VALUE


def evaluate_base(base_type: str, has_influence: bool, ilvl_ge_80: bool) -> tuple[str, str]:
    if is_high_value_base(base_type):
        return "high_value_base", f"基底 {base_type} 為高價值基底"
    if has_influence and ilvl_ge_80:
        return "synthesis_candidate", f"基底 {base_type} 不在高價值列表，但有勢力標記且物品等級 ≥ 80，可作為合成用"
    return "no_value", f"基底 {base_type} 不在高價值基底列表，且無有效勢力例外條件（勢力:{has_influence}, ilvl≥80:{ilvl_ge_80}）"


def compute_verdict(base_verdict: str, mods: dict, item_text: str) -> tuple[str, list[str]]:
    """
    計算最終評級（完全由 Python 決定，不依賴 LLM）。
    Returns (verdict_label, reasons_list)
    """
    reasons = []

    if base_verdict == "no_value":
        return "沒價值", ["基底不在高價值列表，且無有效勢力例外"]

    if base_verdict == "synthesis_candidate":
        return "合成用", ["基底不在高價值列表，但有勢力標記且物品等級 ≥ 80，具合成價值"]

    # 高價值基底：從分數 3 開始扣分
    score = 3
    reasons.append("基底為高價值基底")

    weapon = is_weapon(item_text)

    if mods["has_waste"]:
        score -= 1
        waste_names = "、".join(mods["waste_mods"])
        reasons.append(f"含廢詞（{waste_names}），嚴重扣分")

    if weapon:
        if not mods["has_attack_speed"]:
            score -= 1
            reasons.append("缺少攻速詞綴，DPS 上限低")
        if not mods["has_phys_pct"]:
            score -= 1
            reasons.append("缺少物理傷害百分比詞綴，DPS 上限低")

    score = max(0, score)
    label = _VERDICT_LEVELS[score]
    return label, reasons
