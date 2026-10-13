---
name: review
description: 调用 critic（挑剔读者）与 continuity（连续性审计员）两个子智能体独立审稿，合并写入 reviews/。用法：/review 47
argument-hint: "<章号> 例：47"
disable-model-invocation: true
allowed-tools: Read, Write, Glob, Grep, Agent, Task, Bash(python3 tools/novel.py:*)
---

# /review —— 独立审稿

目标：第 **$ARGUMENTS** 章（三位数补零，记为 XXX）

## 0. 前置检查
- `chapters/chXXX.md` 不存在 → 停止。
- `reviews/chXXX-review.md` 已存在 → 把旧文件改名为 `reviews/chXXX-review-r1.md`（已有 r1 则 r2，依此类推）后再写新的，保留审稿历史。

## 1. 并行调用两个子智能体（写审分离 + 信息隔离）
在**同一条消息里**同时发起两个子智能体调用，让它们互不影响：

- **critic**（subagent_type: `critic`）。给它的提示只包含：
  > 审第 XXX 章：chapters/chXXX.md。按你的工作规范输出。
  不要把章节卡、作者意图、写作者自检结果、你自己的看法传给它——真实读者看不到这些，critic 也不该看到。

- **continuity**（subagent_type: `continuity`）。给它的提示：
  > 审第 XXX 章：chapters/chXXX.md，章节卡 cards/chXXX.md。注意：state/ 当前反映的是第 XXX 章开始前的状态（本章尚未 /sync）。按你的工作规范输出冲突清单。

不要自己代替子智能体审稿；不要在子智能体返回前预判结论。

## 2. 机检补充
运行 `python3 tools/novel.py count XXX` 与 `python3 tools/novel.py lint XXX`，结果作为附录。

## 3. 合并写入 reviews/chXXX-review.md
严格按 templates/review.md 的结构：

```markdown
# 第XXX章 审稿
## 弃书风险评分（1–10）：N
（一句话说明分数依据。以 critic 的评分为基础；continuity 发现硬伤（时间线/能力/信息差错误）时酌情上调。）
## 挑剔读者意见（critic）
（critic 原始意见，保留原文引用与行号，可去重、可按严重程度排序，不得软化措辞）
## 连续性问题（continuity）
（continuity 冲突清单原样保留：正文位置 / 冲突内容 / 来源文件）
## 最重要的 3 条修改建议
1. ……（指向具体位置，写清怎么改）
2. ……
3. ……
## 作者决定（留空，由作者填写）

---
### 附录：机检
（count 与 lint 结果）
```

"最重要的 3 条"排序原则：连续性硬伤 > 读者弃书点 > 笑点失效 > AI 腔 > 措辞。

## 4. 回复作者
- 弃书风险评分：N / 10
- 最重要的 3 条修改建议（每条一两行）
- 审稿记录路径
- 提示：精修定稿后运行 `/sync XXX`

**不修改正文。** 改不改、怎么改由作者决定。
