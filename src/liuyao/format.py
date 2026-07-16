"""卦盘文本格式化输出。"""

from .board import Board


def yao_name(pos, yin_yang):
    """生成爻位名：阳爻九X，阴爻六X。"""
    nine_six = "九" if yin_yang == "阳" else "六"
    if pos == 1:
        return "初" + nine_six
    if pos == 6:
        return "上" + nine_six
    return nine_six + {2: "二", 3: "三", 4: "四", 5: "五"}[pos]


def format_board(board: Board) -> str:
    """把卦盘格式化为文本表格（上爻在上）。"""
    out = []
    out.append(f"占时：{board.month_zhi}月 {board.day_gz}日（旬空：{'、'.join(board.xunkong)}）")
    out.append(
        f"主卦：{board.hexagram}（{board.palace}宫·{board.palace_wx}）"
        f" → 变卦：{board.changed_hexagram or '（无）'}"
    )
    moving = "、".join(yao_name(l.position, l.yin_yang) for l in board.moving_lines) or "无"
    out.append(f"世在{board.world_pos}爻，应在{board.response_pos}爻；动爻：{moving}")
    if board.yongshen_qin:
        ys = "、".join(f"{yao_name(l.position, l.yin_yang)}({l.gan}{l.zhi})" for l in board.yongshen_lines)
        out.append(f"用神（{board.yongshen_qin}）：{ys}")
    out.append("")

    header = f"{'六神':<4} {'爻位':<5} {'卦象':<5} {'六亲':<4} {'纳甲':<6} {'标注'}"
    out.append(header)
    out.append("-" * 60)

    # 上爻在上
    for pos in range(6, 0, -1):
        ln = board.line(pos)
        symbol = "———" if ln.yin_yang == "阳" else "— —"
        tags = ln.label()
        tag_str = " ".join(tags) if tags else "静"
        change = ""
        if ln.is_moving and ln.change_zhi:
            change = f" → {ln.change_gan}{ln.change_zhi}({ln.change_qin})"
        out.append(
            f"{ln.shen:<4} {yao_name(pos, ln.yin_yang):<5} {symbol:<5} "
            f"{ln.qin:<4} {ln.gan + ln.zhi + ln.wx:<6} {tag_str}{change}"
        )

    out.append("-" * 60)
    return "\n".join(out)
