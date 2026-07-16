"""排盘主逻辑：把主卦+动爻+月日 装成完整的结构化卦盘。

cast_board(...) 返回 Board 对象，含六爻的全部信息：
阴阳、纳甲、六亲、六神、世应、动变、空亡、月破、日破、暗动、化进化退、入墓、旺衰。
"""

from .data import (
    BAGUA, BAGUA_NAGAN, BAGUA_NAZHI, DIZHI_WUXING, WUXING_MU,
    JINSHEN, TUISHEN, LIUSHEN_ORDER, LIUSHEN_START, find_hexagram, HEXAGRAMS,
)
from .wuxing import (
    liuqin, wuxing_state, shier_changsheng, is_prosperous,
    xunkong, is_void, is_chong, yongshen_role, i_sheng, i_ke,
)


def _yao_to_bagua(yao3):
    """由三爻(自下而上 [初,中,上]，1阳0阴)反查八卦名。"""
    for name, info in BAGUA.items():
        if info["yao"] == yao3:
            return name
    raise ValueError(f"无法识别的卦象: {yao3}")


def _find_changed_hexagram(changed_lower_gua, changed_upper_gua):
    """由变卦的上下卦反查变卦全名（可能查不到组合，返回 None）。"""
    for rec in HEXAGRAMS.values():
        if rec["upper"] == changed_upper_gua and rec["lower"] == changed_lower_gua:
            return rec["name"]
    return None


class Line:
    """单爻信息。"""

    def __init__(self, position):
        self.position = position            # 1..6
        self.name = {1: "初", 2: "二", 3: "三", 4: "四", 5: "五", 6: "上"}[position]
        self.yin_yang = None                # "阳"/"阴"
        self.gan = None                     # 天干
        self.zhi = None                     # 地支
        self.wx = None                      # 爻五行
        self.qin = None                     # 六亲
        self.shen = None                    # 六神
        self.is_world = False
        self.is_response = False
        self.is_moving = False
        # 动爻变爻
        self.change_gan = None
        self.change_zhi = None
        self.change_wx = None
        self.change_qin = None
        # 状态标记
        self.void = False                   # 空亡
        self.month_break = False            # 月破
        self.day_strike = False             # 被日冲
        self.dark_move = False              # 暗动
        self.day_break = False              # 日破
        self.prosperous = False             # 旺相
        self.jin_tui = None                 # "化进神"/"化退神"/"化回头生"/"化回头克"/"化比和"
        self.in_grave = []                  # 入墓原因列表
        self.grave_is_void = False          # 是否入空墓
        self.stage = None                   # 十二长生阶段
        self.state = None                   # 旺相休囚死
        self.role = None                    # 相对用神的角色

    def label(self):
        """组合标注，用于展示。"""
        tags = []
        if self.is_world:
            tags.append("世")
        if self.is_response:
            tags.append("应")
        if self.is_moving:
            tags.append("动")
        if self.void:
            tags.append("空")
        if self.month_break:
            tags.append("月破")
        if self.dark_move:
            tags.append("暗动")
        if self.day_break:
            tags.append("日破")
        if self.jin_tui:
            tags.append(self.jin_tui)
        for g in self.in_grave:
            tags.append(g)
        if self.grave_is_void:
            tags.append("空墓")
        return tags


class Board:
    """完整卦盘。"""

    def __init__(self):
        self.hexagram = None
        self.changed_hexagram = None
        self.palace = None
        self.palace_wx = None
        self.world_pos = None
        self.response_pos = None
        self.month_zhi = None
        self.month_wx = None
        self.day_gz = None
        self.day_gan = None
        self.day_zhi = None
        self.day_wx = None
        self.xunkong = None                 # (支,支)
        self.lines = [Line(i) for i in range(1, 7)]
        self.yongshen_qin = None
        self.yongshen_lines = []

    def line(self, pos):
        return self.lines[pos - 1]

    @property
    def moving_lines(self):
        return [l for l in self.lines if l.is_moving]


def cast_board(hexagram, moving, month_zhi, day_gz, yongshen_qin=None):
    """排盘。

    Args:
        hexagram: 卦名（全名"地泽临"或单字"临"）。
        moving: 动爻位置，int 或 list[int]（1..6）。
        month_zhi: 月建地支，如 "未"。
        day_gz: 日干支，如 "辛卯"（完整两天字符）。
        yongshen_qin: 可选，用神六亲名（"妻财"等），用于标注各爻角色。

    Returns:
        Board 对象。
    """
    rec = find_hexagram(hexagram)
    if rec is None:
        raise ValueError(f"未找到卦: {hexagram}")

    if isinstance(moving, int):
        moving = [moving]
    moving_set = set(moving)

    board = Board()
    board.hexagram = rec["name"]
    board.palace = rec["palace"]
    board.palace_wx = rec["palace_wx"]
    board.world_pos = rec["world"]
    board.response_pos = ((board.world_pos - 1 + 3) % 6) + 1

    board.month_zhi = month_zhi
    board.month_wx = DIZHI_WUXING[month_zhi]
    board.day_gz = day_gz
    board.day_gan = day_gz[0]
    board.day_zhi = day_gz[1]
    board.day_wx = DIZHI_WUXING[board.day_zhi]
    board.xunkong = xunkong(day_gz)
    board.yongshen_qin = yongshen_qin

    upper, lower = rec["upper"], rec["lower"]
    lower_yao = BAGUA[lower]["yao"]
    upper_yao = BAGUA[upper]["yao"]
    six_yao = lower_yao + upper_yao  # 初..上

    # 变卦（动爻阴阳翻转）
    changed_yao = [(1 - y if (i + 1) in moving_set else y) for i, y in enumerate(six_yao)]
    changed_lower_gua = _yao_to_bagua(changed_yao[0:3])
    changed_upper_gua = _yao_to_bagua(changed_yao[3:6])
    board.changed_hexagram = _find_changed_hexagram(changed_lower_gua, changed_upper_gua)

    # 六神起例
    start_shen = LIUSHEN_START[board.day_gan]
    start_idx = LIUSHEN_ORDER.index(start_shen)

    # 装每爻
    lower_gan, upper_gan = BAGUA_NAGAN[lower][0], BAGUA_NAGAN[upper][1]
    lower_zhi = BAGUA_NAZHI[lower][:3]
    upper_zhi = BAGUA_NAZHI[upper][3:]

    for pos in range(1, 7):
        ln = board.line(pos)
        idx = pos - 1
        ln.yin_yang = "阳" if six_yao[idx] == 1 else "阴"
        if pos <= 3:
            ln.gan = lower_gan
            ln.zhi = lower_zhi[idx]
        else:
            ln.gan = upper_gan
            ln.zhi = upper_zhi[idx - 3]
        ln.wx = DIZHI_WUXING[ln.zhi]
        ln.qin = liuqin(ln.wx, board.palace_wx)
        ln.shen = LIUSHEN_ORDER[(start_idx + idx) % 6]
        ln.is_world = (pos == board.world_pos)
        ln.is_response = (pos == board.response_pos)
        ln.is_moving = pos in moving_set

        # 旺衰
        ln.state = wuxing_state(ln.wx, board.month_wx)
        ln.stage = shier_changsheng(ln.wx, ln.zhi)
        ln.prosperous = is_prosperous(ln.wx, ln.zhi, board.month_zhi, board.day_zhi)

        # 空亡
        ln.void = is_void(ln.zhi, day_gz)
        # 月破
        ln.month_break = is_chong(board.month_zhi, ln.zhi)
        # 日冲
        ln.day_strike = is_chong(board.day_zhi, ln.zhi)
        # 暗动 / 日破（仅静爻被日冲）
        if ln.day_strike and not ln.is_moving:
            if ln.prosperous:
                ln.dark_move = True
            else:
                ln.day_break = True

    # 动爻变爻
    ch_lower_gan, ch_upper_gan = BAGUA_NAGAN[changed_lower_gua][0], BAGUA_NAGAN[changed_upper_gua][1]
    ch_lower_zhi = BAGUA_NAZHI[changed_lower_gua][:3]
    ch_upper_zhi = BAGUA_NAZHI[changed_upper_gua][3:]

    for ln in board.moving_lines:
        p = ln.position
        if p <= 3:
            ln.change_gan = ch_lower_gan
            ln.change_zhi = ch_lower_zhi[p - 1]
        else:
            ln.change_gan = ch_upper_gan
            ln.change_zhi = ch_upper_zhi[p - 4]
        ln.change_wx = DIZHI_WUXING[ln.change_zhi]
        ln.change_qin = liuqin(ln.change_wx, board.palace_wx)

        # 化进退 / 回头生克
        if ln.wx == ln.change_wx:
            if JINSHEN.get(ln.zhi) == ln.change_zhi:
                ln.jin_tui = "化进神"
            elif TUISHEN.get(ln.zhi) == ln.change_zhi:
                ln.jin_tui = "化退神"
            else:
                ln.jin_tui = "化比和"
        else:
            if i_sheng(ln.change_wx) == ln.wx:
                ln.jin_tui = "化回头生"
            elif i_ke(ln.change_wx) == ln.wx:
                ln.jin_tui = "化回头克"
            else:
                ln.jin_tui = "化他"

    # 入墓
    for ln in board.lines:
        mu = WUXING_MU[ln.wx]
        reasons = []
        if board.month_zhi == mu:
            reasons.append("月墓")
        if board.day_zhi == mu:
            reasons.append("日墓")
        for other in board.lines:
            if other.is_moving and other.zhi == mu and other.position != ln.position:
                reasons.append(f"动爻{other.name}墓")
        if ln.is_moving and ln.change_zhi == mu:
            reasons.append("化墓")
        ln.in_grave = reasons
        # 空墓：入墓 且 墓库地支落空亡
        if reasons and mu in board.xunkong:
            ln.grave_is_void = True

    # 用神角色
    if yongshen_qin:
        for ln in board.lines:
            if ln.qin == yongshen_qin:
                board.yongshen_lines.append(ln)
            ln.role = yongshen_role(ln.qin, yongshen_qin)
        # 用神本身标记 role="用神"
        for ln in board.yongshen_lines:
            ln.role = "用神"

    return board
