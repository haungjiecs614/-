---
name: audit
description: 对指定章节范围做一致性、节奏、账本健康三项体检，报告写入 audits/。建议每 10 章一次。用法：/audit 41-50
argument-hint: "<起-止> 例：41-50"
disable-model-invocation: true
allowed-tools: Read, Write, Glob, Grep, Agent, Task, Bash(python3 tools/novel.py:*)
---

# /audit —— 阶段体检

目标范围：**$ARGUMENTS**，报告写入 `audits/audit-起-止.md`（三位数补零，如 audits/audit-041-050.md）。

## 0. 先跑机械检查（结果全部进报告附录）
- `python3 tools/novel.py check-cards $ARGUMENTS`
- `python3 tools/novel.py count $ARGUMENTS`
- `python3 tools/novel.py lint $ARGUMENTS`
- `python3 tools/novel.py health`

## 1. 一致性审计
- 读取：bible/（core、world、relations、相关角色档案）、state/ledger.md、state/foreshadow.md、state/summaries.md，以及范围内各章正文。
- 范围较大时，可以并行调用 `continuity` 子智能体分段检查（例如每 3–4 章一个），再合并结果。
- 输出冲突清单：正文位置 / 冲突内容 / 冲突来源文件 / 严重程度（硬伤 / 瑕疵）。
- 特别检查：人物声纹是否在范围内逐渐趋同；主角是否出现"洗白"倾向；尺度是否越线；【待访谈】设定是否被偷偷写成了事实。

## 2. 节奏审计
- 列出每章：主功能 / 脉冲级别 / 推进的进度条 / 章末钩子类型（来自章节卡，并对照正文核实是否真的兑现）。
- 按 structure/rhythm.md 的"平淡区定义"标出连续平淡区。
- 统计四个喜剧引擎在范围内的出场比重，标出被冷落或过度使用的引擎。
- 字数分布：偏短/偏长的章节。

## 3. 账本健康
- 开放悬念数量（理想 3–5 个），过多或过少都要说明后果。
- 超期未回收伏笔（以 health 结果为准），以及"埋了很久却从未被提起"的伏笔。
- 过度使用的梗（需升级/接近退休/已违规）。

## 4. 报告结构
```markdown
# 体检报告 ch起–ch止
## 总评（三句话以内）
## 一、一致性
## 二、节奏
## 三、账本健康
## 下一个 10 章最该调整的 3 件事
1. ……（具体到要改哪类章节卡、哪条伏笔、哪个梗）
2. ……
3. ……
---
## 附录：机械检查结果
```

## 5. 回复作者
总评 + "下一个 10 章最该调整的 3 件事" + 报告路径。

**只出报告，不修改任何正文、章节卡、bible 或 state。** 需要改的列为建议，由作者决定。
