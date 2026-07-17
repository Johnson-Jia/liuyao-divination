"""排盘主逻辑：把主卦+动爻+月日 装成完整的结构化卦盘。

cast_board(...) 返回 Board 对象，含六爻的全部信息：
阴阳、纳甲、六亲、六神、世应、动变、空亡、月破、日破、暗动、化进化退、入墓、旺衰。
"""

from .data import (
    BAGUA, BAGUA_NAGAN, BAGUA_NAZHI, DIZHI_WUXING, WUXING_MU,
    JINSHEN, TUISHEN, LIUSHEN_ORDER, LIUSHEN_START, find_hexagram, HEXAGRAMS,
    CHONG,
)

# 三合局：三支 + 化出五行
SANHE_JU = [
    ("申", "子", "辰", "水"),
    ("亥", "卯", "未", "木"),
    ("寅", "午", "戌", "火"),
    ("巳", "酉", "丑", "金"),
]
from .wuxing import (
    liuqin, wuxing_state, shier_changsheng, is_prosperous,
    xunkong, is_void, is_chong, yongshen_role, i_sheng, i_ke,
    is_true_void, four_gods,
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


def _spirit_effective(ln, board):
    """判定元神/忌神是否有力（有效）。返回 (effective, reason)。

    effective: True=有力(能生用/能克用), False=无力(见生不生/虽动不克), None=中和不定。
    依据《增删卜易·用神元神忌神仇神章》有力五条/无用六条/忌神不克七条综合。
    """
    # —— 明显无力（任一命中即无力）——
    if ln.month_break:
        return (False, "月破无力")
    if ln.in_grave:
        return (False, "入墓无力")
    if ln.jin_tui == "化回头克":
        return (False, "化回头克无力")
    if ln.jin_tui == "化退神":
        return (False, "化退神无力")
    if ln.day_break:
        return (False, "日破无力")
    if ln.true_void:
        return (False, "真空无力")
    if ln.state in ("囚", "死") and ln.void:
        return (False, "休囚旬空无力")
    if ln.state in ("囚", "死") and not ln.is_moving and not ln.dark_move:
        return (False, "休囚不动无力")
    if ln.state in ("囚", "死") and ln.stage in ("绝", "墓", "死") and not ln.is_moving:
        return (False, "衰绝无力")

    # —— 有力（任一命中即有力）——
    if ln.is_on_month or ln.is_on_day:
        return (True, "临日月有力")
    if ln.state in ("旺", "相"):
        return (True, "旺相有力")
    if ln.jin_tui in ("化回头生", "化进神"):
        return (True, f"{ln.jin_tui}有力")
    if ln.is_moving or ln.dark_move:
        return (True, "发动有力")

    return (None, "中和")


def _analyze_gua_bian(board):
    """卦变生克：以主卦宫五行 vs 变卦宫五行（《增删卜易·卦变生克墓绝章》）。

    变生/变比和为吉，变克为凶。
    """
    main_wx = board.palace_wx
    ch_name = board.changed_hexagram
    if not ch_name:
        board.gua_bian = "变卦未明"
        return
    ch_rec = find_hexagram(ch_name)
    if not ch_rec:
        board.gua_bian = "变卦未明"
        return
    ch_wx = ch_rec["palace_wx"]
    if ch_wx == main_wx:
        board.gua_bian = "变比和(吉)"
    elif i_sheng(ch_wx) == main_wx:
        board.gua_bian = "变生主(吉)"
    elif i_ke(ch_wx) == main_wx:
        board.gua_bian = "变克主(凶)"
    elif i_sheng(main_wx) == ch_wx:
        board.gua_bian = "主生变(泄)"
    elif i_ke(main_wx) == ch_wx:
        board.gua_bian = "主克变(制)"
    else:
        board.gua_bian = "无"


def _detect_fu_fan_yin(board):
    """伏吟：主卦六爻地支全等于变卦地支(卦变而地支不变)。
    反吟(简化)：所有动爻皆化回头冲(变爻地支冲动爻地支)。"""
    moving = board.moving_lines
    if not moving:
        return
    orig_zhi = [ln.zhi for ln in board.lines]
    changed_zhi = [ln.change_zhi if ln.is_moving else ln.zhi for ln in board.lines]
    if changed_zhi == orig_zhi:
        board.fu_yin = True
    if all(CHONG.get(ln.zhi) == ln.change_zhi for ln in moving):
        board.fan_yin = True


def _detect_sanhe(board):
    """检测三合成局（《增删卜易·三合章》）：明动+暗动皆算动爻。

    三支齐于卦内 + 动爻≥2 → 实成之局；
    三支齐于卦内 + 动爻<2 → 虚合待用(支齐动不足)；
    支不全(有支在月日不在卦) → 虚合(待填实)。
    """
    board_zhi = {ln.zhi for ln in board.lines}
    moving_zhi = {ln.zhi for ln in board.lines if ln.is_moving or ln.dark_move}
    result = {}
    for a, b, c, wx in SANHE_JU:
        tri = (a, b, c)
        in_board_zhi = [z for z in tri if z in board_zhi]
        if not in_board_zhi:
            continue
        moving_count = sum(1 for z in tri if z in moving_zhi)
        if len(in_board_zhi) == 3:
            status = "实成之局" if moving_count >= 2 else "虚合待用(支齐动不足)"
        else:
            missing = [z for z in tri if z not in board_zhi]
            status = f"虚合(缺{''.join(missing)}，待填实)"
        result[f"{a}{b}{c}{wx}局"] = {
            "status": status,
            "moving_count": moving_count,
            "branches_in_board": in_board_zhi,
        }
    board.sanhe = result


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
        self.role = None                    # 相对用神的四神角色(用/元/忌/仇/闲)
        # —— 扩展判定 ——
        self.is_on_day = False              # 临日建(爻支==日支)
        self.is_on_month = False            # 临月建(爻支==月支)
        self.true_void = False              # 真空(旬空且当季死地)
        self.day_strike_moving = None       # 动爻被日冲："动而愈动"/"动而冲散"
        self.effective = None               # 元神/忌神是否有力 True/False/None
        self.effective_reason = ""          # 有力/无力理由

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
        if self.is_on_month:
            tags.append("临月建")
        if self.is_on_day:
            tags.append("临日建")
        if self.true_void:
            tags.append("真空")
        if self.day_strike_moving:
            tags.append(self.day_strike_moving)
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
        self.yongshen_wx = None             # 用神爻五行(四神判定基准)
        # —— 卦级分析 ——
        self.gua_bian = None                # 卦变生克(主宫vs变宫)
        self.fu_yin = False                 # 伏吟
        self.fan_yin = False                # 反吟
        self.sanhe = {}                     # 三合局检测结果

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
        ln.true_void = ln.void and is_true_void(ln.wx, board.month_zhi)
        # 月破
        ln.month_break = is_chong(board.month_zhi, ln.zhi)
        # 日冲
        ln.day_strike = is_chong(board.day_zhi, ln.zhi)
        # 临日月建
        ln.is_on_month = (ln.zhi == board.month_zhi)
        ln.is_on_day = (ln.zhi == board.day_zhi)
        # 暗动 / 日破（静爻被日冲）
        if ln.day_strike and not ln.is_moving:
            if ln.prosperous:
                ln.dark_move = True
            else:
                ln.day_break = True
        # 动爻被日冲（《增删卜易·日辰章》：旺动愈动，衰动冲散）
        if ln.day_strike and ln.is_moving:
            ln.day_strike_moving = "动而愈动" if ln.prosperous else "动而冲散"

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

    # 用神四神角色 + 元神/忌神有力无力（以用神爻五行为基准）
    if yongshen_qin:
        for ln in board.lines:
            if ln.qin == yongshen_qin:
                board.yongshen_lines.append(ln)
        # 用神五行基准：取最旺者，否则取第一个
        if board.yongshen_lines:
            ys_sorted = sorted(
                board.yongshen_lines,
                key=lambda l: (l.is_on_month or l.is_on_day, l.prosperous,
                               l.state in ("旺", "相")),
                reverse=True,
            )
            yongshen_wx = ys_sorted[0].wx
        else:
            yongshen_wx = None
        board.yongshen_wx = yongshen_wx
        for ln in board.lines:
            ln.role = yongshen_role(ln.wx, yongshen_wx) if yongshen_wx else None
            if ln in board.yongshen_lines:
                ln.role = "用神"
            # 元神/忌神判有力无力
            if ln.role in ("元神", "忌神"):
                eff, reason = _spirit_effective(ln, board)
                ln.effective = eff
                ln.effective_reason = reason

    # —— 卦级分析：卦变生克 / 反伏 / 三合 ——
    _analyze_gua_bian(board)
    _detect_fu_fan_yin(board)
    _detect_sanhe(board)

    return board
