#!/usr/bin/env python3
"""六爻排盘 CLI。

示例：
    python src/paipan.py --hexagram 地泽临 --moving 2 --month 未 --day 辛卯 --yongshen 妻财
"""

import argparse
import sys
from pathlib import Path

# 让脚本可直接运行（把 src/ 加入 path，使 import liuyao 可用）
sys.path.insert(0, str(Path(__file__).resolve().parent))

from liuyao import cast_board, format_board


def parse_moving(s):
    return [int(x.strip()) for x in str(s).split(",") if x.strip()]


def main():
    p = argparse.ArgumentParser(description="六爻排盘")
    p.add_argument("--hexagram", required=True, help="卦名，如 地泽临 / 临")
    p.add_argument("--moving", required=True, help="动爻位置，如 2 或 2,4")
    p.add_argument("--month", required=True, help="月建地支，如 未")
    p.add_argument("--day", required=True, help="日干支(两天字符)，如 辛卯")
    p.add_argument("--yongshen", help="用神六亲，如 妻财（可选）")
    args = p.parse_args()

    board = cast_board(
        args.hexagram, parse_moving(args.moving),
        args.month, args.day, args.yongshen,
    )
    print(format_board(board))


if __name__ == "__main__":
    main()
