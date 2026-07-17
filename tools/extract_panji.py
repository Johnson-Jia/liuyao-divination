#!/usr/bin/env python3
"""从《易经六十四卦》整理稿提炼每卦的「一句话卦象 + 判曰」，生成判辞速查文档。

源稿由仓库作者整理（含每卦排盘、卦象、判曰、人间道等），本脚本只提取对六爻
断法直接有用的「卦象概括 + 断辞歌诀」部分，按八宫分组输出。

用法（在项目根目录）：
    python tools/extract_panji.py ../易经六十四卦.md
"""

import re
import sys
from pathlib import Path


def extract(src_path):
    text = Path(src_path).read_text(encoding="utf-8")
    palaces = []           # [(宫名, [(卦名, 注记, 卦象句, 判曰)])]
    cur_palace = None
    cur_guas = []
    cur_name = None
    cur_attr = None
    cur_block = []

    def finalize_gua():
        nonlocal cur_name, cur_attr, cur_block
        if cur_name and cur_palace:
            xiang = panji = ""
            for i, ln in enumerate(cur_block):
                if ln.startswith("判曰："):
                    panji = ln[len("判曰："):].strip()
                    j = i - 1
                    while j >= 0 and not cur_block[j].strip():
                        j -= 1
                    if j >= 0:
                        xiang = cur_block[j].strip()
                    break
            cur_guas.append((cur_name, cur_attr or "", xiang, panji))
        cur_name = None
        cur_attr = None
        cur_block = []

    for ln in text.split("\n"):
        pm = re.match(r"# (.+宫八卦.*)", ln)
        if pm:
            finalize_gua()
            if cur_palace and cur_guas:
                palaces.append((cur_palace, cur_guas))
                cur_guas = []
            cur_palace = pm.group(1).strip()
            continue
        gm = re.match(r"## 《(.+?)》(.*)", ln)
        if gm:
            finalize_gua()
            cur_name = gm.group(1).strip()
            cur_attr = gm.group(2).strip()
            cur_block = []
            continue
        if cur_name is not None:
            cur_block.append(ln)
    finalize_gua()
    if cur_palace and cur_guas:
        palaces.append((cur_palace, cur_guas))
    return palaces


def to_markdown(palaces):
    out = [
        "# 11 · 六十四卦判辞（卦象与断辞速查）",
        "",
        "断卦时，主卦、变卦的**卦意**可参此表——每卦列「一句话卦象」与「判曰（传统断辞歌诀）」，"
        "用于快速把握卦的总体意象与吉凶倾向。",
        "",
        "> 提炼自《易经六十四卦》整理稿（判辞为传统断卦歌诀）。**六爻纳甲断法以用神旺衰生克为本，"
        "卦辞判辞为意象参考**，二者互为参证，不可只凭卦辞判辞定吉凶。",
        "",
        "> 注：各卦注记（纯卦／一世／…、六冲／六合）沿用源稿，偶有笔误；"
        "**世爻位置与六冲六合一律以引擎排盘（`paipan.py`）为准**。",
        "",
    ]
    total = 0
    for palace, guas in palaces:
        out.append(f"## {palace}")
        out.append("")
        for name, attr, xiang, panji in guas:
            total += 1
            out.append(f"### {name}")
            if attr:
                out.append(f"> {attr}")
                out.append("")
            out.append(f"- **卦象**：{xiang}")
            out.append(f"- **判曰**：{panji}")
            out.append("")
    out.insert(2, f"（共 {total} 卦，按八宫分组。）")
    return "\n".join(out)


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "../易经六十四卦.md"
    palaces = extract(src)
    md = to_markdown(palaces)
    out = Path("references/11-六十四卦判辞.md")
    out.write_text(md, encoding="utf-8")
    n = sum(len(g) for _, g in palaces)
    print(f"提取 {n} 卦 / {len(palaces)} 宫 → {out}")


if __name__ == "__main__":
    main()
