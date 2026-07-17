#!/usr/bin/env python3
"""六爻 HTML 报告生成器。

读取一个结构化的卦例 JSON，调用排盘引擎排盘，生成一份古典卷宗风格的 HTML 报告。

示例：
    python tools/generate_report.py examples/01-是否旺己-地泽临之复.json -o outputs/report.html
"""

import argparse
import html
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from liuyao import cast_board
from liuyao.format import yao_name


CSS = """
:root{
  --paper:#f4ead5; --paper-light:#faf4e4;
  --ink:#2b2218; --ink-soft:#4a3f30; --ink-fade:#6b5d48;
  --vermilion:#9e2b25; --vermilion-bright:#c0392b;
  --gold:#a87c2a; --gold-bright:#c9a44c;
  --jade:#4f6f57; --border:#d4c4a0; --border-strong:#bda672;
}
*{box-sizing:border-box;margin:0;padding:0}
body{
  font-family:'Noto Serif SC','Songti SC','SimSun',serif;
  background:radial-gradient(circle at 20% 10%,rgba(168,124,42,.06),transparent 40%),
             radial-gradient(circle at 80% 90%,rgba(158,43,37,.05),transparent 45%),var(--paper);
  color:var(--ink);line-height:1.9;font-size:17.5px;padding:40px 20px 60px;
}
.wrap{max-width:920px;margin:0 auto}
.header{text-align:center;padding:50px 30px 40px;background:linear-gradient(180deg,var(--paper-light),var(--paper));
  border:1px solid var(--border);border-radius:6px;position:relative;overflow:hidden;box-shadow:0 4px 24px rgba(60,40,10,.08)}
.seal{position:absolute;top:24px;right:30px;width:62px;height:62px;background:var(--vermilion);color:#fff7e8;
  font-family:'KaiTi',serif;font-size:30px;display:flex;align-items:center;justify-content:center;border-radius:8px;
  transform:rotate(8deg);box-shadow:0 2px 8px rgba(158,43,37,.4);line-height:1}
.seal::after{content:"";position:absolute;inset:4px;border:1.5px solid rgba(255,247,232,.5);border-radius:5px}
.title-sub{font-size:17px;color:var(--vermilion);letter-spacing:4px;margin-bottom:8px;font-weight:600}
.title-main{font-family:'KaiTi',serif;font-size:42px;color:var(--ink);letter-spacing:6px;margin-bottom:6px}
.title-main.red{color:var(--vermilion)}
.divider{display:flex;align-items:center;justify-content:center;gap:14px;margin:18px 0;color:var(--gold)}
.divider::before,.divider::after{content:"";height:1px;width:90px;background:linear-gradient(90deg,transparent,var(--gold),transparent)}
.info-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:14px;margin:24px 0}
.info-card{background:var(--paper-light);border:1px solid var(--border);border-left:3px solid var(--gold);border-radius:4px;padding:16px 18px}
.info-card .label{font-size:13.5px;color:var(--ink-fade);letter-spacing:2px;margin-bottom:6px}
.info-card .value{font-size:17.5px;color:var(--ink);font-weight:600}
.info-card .value .accent{color:var(--vermilion)}
.section{margin:42px 0 20px}
.section-title{display:flex;align-items:center;gap:14px;margin-bottom:20px}
.section-title .num{width:34px;height:34px;background:var(--ink);color:var(--paper-light);font-family:'KaiTi',serif;
  font-size:18px;display:flex;align-items:center;justify-content:center;border-radius:50%;flex-shrink:0}
.section-title h2{font-family:'KaiTi',serif;font-size:26px;color:var(--ink);letter-spacing:3px;font-weight:400}
.section-title .line{flex:1;height:1px;background:linear-gradient(90deg,var(--border-strong),transparent)}
.hex-display{display:flex;align-items:center;justify-content:center;gap:24px;padding:30px 16px;
  background:var(--paper-light);border:1px solid var(--border);border-radius:6px;margin-bottom:24px;overflow-x:auto}
.hex-block{text-align:center}
.hex-mid{display:flex;flex-direction:column;align-items:center;gap:8px;flex-shrink:0;max-width:100px}
.hex-mid .gua-tags{margin:0;text-align:center}
.hex-mid .gua-tags .tag{display:block;margin:3px 0;font-size:11px;letter-spacing:1px}
.gua-name{font-family:'KaiTi',serif;font-size:26px;color:var(--ink);margin-bottom:6px;letter-spacing:2px}
.gua-tag{font-size:13.5px;color:var(--ink-fade);margin-bottom:16px;letter-spacing:2px}
.hex-lines{display:flex;flex-direction:column;gap:9px;align-items:center}
.yao{display:flex;align-items:center;gap:7px;width:368px;min-height:28px}
.yao .yleft{font-size:13px;color:var(--ink-soft);width:80px;text-align:right;flex-shrink:0;white-space:nowrap}
.yao .pos{font-size:13px;color:var(--ink-fade);width:28px;text-align:center;flex-shrink:0}
.yao .bars{width:64px;display:flex;justify-content:space-between;align-items:center;height:10px;flex-shrink:0}
.yao .bars .b{height:10px;background:var(--ink);border-radius:1px}
.yao .bars.solid .b{width:64px}
.yao .bars.split .b{width:30px}
.yao .yright{font-size:14px;color:var(--ink);width:44px;flex-shrink:0;white-space:nowrap;font-weight:600}
.yao .ytags{width:124px;display:flex;flex-wrap:wrap;gap:2px;align-items:center}
.yao .ytag{font-size:10.5px;padding:1px 5px;border-radius:2px;background:rgba(158,43,37,.1);color:var(--vermilion);white-space:nowrap;line-height:1.4}
.yao.moving .b{background:var(--vermilion);box-shadow:0 0 8px rgba(158,43,37,.4)}
.yao.moving .pos{color:var(--vermilion);font-weight:600}
.arrow{font-size:34px;color:var(--gold)}
.board{background:var(--paper-light);border:1px solid var(--border-strong);border-radius:6px;overflow:hidden;box-shadow:0 2px 12px rgba(60,40,10,.06)}
.board table{width:100%;border-collapse:collapse;font-size:14.5px}
.board th{background:var(--ink);color:var(--paper-light);padding:12px 8px;font-weight:600;letter-spacing:2px;font-size:13px}
.board td{padding:13px 8px;text-align:center;border-bottom:1px solid var(--border)}
.board tr:last-child td{border-bottom:none}
.board tr:nth-child(even) td{background:rgba(168,124,42,.04)}
.board tr.moving td{background:rgba(158,43,37,.07)}
.board .ys{color:var(--vermilion);font-weight:700}
.board .sy{font-weight:700}
.tag{display:inline-block;font-size:11.5px;padding:2px 7px;border-radius:3px;margin:1px;letter-spacing:1px}
.tag-red{background:rgba(158,43,37,.12);color:var(--vermilion)}
.tag-jade{background:rgba(79,111,87,.12);color:var(--jade)}
.tag-gold{background:rgba(168,124,42,.15);color:var(--gold)}
.params{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:10px;margin:20px 0}
.param{background:var(--paper-light);border:1px solid var(--border);border-radius:4px;padding:12px 14px;text-align:center}
.param .k{font-size:12.5px;color:var(--ink-fade);letter-spacing:2px;margin-bottom:4px}
.param .v{font-size:15.5px;color:var(--ink);font-weight:600}
.param .v.red{color:var(--vermilion)}
.card{background:var(--paper-light);border:1px solid var(--border);border-radius:6px;padding:22px 26px;margin-bottom:16px}
.card .ct{font-family:'KaiTi',serif;font-size:22.5px;color:var(--ink);margin-bottom:4px;letter-spacing:2px}
.card .cs{font-size:14.5px;color:var(--vermilion);margin-bottom:12px;letter-spacing:1px;font-weight:600}
.card p{color:var(--ink-soft);margin-bottom:10px;text-align:justify}
.card p:last-child{margin-bottom:0}
.ci-block{background:var(--paper-light);border:1px solid var(--border);border-radius:6px;padding:16px 20px;margin-bottom:14px}
.ci-cap{font-family:'KaiTi',serif;font-size:17.5px;color:var(--vermilion);letter-spacing:6px;margin-bottom:12px;text-align:center}
.ci-item{padding:10px 0;border-bottom:1px dashed var(--border)}
.ci-item:last-child{border-bottom:none}
.ci-label{font-size:14.5px;color:var(--ink-fade);margin-bottom:5px;letter-spacing:1px}
.ci-text{font-family:'KaiTi','STKaiti',serif;font-size:18.5px;color:var(--ink);margin-bottom:6px;letter-spacing:1px;line-height:1.7}
.ci-note{font-size:15px;color:var(--ink-soft);line-height:1.85}
.gua-tags{text-align:center;margin:-6px 0 20px}
.gua-tags .tag{font-size:13px;padding:3px 10px}
.mini-table{width:100%;border-collapse:collapse;margin:10px 0;font-size:14px}
.mini-table td{padding:8px 10px;border-bottom:1px dashed var(--border);vertical-align:top}
.mini-table td:first-child{color:var(--vermilion);font-weight:600;white-space:nowrap}
.verdict{background:linear-gradient(180deg,#3a2f22,#2b2218);border:2px solid var(--gold);border-radius:8px;
  padding:40px 38px;margin:30px 0;color:#f0e6d0;box-shadow:0 8px 30px rgba(40,30,15,.25)}
.verdict-title{text-align:center;font-family:'KaiTi',serif;font-size:30px;color:var(--gold-bright);letter-spacing:10px;margin-bottom:28px}
.verdict-body{font-size:17.5px;line-height:2.1;color:#e8dcc2;text-indent:2em;text-align:justify}
.verdict-body p{margin-bottom:14px}
.verdict-body p:last-child{margin-bottom:0}
.summary{background:linear-gradient(135deg,rgba(158,43,37,.06),rgba(168,124,42,.06));border:1.5px solid var(--vermilion);
  border-radius:6px;padding:28px 30px;margin:30px 0}
.summary h3{font-family:'KaiTi',serif;font-size:24px;color:var(--vermilion);margin-bottom:12px;letter-spacing:2px}
.summary p{color:var(--ink);font-size:17.5px;line-height:2}
.notice{text-align:center;font-size:14.5px;color:var(--ink-fade);border-top:1px dashed var(--border);padding-top:22px;margin-top:30px;line-height:1.9}
.footer{text-align:center;margin-top:30px;font-size:12px;color:var(--ink-fade);letter-spacing:2px}
.footer .orn{color:var(--gold);margin:0 8px}
@keyframes fadeUp{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:none}}
.header,.hex-display,.board,.card,.verdict,.summary{animation:fadeUp .7s ease both}
@media(max-width:600px){body{padding:20px 12px 40px}.title-main{font-size:32px}.board{overflow-x:auto}.board table{min-width:560px}}
"""


def esc(s):
    return html.escape(str(s))


def render_yao_bars(yin_yang, moving=False):
    cls = "bars solid" if yin_yang == "阳" else "bars split"
    yao_cls = "yao moving" if moving else "yao"
    if yin_yang == "阳":
        bars = '<div class="bars solid"><span class="b"></span></div>'
    else:
        bars = '<div class="bars split"><span class="b"></span><span class="b"></span></div>'
    return f'<div class="{yao_cls}">{{pos}}{bars}</div>'


def render_hex_diagram(board):
    """主卦 → 变卦 大图。每爻含 爻位/阴阳爻/六神·六亲·纳甲，卦名附六合/六冲标注。

    主卦、变卦同爻左右并排，一行即可横向对比变化。
    """
    def suffix(is_he, is_chong):
        if is_he:
            return "（六合卦）"
        if is_chong:
            return "（六冲卦）"
        return ""

    def block(title, tag, yin_yangs, moving_set, info_of):
        rows = []
        for pos in range(6, 0, -1):
            yy = yin_yangs[pos - 1]
            mv = pos in moving_set
            pos_label = yao_name(pos, yy)
            bars = ('<div class="bars solid"><span class="b"></span></div>' if yy == "阳"
                    else '<div class="bars split"><span class="b"></span><span class="b"></span></div>')
            yao_cls = "yao moving" if mv else "yao"
            info = info_of(pos)
            left_html = f'<span class="yleft">{esc(info["shen"])}·{esc(info["qin"])}</span>'
            right_html = f'<span class="yright">{esc(info["gan"])}{esc(info["zhi"])}</span>'
            tag_html = "".join(f'<span class="ytag">{esc(t)}</span>' for t in info.get("tags", []))
            rows.append(
                f'<div class="{yao_cls}">{left_html}<span class="pos">{esc(pos_label)}</span>'
                f'{bars}{right_html}<span class="ytags">{tag_html}</span></div>'
            )
        return (f'<div class="hex-block"><div class="gua-name">{esc(title)}</div>'
                f'<div class="gua-tag">{esc(tag)}</div>'
                f'<div class="hex-lines">{"".join(rows)}</div></div>')

    yin_yangs = [ln.yin_yang for ln in board.lines]
    moving_set = {ln.position for ln in board.moving_lines}
    changed_yy = [("阴" if yy == "阳" else "阳") if (i + 1) in moving_set else yy
                  for i, yy in enumerate(yin_yangs)]

    def main_info(pos):
        ln = board.line(pos)
        return {"shen": ln.shen, "qin": ln.qin, "gan": ln.gan, "zhi": ln.zhi,
                "tags": ln.label()}

    ch = board.changed_line_info()
    def changed_info(pos):
        c = ch[pos - 1]
        m = board.line(pos)
        tags = [m.jin_tui] if (m.is_moving and m.jin_tui) else []
        return {"shen": c["shen"], "qin": c["qin"], "gan": c["gan"], "zhi": c["zhi"],
                "tags": tags}

    left_title = board.hexagram + suffix(board.is_liuhe_gua, board.is_liuchong_gua)
    right_title = (board.changed_hexagram or "變卦") + suffix(board.changed_is_liuhe, board.changed_is_liuchong)
    left = block(left_title, "主卦", yin_yangs, moving_set, main_info)
    right = block(right_title, "變卦", changed_yy, moving_set, changed_info)
    mid = f'<div class="hex-mid"><div class="arrow">➜</div>{render_gua_tags(board)}</div>'
    return f'<div class="hex-display">{left}{mid}{right}</div>'


def render_board_table(board):
    rows = []
    for pos in range(6, 0, -1):
        ln = board.line(pos)
        symbol = "———" if ln.yin_yang == "阳" else "— —"
        tags = []
        cls = []
        if ln.is_world:
            tags.append(("世", "tag-red"))
        if ln.is_response:
            tags.append(("应", "tag-red"))
        if ln.is_moving:
            tags.append(("动", "tag-red"))
        if ln.void:
            tags.append(("空", "tag-gold"))
        if ln.month_break:
            tags.append(("月破", "tag-gold"))
        if ln.dark_move:
            tags.append(("暗动·生财" if ln.role == "元神" else "暗动", "tag-jade"))
        if ln.day_break:
            tags.append(("日破", "tag-gold"))
        if ln.jin_tui:
            tags.append((ln.jin_tui, "tag-red"))
        for g in ln.in_grave:
            tags.append((g, "tag-red"))
        if ln.grave_is_void:
            tags.append(("空墓", "tag-red"))
        tag_html = "".join(f'<span class="tag {c}">{esc(t)}</span>' for t, c in tags) or "静"
        change = ""
        if ln.is_moving and ln.change_zhi:
            change = f"{ln.change_gan}{ln.change_zhi}({ln.change_qin})"
        qin_cls = "ys" if ln.role == "用神" else ("sy" if ln.is_world else "")
        tr_cls = ' class="moving"' if ln.is_moving else ""
        rows.append(
            f'<tr{tr_cls}><td>{esc(ln.shen)}</td><td>{esc(yao_name(pos, ln.yin_yang))}</td>'
            f'<td>{esc(symbol)}</td><td class="{qin_cls}">{esc(ln.qin)}</td>'
            f'<td class="{qin_cls}">{esc(ln.gan)}{esc(ln.zhi)}{esc(ln.wx)}</td>'
            f'<td>{tag_html}</td><td>{esc(change)}</td></tr>'
        )
    head = ("<tr><th>六神</th><th>爻位</th><th>卦象</th><th>六亲</th><th>纳甲</th>"
            "<th>标注</th><th>变卦</th></tr>")
    return f'<div class="board"><table>{head}{"".join(rows)}</table></div>'


def render_params(board):
    def p(k, v, red=False):
        c = "red" if red else ""
        return f'<div class="param"><div class="k">{esc(k)}</div><div class="v {c}">{esc(v)}</div></div>'
    moving = "、".join(yao_name(l.position, l.yin_yang) for l in board.moving_lines) or "无"
    sanhe_hint = ""
    items = [
        p("月建", f"{board.month_zhi}·{board.month_wx}"),
        p("日辰", f"{board.day_gz}（{board.day_wx}）"),
        p("空亡", "、".join(board.xunkong)),
        p("动爻", moving, red=True),
        p("世/应", f"世{board.world_pos}·应{board.response_pos}"),
        p("用神", board.yongshen_qin or "—", red=bool(board.yongshen_qin)),
    ]
    return f'<div class="params">{"".join(items)}</div>'


def render_gua_tags(board):
    """卦级特征标签条（附在卦象图下）：六合卦/六冲卦/反伏/卦变生克。"""
    tags = []
    if board.is_liuhe_gua:
        tags.append(("主卦·六合卦", "tag-jade"))
    if board.is_liuchong_gua:
        tags.append(("主卦·六冲卦", "tag-red"))
    if board.changed_is_liuhe:
        tags.append(("变卦·六合卦", "tag-jade"))
    if board.changed_is_liuchong:
        tags.append(("变卦·六冲卦", "tag-red"))
    if board.fu_yin:
        tags.append(("伏吟", "tag-gold"))
    if board.fan_yin:
        tags.append(("反吟", "tag-gold"))
    if board.gua_bian and board.gua_bian != "变卦未明":
        tags.append((board.gua_bian, "tag-gold"))
    if not tags:
        return ""
    html = "".join(f'<span class="tag {c}">{esc(t)}</span>' for t, c in tags)
    return f'<div class="gua-tags">{html}</div>'


def render_overview(overview):
    """渲染卦象总览的卦辞/爻辞 + 卦象/动爻 LLM 推演讲解。"""
    if not overview:
        return ""
    out = []

    def ci_items(items):
        return "".join(
            f'<div class="ci-item"><div class="ci-label">{esc(c["label"])}</div>'
            f'<div class="ci-text">{esc(c["text"])}</div>'
            f'<div class="ci-note">{esc(c["note"])}</div></div>'
            for c in items
        )

    if overview.get("gua_ci"):
        out.append(f'<div class="ci-block"><div class="ci-cap">卦　辭</div>'
                   f'{ci_items(overview["gua_ci"])}</div>')
    if overview.get("yao_ci"):
        out.append(f'<div class="ci-block"><div class="ci-cap">動爻爻辭</div>'
                   f'{ci_items(overview["yao_ci"])}</div>')
    if overview.get("gua_explanation"):
        out.append(f'<div class="card"><div class="ct">卦象推演</div>'
                   f'<p>{esc(overview["gua_explanation"])}</p></div>')
    if overview.get("moving_explanation"):
        out.append(f'<div class="card"><div class="ct">動爻推演</div>'
                   f'<p>{esc(overview["moving_explanation"])}</p></div>')
    return "".join(out)


def render_sections(sections):
    out = []
    for sec in sections:
        paras = "".join(f"<p>{esc(pa)}</p>" for pa in sec.get("paragraphs", []))
        table = ""
        if "table" in sec:
            t = sec["table"]
            head = "".join(f"<th>{esc(h)}</th>" for h in t["headers"])
            body = ""
            for r in t["rows"]:
                body += "<tr>" + "".join(f"<td>{esc(c)}</td>" for c in r) + "</tr>"
            table = f'<table class="mini-table"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>'
        after = "".join(f"<p>{esc(pa)}</p>" for pa in sec.get("paragraphs_after_table", []))
        out.append(
            f'<div class="card"><div class="ct">{esc(sec["title"])}</div>'
            f'<div class="cs">{esc(sec.get("subtitle", ""))}</div>{paras}{table}{after}</div>'
        )
    return "".join(out)


def render_verdict(verdict):
    paras = "".join(f"<p>{esc(p)}</p>" for p in verdict)
    return f'<div class="verdict"><div class="verdict-title">斷　曰</div><div class="verdict-body">{paras}</div></div>'


def generate_html(case, board):
    m = case["meta"]
    info = [
        ("占时", f'{m["year"]}年 · {m["month"]}月 · <span class="accent">{m["day"]}日</span>'),
        ("旬空", f'<span class="accent">{m["xunkong"]}</span>'),
        ("问事", m["question"]),
        ("用神", f'{board.yongshen_qin or "—"} <span class="accent">({board.line(5).gan}{board.line(5).zhi})</span>'
                 if board.yongshen_qin else "—"),
    ]
    info_cards = "".join(
        f'<div class="info-card"><div class="label">{esc(k)}</div><div class="value">{v}</div></div>'
        for k, v in info
    )

    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{esc(case['title'])} · {esc(case['subtitle'])}</title>
<style>{CSS}</style></head><body><div class="wrap">

<header class="header">
  <div class="seal">卦</div>
  <div class="title-sub">六爻卦象解析</div>
  <h1 class="title-main">{esc(case['subtitle'].split(' · ')[0])}</h1>
  <div class="divider"><span>✦</span><span>九二爻動 · 變</span><span>✦</span></div>
  <h1 class="title-main red">{esc(board.changed_hexagram or '變卦')}</h1>
</header>

<div class="info-grid">{info_cards}</div>

<div class="section">
  <div class="section-title"><div class="num">壹</div><h2>卦象總覽</h2><div class="line"></div></div>
  {render_hex_diagram(board)}
  {render_params(board)}
  {render_overview(case.get("overview"))}
</div>

<div class="section">
  <div class="section-title"><div class="num">貳</div><h2>分層解析</h2><div class="line"></div></div>
  {render_sections(case['sections'])}
</div>

<div class="section">
  <div class="section-title"><div class="num">叁</div><h2>整體推演 · 斷語</h2><div class="line"></div></div>
  {render_verdict(case['verdict'])}
</div>

<div class="summary">
  <h3>一語總括</h3>
  <p>{esc(case['summary'])}</p>
</div>

<div class="notice">※ 理性提醒 ※<br>{esc(case.get('disclaimer', ''))}</div>

<div class="footer">六爻卦象解析報告<span class="orn">✦</span>{esc(case['subtitle'])}<span class="orn">✦</span>僅供參考</div>

</div></body></html>"""


def main():
    p = argparse.ArgumentParser(description="六爻 HTML 报告生成器")
    p.add_argument("case_json", help="卦例 JSON 路径")
    p.add_argument("-o", "--output", default="outputs/report.html", help="输出 HTML 路径")
    args = p.parse_args()

    case = json.loads(Path(args.case_json).read_text(encoding="utf-8"))
    bpar = case["board"]
    board = cast_board(
        bpar["hexagram"], bpar["moving"], bpar["month_zhi"], bpar["day_gz"],
        bpar.get("yongshen"),
    )

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(generate_html(case, board), encoding="utf-8")
    print(f"已生成报告：{out_path}（主卦 {board.hexagram} → {board.changed_hexagram}）")


if __name__ == "__main__":
    main()
