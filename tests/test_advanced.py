"""进阶判定测试：四神、有力无力、真空、临日建、卦变反伏、三合虚合。

对应 P0+P1 升级项，验证引擎新增的判定逻辑。
"""

from liuyao import cast_board
from liuyao.wuxing import four_gods, is_true_void, season_of


# ----------------------------------------------------------------
# 四神
# ----------------------------------------------------------------
def test_four_gods_water():
    """用神=水 → 元金、忌土、仇火。"""
    assert four_gods("水") == {"用": "水", "元": "金", "忌": "土", "仇": "火"}


def test_four_gods_metal():
    """用神=金 → 元土、忌火、仇木（《增删卜易》原例）。"""
    assert four_gods("金") == {"用": "金", "元": "土", "忌": "火", "仇": "木"}


def test_chou_shen_parent_fire():
    """⭐ 父母巳火(火) 对用神妻财水 → 仇神(克金元、生土忌)。

    旧版按六亲判为'闲神'，改为五行基准后正确判为仇神。
    """
    b = cast_board("地泽临", 2, "未", "辛卯", "妻财")
    l1 = b.line(1)
    assert l1.qin == "父母"
    assert l1.zhi == "巳"
    assert l1.wx == "火"
    assert l1.role == "仇神"


# ----------------------------------------------------------------
# 元神忌神有力无力
# ----------------------------------------------------------------
def test_yuanshen_effective_you():
    """子孙酉金=元神，未月旺相、逢日冲暗动 → 有力(能生用)。"""
    b = cast_board("地泽临", 2, "未", "辛卯", "妻财")
    l6 = b.line(6)
    assert l6.role == "元神"
    assert l6.effective is True
    assert "有力" in l6.effective_reason


def test_jishen_ineffective_chou():
    """⭐ 兄弟丑土=忌神，但月破 → 无力(虽忌神却克不到用，'虽动不克')。"""
    b = cast_board("地泽临", 2, "未", "辛卯", "妻财")
    l3 = b.line(3)
    assert l3.role == "忌神"
    assert l3.effective is False
    assert "月破" in l3.effective_reason


# ----------------------------------------------------------------
# 临日建 / 真空
# ----------------------------------------------------------------
def test_world_on_day():
    """世爻卯木临日建(卯日)。"""
    b = cast_board("地泽临", 2, "未", "辛卯", "妻财")
    assert b.line(2).is_on_day is True


def test_true_void_season():
    """真空季节：春土/夏金/秋木/冬火；四季月无真空。"""
    assert is_true_void("土", "寅") is True   # 春土
    assert is_true_void("金", "巳") is True   # 夏金
    assert is_true_void("木", "申") is True   # 秋木
    assert is_true_void("火", "亥") is True   # 冬火
    assert season_of("未") == "季"
    assert is_true_void("金", "未") is False  # 季月无真空


# ----------------------------------------------------------------
# 卦变生克 / 反伏
# ----------------------------------------------------------------
def test_gua_bian_bihe():
    """临变复，同坤宫土 → 变比和(吉)。"""
    b = cast_board("地泽临", 2, "未", "辛卯", "妻财")
    assert "比和" in b.gua_bian


def test_fu_fan_yin_false():
    """临变复，卯化寅，非伏非反。"""
    b = cast_board("地泽临", 2, "未", "辛卯", "妻财")
    assert b.fu_yin is False
    assert b.fan_yin is False


# ----------------------------------------------------------------
# 三合（虚合待用 + 暗动算动）
# ----------------------------------------------------------------
def test_sanhe_xu_he_que_wei():
    """亥卯未木局：卦中缺未(在月)，虚合待填实；动爻仅卯1。"""
    b = cast_board("地泽临", 2, "未", "辛卯", "妻财")
    s = b.sanhe["亥卯未木局"]
    assert "虚合" in s["status"] and "缺未" in s["status"]
    assert s["moving_count"] == 1


def test_sanhe_dark_move_counts_as_moving():
    """⭐ 巳酉丑金局：酉暗动计入动爻数(=1)；三支虽齐但动不足→虚合待用。"""
    b = cast_board("地泽临", 2, "未", "辛卯", "妻财")
    s = b.sanhe["巳酉丑金局"]
    assert s["moving_count"] == 1          # 酉暗动算入
    assert "支齐动不足" in s["status"]
