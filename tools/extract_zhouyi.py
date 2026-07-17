#!/usr/bin/env python3
"""从《易经六十四卦》整理稿提取卦辞、爻辞原文 → data/zhouyi.json。

整理稿用颜色标注：红色 <font color="#ff0000"> 为卦辞/爻辞原文；绿色为《彖》《象》
传及解读，不取。爻辞按爻位(初九/九二/…/上九/初六/…/用九/用六)识别；卦辞取每卦
首个"X：…"式短句。

用法（项目根目录）：
    python tools/extract_zhouyi.py ../易经六十四卦.md
"""

import json
import re
import sys
from pathlib import Path

RED = re.compile(r'<font color="#ff0000">(.*?)</font>', re.S)
YAO_KW = ["初九", "九二", "九三", "九四", "九五", "上九",
          "初六", "六二", "六三", "六四", "六五", "上六", "用九", "用六"]
YAO_RE = re.compile(r"^(" + "|".join(YAO_KW) + r")[：:]")
GUACI_HEAD = re.compile(r"^.{1,3}[：:]")


def _strip_text(s):
    return re.sub(r"</?font[^>]*>", "", s).strip()


# 个别卦辞源稿未单独标红，补公有领域《周易》原文（不带卦名前缀，与脚本风格一致）
GUACI_OVERRIDES = {
    "山泽损": "有孚，元吉，无咎，可貞，利有攸往。曷之？二簋可用享。",
}


def extract(src_path):
    text = Path(src_path).read_text(encoding="utf-8")
    result = {}
    for part in re.split(r"\n(?=## 《)", text):
        gm = re.match(r"## 《(.+?)》", part.strip())
        if not gm:
            continue
        name = gm.group(1).strip()
        # 只取"人间道"段，排除"文言曰"等，避免文言内容污染爻辞
        seg = part
        sm = re.search(r"### 人间道", part)
        if sm:
            seg = part[sm.end():]
            nxt = re.search(r"\n### ", seg)
            if nxt:
                seg = seg[:nxt.start()]
        reds = [r for r in (_strip_text(x) for x in RED.findall(seg)) if r]
        gua_ci = ""
        yao = {}
        # 卦辞：人间道段首条红色。兼容三种格式：
        #   "X：内容"（取内容）、纯前缀"X："（取下一段）、无前缀直接内容（整条取）
        if reds and not YAO_RE.match(reds[0]):
            first = reds[0]
            cm = re.match(r"^(.{1,3})[：:](.*)$", first, re.S)
            if cm:
                gua_ci = cm.group(2).strip()
                if not gua_ci and len(reds) > 1 and not YAO_RE.match(reds[1]):
                    gua_ci = reds[1]   # 纯前缀"X："后跟卦辞内容
                # 若后跟爻辞，说明卦辞内容源稿未标红 → 留空
            else:
                gua_ci = first
        # 爻辞
        for r in reds:
            ym = YAO_RE.match(r)
            if ym and ym.group(1) not in yao:
                yao[ym.group(1)] = r.split("：", 1)[1].strip() if "：" in r else r
        result[name] = {"gua_ci": gua_ci or GUACI_OVERRIDES.get(name, ""), "yao": yao}
    return result


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "../易经六十四卦.md"
    data = extract(src)
    out = Path("data/zhouyi.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    n_gua = len(data)
    n_ci = sum(1 for v in data.values() if v["gua_ci"])
    n_yao = sum(len(v["yao"]) for v in data.values())
    miss_gua = [k for k, v in data.items() if not v["gua_ci"]]
    print(f"提取 {n_gua} 卦：卦辞 {n_ci}、爻辞 {n_yao}")
    if miss_gua:
        print(f"⚠️ 卦辞缺失({len(miss_gua)})：{miss_gua[:10]}")


if __name__ == "__main__":
    main()
