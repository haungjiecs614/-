---
name: write
description: 按章节卡写正文到 chapters/，写完自检。不更新 state/。用法：/write 47 或 /write 47-48
argument-hint: "<章号或范围> 例：47 或 47-48"
disable-model-invocation: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(python3 tools/novel.py:*)
---

# /write —— 写正文

目标：**$ARGUMENTS**（范围则按章号顺序逐章完成，每章完整走一遍下面的流程后再写下一章）

## 0. 前置检查
- `cards/chXXX.md` 不存在 → 停止，提示作者先运行 `/cards XXX`。
- `chapters/chXXX.md` 已存在 → 停止，问作者是要覆盖重写、还是在原稿上修改。
- 上一章（第 1 章除外）尚未 /sync → 提醒作者：ledger 不是本章的开场状态，本章将以"章节卡开场状态 + 上一章正文"为准。如果是范围写作（如 47-48），第 48 章就属于这种情况，属正常。

## 1. 必读清单（严格按 CLAUDE.md 顺序，一项都不能跳）
1. `cards/chXXX.md`
2. `state/ledger.md`
3. 本章出场角色的 `bible/characters/*.md`（以章节卡"出场角色"为准；重点看声纹、喜剧引擎、不可违背的设定）
4. 最近 10 章摘要：`python3 tools/novel.py recent XXX`
5. 上一章结尾约 1500 字：`python3 tools/novel.py tail <XXX-1>`
6. `state/gags.md`
7. `style/guide.md` 与 `style/banned.md`
8. `style/anchors/` 下作者已确认的样本（`candidates/` 不算）

**不要读取其他章节的完整正文。** 上下文工程的意义就在于只带最小充分信息。

## 2. 写作
- 写入 `chapters/chXXX.md`。第一行 `# 第X章 章名`，之后只有正文。没有任何说明文字、注释、括号备注。
- 章节卡是合同：核心冲突、中段转折、章末钩子必须兑现；"本章不允许解决的矛盾"绝不能解决；"禁区"绝不踩。
- 喜剧用机制生成：每个场景先确定是哪个引擎在转，再写台词。
- 好色桥段只写到口嗨、意淫、吹牛、计划失败、被反杀、被扇，镜头在得逞之前切断。
- 遇到章节卡没写到、但需要新设定才能写下去的地方：不得编造，停下来用 CLAUDE.md 的【冲突报告】格式报告。

## 3. 自检（写完必须做）
1. 字数：`python3 tools/novel.py count XXX`。不在 2500–3000 内就修改到达标再继续。
2. AI 腔机检：`python3 tools/novel.py lint XXX`。逐条处理命中项（改掉，或确认是误报并说明）。
3. 对照章节卡逐项核对：核心冲突 / 中段转折 / 章末钩子是否兑现；伏笔埋设与回收是否到位；有没有解决"不允许解决"的矛盾。
4. 对照 state/gags.md：是否重复用了已退休的梗；需升级的梗是否真的升级了。
5. 对照 style/banned.md 的非机检条目：角色有没有互相说明已知信息、叙述者有没有解释笑点、章末有没有升华。

## 4. 回复作者（三五行即可）
```
第XXX章已写入 chapters/chXXX.md
- 字数：____（count 结果）
- 章节卡兑现：冲突 ✅/❌ · 转折 ✅/❌ · 钩子 ✅/❌ · 伏笔 ✅/❌
- 机检：命中 __ 处，已修 __ 处，保留 __ 处（理由）
- 梗：本章使用 ____（无重复 / 有升级）
- 最没把握的地方：____
建议下一步：/review XXX
```

**此命令不更新 state/。** 状态更新在作者审定后由 `/sync` 执行。
