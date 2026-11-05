# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Reference docs**: `references/12-应期与应验.md` — 应期多通道交叉定位与置信度分级、化出之支三重身份（"退而得合"辨析）、应验分层核对、验卦复盘闭环（事前断语/事后补释证据分级）。`references/13-象意解读.md` — **全要素象意体系**：七层象源（五行五性、关系、状态、爻位、天时、卦象、六神）一套语法「**象核 × 域 × 角色**」同象异读；象核×域速查表、旺相休囚死的处境象、十二长生的生命周期象、间爻=中间人象、月建日辰天时象、多象同向与层间互校、同盘异占迁移示范。均以验证卦例（地泽临之复）匿名贯穿。
- **Skill**: `SKILL.md` 新增关键辨析 #11（象意三要素·同象异读）、#12（应期多通道交叉与应验分层）及速查条目；Deep References 同步。
- **Report generator**: 报告布局从「占时快照」升级为「断→验→续生命周期档案」——新增可选节 **肆·应验纪实**（事实时间线 + 逐象对应表 + 证据分级徽章：事前断语·已验/事后对账/回溯吻合）与 **伍·应期追踪**（时间窗/卦理预期/状态徽章：待验/警示），编号动态顺延；旧案例 JSON 无新字段则不渲染（完全向后兼容）。
- README（中/英）结构树更新为 13 册。

### Fixed
- **Engine**: `wuxing_state()` 相/休 判定反转 — 旧版"生令者相、令生者休"，与《增删卜易》及本项目 `references/03` 表格、案例断言相反；现为 **当令所生者相、生令者休**（例：未月土令，金相、火休）。案例 01 中子孙酉金旺衰由"休"正为"相"，元神有力理由由"发动有力"精化为"旺相有力"；暗动等其余判定不受影响（`is_prosperous` 多通道兜底）。
- **Docs**: `references/03-旺衰月日.md`、`SKILL.md` 旺相休囚死速查文字表述同步修正，与表格一致。
- **Tests**: 新增五行五态全表参数化测试 + 案例 01 回归断言（未月酉金=相、巳火=休、暗动不变），共 29 项。

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
