"""六爻排盘引擎。

快速使用：
    from liuyao import cast_board
    board = cast_board("地泽临", moving=2, month_zhi="未", day_gz="辛卯", yongshen_qin="妻财")
    print(board.line(2).jin_tui)   # "化退神"
"""

from .board import cast_board, Board, Line
from .data import find_hexagram, HEXAGRAMS
from .wuxing import xunkong, liuqin, wuxing_state, is_prosperous
from .format import format_board

__all__ = [
    "cast_board", "Board", "Line",
    "find_hexagram", "HEXAGRAMS",
    "xunkong", "liuqin", "wuxing_state", "is_prosperous",
    "format_board",
]

__version__ = "0.1.0"
