"""五行工具：生克关系、六亲推演、旺衰判定、十二长生、旬空、暗动/日破判定。"""

from .data import (
    DIZHI, DIZHI_WUXING, WUXING_SHENG, WUXING_KE, WUXING_MU,
    SHIER_CHANGSHENG_START, SHIER_NAMES, SHIER_STRONG, SHIER_WEAK,
    TIANGAN, XUNKONG_BY_XUN, CHONG,
)


# ----------------------------------------------------------------
# 基本关系
# ----------------------------------------------------------------
def sheng_me(wx):
    """生我者的五行（谁生 wx）。"""
    for k, v in WUXING_SHENG.items():
        if v == wx:
            return k
    return None


def ke_me(wx):
    """克我者的五行（谁克 wx）。"""
    for k, v in WUXING_KE.items():
        if v == wx:
            return k
    return None


def i_sheng(wx):
    """我生者。"""
    return WUXING_SHENG[wx]


def i_ke(wx):
    """我克者。"""
    return WUXING_KE[wx]


# ----------------------------------------------------------------
# 六亲
# ----------------------------------------------------------------
def liuqin(yao_wx, palace_wx):
    """根据爻五行与本宫五行，返回六亲。

    以本宫五行为'我'：
        生我者 = 父母；我生者 = 子孙；克我者 = 官鬼；我克者 = 妻财；同我 = 兄弟。
    """
    if yao_wx == palace_wx:
        return "兄弟"
    if sheng_me(palace_wx) == yao_wx:   # yao 生 palace → 生我者 = 父母
        return "父母"
    if i_sheng(palace_wx) == yao_wx:    # palace 生 yao → 我生者 = 子孙
        return "子孙"
    if ke_me(palace_wx) == yao_wx:      # yao 克 palace → 克我者 = 官鬼
        return "官鬼"
    if i_ke(palace_wx) == yao_wx:       # palace 克 yao → 我克者 = 妻财
        return "妻财"
    return "兄弟"


def four_gods(yongshen_wx):
    """以用神五行为基准，返回四神的五行。

    用=本身；元=生用者(sheng_me)；忌=克用者(ke_me)；仇=克元者(=生忌者)。
    例：用=金 → 元=土, 忌=火, 仇=木(克土生火)。
    """
    yuan = sheng_me(yongshen_wx)
    ji = ke_me(yongshen_wx)
    chou = ke_me(yuan)  # 克元神者；亦 = sheng_me(ji) 生忌神者
    return {"用": yongshen_wx, "元": yuan, "忌": ji, "仇": chou}


def yongshen_role(yao_wx, yongshen_wx):
    """该爻(按五行)相对用神爻(按五行)的四神角色：用/元/忌/仇/闲。

    注意：以【用神爻的五行】为基准（非六亲），这才符合"元生用、忌克用、仇克元生忌"的定义。
    """
    if yao_wx == yongshen_wx:
        return "用神"
    g = four_gods(yongshen_wx)
    if yao_wx == g["元"]:
        return "元神"
    if yao_wx == g["忌"]:
        return "忌神"
    if yao_wx == g["仇"]:
        return "仇神"
    return "闲神"


# ----------------------------------------------------------------
# 真空（旬空 + 当令死地）
# ----------------------------------------------------------------
# 真空：春土、夏金、秋木、冬火（《增删卜易·旬空章》）
_TRUE_VOID = {
    "春": "土", "夏": "金", "秋": "木", "冬": "火",
}


def season_of(month_zhi):
    """月支 → 季节。四季月(辰戌丑未)返回 '季'（土当令，无真空）。"""
    if month_zhi in ("寅", "卯"):
        return "春"
    if month_zhi in ("巳", "午"):
        return "夏"
    if month_zhi in ("申", "酉"):
        return "秋"
    if month_zhi in ("亥", "子"):
        return "冬"
    return "季"  # 辰戌丑未


def is_true_void(yao_wx, month_zhi):
    """爻是否为'真空'：落旬空且其五行恰为当季真空之五行。须配合 is_void 使用。"""
    season = season_of(month_zhi)
    return _TRUE_VOID.get(season) == yao_wx


# ----------------------------------------------------------------
# 旺相休囚死（按月令当令五行）
# ----------------------------------------------------------------
def wuxing_state(yao_wx, ling_wx):
    """爻五行在当令五行(月令)下的状态：旺/相/休/囚/死。"""
    if yao_wx == ling_wx:
        return "旺"
    if sheng_me(ling_wx) == yao_wx:   # 生令者 = 相
        return "相"
    if i_sheng(ling_wx) == yao_wx:    # 令生者 = 休
        return "休"
    if ke_me(ling_wx) == yao_wx:      # 克令者 = 囚
        return "囚"
    if i_ke(ling_wx) == yao_wx:       # 令克者 = 死
        return "死"
    return "休"


# ----------------------------------------------------------------
# 十二长生
# ----------------------------------------------------------------
def shier_changsheng(yao_wx, dz):
    """爻五行(以地支 dz 代表位置)在十二长生中的阶段名。返回阶段名或 None。"""
    start = SHIER_CHANGSHENG_START.get(yao_wx)
    if start is None:
        return None
    start_idx = DIZHI.index(start)
    dz_idx = DIZHI.index(dz)
    # 地支顺行：(dz_idx - start_idx) % 12 为步数
    step = (dz_idx - start_idx) % 12
    return SHIER_NAMES[step]


# ----------------------------------------------------------------
# 爻的旺衰判定（用于暗动/日破、用神有力无力）
# ----------------------------------------------------------------
def is_prosperous(yao_wx, yao_dz, month_dz, day_dz):
    """判断爻是否旺相。

    综合月令旺相休囚死、月日生扶比和、十二长生进气。
    旺相、得月日生、得月日比和、或处长生/冠带/临官/帝旺 → 视为旺相。
    """
    month_wx = DIZHI_WUXING[month_dz]
    day_wx = DIZHI_WUXING[day_dz]

    # 1. 月令旺相
    st = wuxing_state(yao_wx, month_wx)
    if st in ("旺", "相"):
        return True
    # 2. 月生日、日生日（生扶）
    if i_sheng(month_wx) == yao_wx or i_sheng(day_wx) == yao_wx:
        return True
    # 3. 月比和、日比和
    if month_wx == yao_wx or day_wx == yao_wx:
        return True
    # 4. 十二长生进气（旺相阶段）
    stage = shier_changsheng(yao_wx, yao_dz)
    if stage in SHIER_STRONG:
        return True
    return False


# ----------------------------------------------------------------
# 旬空
# ----------------------------------------------------------------
def ganzhi_index(gan, zhi):
    """六十甲子序号 0..59。"""
    gi = TIANGAN.index(gan)
    zi = DIZHI.index(zhi)
    n = gi
    while n % 12 != zi:
        n += 10
    return n  # 必在 0..59


def xunkong(day_gz):
    """由日干支(如 '辛卯')查旬空，返回两个空亡地支的元组。"""
    g, z = day_gz[0], day_gz[1]
    n = ganzhi_index(g, z)
    return XUNKONG_BY_XUN[n // 10]


def is_void(yao_dz, day_gz):
    """爻地支是否落空亡。"""
    return yao_dz in xunkong(day_gz)


# ----------------------------------------------------------------
# 冲
# ----------------------------------------------------------------
def is_chong(a, b):
    return CHONG.get(a) == b
