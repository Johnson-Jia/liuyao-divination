#!/usr/bin/env python3
"""新卦脚手架：自动排盘 + 取卦辞爻辞 + 生成卦例JSON骨架 + 打印推理brief。

分工：
  - 机械层（排盘、卦辞爻辞、JSON结构、关键判定摘要）→ 由本脚本自动完成。
  - 推理层（卦象/动爻讲解、分层解析、断语、应期、发展推演）→ 交给 LLM。
    本脚本会打印一份「排盘摘要 + 推理 prompt」作为 LLM 的输入；
    LLM 据此推理、填好 JSON 的 overview.gua_explanation / sections / verdict / summary，
    再用 generate_report.py 生成报告。

示例：
  python tools/new_case.py --hexagram 雷水解 --moving 3 --month 申 --day 甲子 \\
      --question "占求职能否成" --yongshen 官鬼 --title 求职 -o examples/02-求职.json
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from liuyao import cast_board, format_board
from liuyao.format import yao_name

ROOT = Path(__file__).resolve().parent.parent
ZHOUYI = json.loads(ROOT.joinpath("data", "zhouyi.json").read_text(encoding="utf-8"))

DISCLAIMER = ("六爻为传统文化与占卜术，非科学。断的是「势、象、时机」，非事实预测。"
              "重大决策须以现实理性判断为准，占卜结果仅作参考。")


def build_overview(board):
    """从 zhouyi.json 自动取主卦/变卦卦辞、动爻爻辞；讲解字段留空待 LLM。"""
    def gua_ci(gname, prefix):
        ci = ZHOUYI.get(gname, {}).get("gua_ci", "")
        return {"label": f"{prefix} · {gname}", "text": ci, "note": ""} if ci else None

    items = [gua_ci(board.hexagram, "主卦")]
    if board.changed_hexagram:
        items.append(gua_ci(board.changed_hexagram, "变卦"))
    gua_ci_list = [x for x in items if x]

    yao_ci_list = []
    main_yao = ZHOUYI.get(board.hexagram, {}).get("yao", {})
    for ln in board.moving_lines:
        pos_name = yao_name(ln.position, ln.yin_yang)
        text = main_yao.get(pos_name, "")
        if text:
            yao_ci_list.append({
                "label": f"动爻 · {board.hexagram} {pos_name}",
                "text": f"{pos_name}：{text}",
                "note": "",
            })
    return {"gua_ci": gua_ci_list, "yao_ci": yao_ci_list,
            "gua_explanation": "", "moving_explanation": ""}


def brief(board, output):
    """打印排盘 + 关键判定 + 推理 prompt（LLM 据此发挥）。"""
    L = [format_board(board), "", "===== 关键判定（引擎已算，供推理参考）====="]
    if board.yongshen_wx:
        L.append(f"用神：{board.yongshen_qin}（五行 {board.yongshen_wx}）")
        for ln in board.lines:
            if ln.role and ln.role != "闲神":
                extra = ""
                if ln.role in ("元神", "忌神"):
                    eff = "有力" if ln.effective else ("无力" if ln.effective is False else "中和")
                    extra = f" → {eff}（{ln.effective_reason}）"
                L.append(f"  {yao_name(ln.position, ln.yin_yang)} {ln.qin} {ln.gan}{ln.zhi}：{ln.role}{extra}")
    for ln in board.moving_lines:
        L.append(f"动爻 {yao_name(ln.position, ln.yin_yang)} {ln.gan}{ln.zhi} → "
                 f"{ln.change_gan}{ln.change_zhi}（{ln.jin_tui}）")
    for ln in board.lines:
        if ln.dark_move:
            L.append(f"暗动 {yao_name(ln.position, ln.yin_yang)} {ln.gan}{ln.zhi}（{ln.role}）")
    flags = []
    if board.is_liuhe_gua: flags.append("主卦·六合卦")
    if board.is_liuchong_gua: flags.append("主卦·六冲卦")
    if board.changed_is_liuhe: flags.append("变卦·六合卦")
    if board.changed_is_liuchong: flags.append("变卦·六冲卦")
    if board.fu_yin: flags.append("伏吟")
    if board.fan_yin: flags.append("反吟")
    if board.gua_bian and board.gua_bian != "变卦未明": flags.append(board.gua_bian)
    if flags: L.append("卦级：" + "，".join(flags))
    for k, v in board.sanhe.items():
        L.append(f"三合 {k}：{v['status']}（动爻 {v['moving_count']}）")

    L += ["", "===== 推理 prompt（交 LLM 发挥）=====",
          "请依 SKILL.md 八步流程（取用神→旺衰→世爻→动静暗破→化变合墓→综合定性→应期），"
          "结合上面排盘，推理并填写卦例 JSON：",
          "  overview.gua_explanation  卦象讲解（主→变寓意）",
          "  overview.moving_explanation  动爻讲解（为何是枢纽/病灶）",
          "  sections  分层解析卡片（用神/世爻/元神暗动/三合/六神/空亡/卦意/应期…）",
          "  verdict  完整断语（含发展推演与应期辩证）",
          "  summary  一句话总结",
          "关键辨析：暗动≠日破、贵≠旺、虚合待用、空墓出墓、元忌有力无力、冲墓双向。",
          f"填好后生成报告：python tools/generate_report.py {output} -o outputs/report.html"]
    return "\n".join(L)


def main():
    p = argparse.ArgumentParser(description="新卦脚手架：排盘+卦辞+JSON骨架+推理brief")
    p.add_argument("--hexagram", required=True, help="主卦名（如 雷水解 / 解）")
    p.add_argument("--moving", required=True, help="动爻，如 3 或 2,4")
    p.add_argument("--month", required=True, help="月建（地支如 申，或干支如 庚申）")
    p.add_argument("--day", required=True, help="日干支（两天字符，如 甲子）")
    p.add_argument("--question", required=True, help="所占之事")
    p.add_argument("--yongshen", required=True, help="用神六亲（如 官鬼/妻财）")
    p.add_argument("--year", default="", help="年干支（如 丙午）")
    p.add_argument("--title", default=None, help="卦例标题（默认取问事）")
    p.add_argument("--background", default="", help="背景说明")
    p.add_argument("-o", "--output", default=None, help="输出 JSON 路径")
    args = p.parse_args()

    moving = [int(x.strip()) for x in str(args.moving).split(",") if x.strip()]
    month_zhi = args.month[-1]  # 末字为月支
    board = cast_board(args.hexagram, moving, month_zhi, args.day, args.yongshen)

    output = args.output or str(ROOT / "examples" / "new-case.json")
    output_path = Path(output)
    moving_desc = "".join(yao_name(m, board.line(m).yin_yang) for m in moving)

    case = {
        "id": output_path.stem,
        "title": args.title or args.question[:10],
        "subtitle": f"{board.hexagram} · {moving_desc}动 · 变{board.changed_hexagram}",
        "meta": {
            "year": args.year, "month": args.month, "day": args.day,
            "xunkong": "、".join(board.xunkong),
            "question": args.question, "background": args.background,
        },
        "board": {
            "hexagram": args.hexagram, "moving": moving,
            "month_zhi": month_zhi, "day_gz": args.day, "yongshen": args.yongshen,
        },
        "overview": build_overview(board),
        "sections": [
            {"title": "（待 LLM 填写）分层解析", "subtitle": "", "paragraphs": [""]},
        ],
        "verdict": ["（待 LLM 填写）完整断语"],
        "summary": "（待 LLM 填写）一句话总结",
        "disclaimer": DISCLAIMER,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(case, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"已生成卦例骨架：{output_path}\n")
    print(brief(board, output))


if __name__ == "__main__":
    main()
