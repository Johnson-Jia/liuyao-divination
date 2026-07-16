"""黄金用例测试：地泽临 → 地雷复（辛卯日）。

本卦为本项目全程手工精析、并用于验证引擎的 canonical case。
每条断言对应一处关键技法，引擎必须全部命中。
"""

from liuyao import cast_board, find_hexagram
from liuyao.wuxing import xunkong, liuqin


# ----------------------------------------------------------------
# 基础工具
# ----------------------------------------------------------------
def test_find_hexagram_by_full_name_and_alias():
    assert find_hexagram("地泽临")["name"] == "地泽临"
    assert find_hexagram("临")["name"] == "地泽临"


def test_xunkong_xinmao():
    # 辛卯属甲申旬，空午未
    assert xunkong("辛卯") == ("午", "未")


def test_liuqin_kun_palace():
    # 坤宫属土
    assert liuqin("火", "土") == "父母"
    assert liuqin("木", "土") == "官鬼"
    assert liuqin("土", "土") == "兄弟"
    assert liuqin("水", "土") == "妻财"
    assert liuqin("金", "土") == "子孙"


# ----------------------------------------------------------------
# 核心：完整排盘
# ----------------------------------------------------------------
def test_canonical_board_basics():
    b = cast_board("地泽临", 2, "未", "辛卯", "妻财")
    assert b.hexagram == "地泽临"
    assert b.changed_hexagram == "地雷复"
    assert b.palace == "坤"
    assert b.palace_wx == "土"
    assert b.world_pos == 2
    assert b.response_pos == 5
    assert b.xunkong == ("午", "未")
    # 用神妻财在六五
    assert len(b.yongshen_lines) == 1
    assert b.yongshen_lines[0].position == 5


def test_six_spirits_xin_day():
    """辛日白虎起首爻。"""
    b = cast_board("地泽临", 2, "未", "辛卯", "妻财")
    assert b.line(1).shen == "白虎"
    assert b.line(2).shen == "玄武"
    assert b.line(3).shen == "青龙"
    assert b.line(4).shen == "朱雀"
    assert b.line(5).shen == "勾陈"
    assert b.line(6).shen == "螣蛇"


def test_najia_and_liuqin():
    b = cast_board("地泽临", 2, "未", "辛卯", "妻财")
    # 下兑：丁巳(父母)、丁卯(官鬼)、丁丑(兄弟)
    assert (b.line(1).gan, b.line(1).zhi, b.line(1).qin) == ("丁", "巳", "父母")
    assert (b.line(2).gan, b.line(2).zhi, b.line(2).qin) == ("丁", "卯", "官鬼")
    assert (b.line(3).gan, b.line(3).zhi, b.line(3).qin) == ("丁", "丑", "兄弟")
    # 上坤：癸丑(兄弟)、癸亥(妻财)、癸酉(子孙)
    assert (b.line(4).gan, b.line(4).zhi, b.line(4).qin) == ("癸", "丑", "兄弟")
    assert (b.line(5).gan, b.line(5).zhi, b.line(5).qin) == ("癸", "亥", "妻财")
    assert (b.line(6).gan, b.line(6).zhi, b.line(6).qin) == ("癸", "酉", "子孙")


def test_you_is_dark_move_not_day_break():
    """⭐ 关键：子孙酉金未月旺相、逢卯日冲 → 暗动，非日破。"""
    b = cast_board("地泽临", 2, "未", "辛卯", "妻财")
    l6 = b.line(6)
    assert l6.qin == "子孙"
    assert l6.zhi == "酉"
    assert l6.day_strike is True      # 被日冲
    assert l6.prosperous is True      # 旺相
    assert l6.dark_move is True       # 暗动
    assert l6.day_break is False      # 不是日破


def test_chou_month_break():
    """兄弟丑土逢未月 → 月破。"""
    b = cast_board("地泽临", 2, "未", "辛卯", "妻财")
    assert b.line(3).month_break is True
    assert b.line(4).month_break is True
    assert b.line(3).qin == "兄弟"


def test_world_line_retreat_and_grave():
    """⭐ 九二官鬼卯木：世·动·化退神·入月墓·空墓，变庚寅。"""
    b = cast_board("地泽临", 2, "未", "辛卯", "妻财")
    l2 = b.line(2)
    assert l2.qin == "官鬼"
    assert l2.zhi == "卯"
    assert l2.is_world is True
    assert l2.is_moving is True
    assert l2.jin_tui == "化退神"          # 卯→寅
    assert l2.change_gan == "庚"
    assert l2.change_zhi == "寅"
    assert l2.change_qin == "官鬼"
    assert "月墓" in l2.in_grave           # 入未墓
    assert l2.grave_is_void is True        # 未落旬空 → 空墓


def test_no_line_is_void():
    """旬空午未，但卦中六爻无落空者。"""
    b = cast_board("地泽临", 2, "未", "辛卯", "妻财")
    for ln in b.lines:
        assert ln.void is False
    # 用神亥水、世爻卯木皆不空
    assert b.line(5).void is False
    assert b.line(2).void is False


def test_yongshen_roles():
    """相对用神(妻财)的角色：子孙为元神，兄弟为忌神。"""
    b = cast_board("地泽临", 2, "未", "辛卯", "妻财")
    assert b.line(6).role == "元神"   # 子孙(金)生妻财(水)？金生水 → 元神
    assert b.line(3).role == "忌神"   # 兄弟(土)克妻财(水) → 忌神
    assert b.line(5).role == "用神"


def test_yongshen_generates_world():
    """用神亥水生世爻卯木 → 本质旺我（关系判定）。"""
    b = cast_board("地泽临", 2, "未", "辛卯", "妻财")
    ys = b.line(5)   # 妻财亥水
    world = b.line(2)  # 世爻卯木
    # 水(亥)生木(卯)
    from liuyao.wuxing import i_sheng
    assert i_sheng(ys.wx) == world.wx   # 水生木
