# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-07-16

### Added
- **Skill**: `skill/liuyao-divination/SKILL.md` — Claude Code / agent skill for Liu Yao (六爻) divination analysis, distilling a complete interpretive methodology.
- **Reference docs** (`references/`): 8 monographs covering 装卦排盘 (casting & assigning), 用神取用 (selecting the Significant Line), 旺衰月日 (strength via month/day), 动静暗破 (moving/dark-move/broken/void), 进退神化 (advancing/retreating transformation), 三合六合 (combinations), 墓库论 (graveyard/storehouse theory), 断卦步骤 (full interpretation workflow).
- **Python engine** (`src/liuyao/`): programmatic board-casting — 64 hexagrams, eight palaces & six relations (六亲), nayin-stem assignment (纳甲), six spirits (六神), void/empty (空亡), month/day break (月破/日破), dark-move (暗动), advancing/retreating spirit (化进/化退), twelve-stage graveyard (十二长生墓库), world/response (世应).
- **CLI**: `src/paipan.py` — cast and print a board from hexagram + moving line + month + day.
- **Report generator**: `tools/generate_report.py` — render an ornate classical-style HTML report from a structured case JSON.
- **Examples**: `examples/01-是否旺己-地泽临之复.json` — the canonical case (地泽临 → 地雷复, 辛卯日) used to validate the engine end-to-end.
- Bilingual README (English + 简体中文), MIT license.

[Unreleased]: https://github.com/Johnson/liuyao-divination/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/Johnson/liuyao-divination/releases/tag/v0.1.0
