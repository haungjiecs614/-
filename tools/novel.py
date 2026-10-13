#!/usr/bin/env python3
"""小说生产系统的确定性辅助脚本。

凡是"数数"类的工作（字数、次数、超期、连续性规则）交给脚本，不靠模型目测。
只读：本脚本从不修改任何文件。

用法（在项目根目录执行）：
  python3 tools/novel.py count <章节>          正文字数，如 47 / 41-50 / all
  python3 tools/novel.py tail <章号> [字数]     某章结尾约 N 字（默认 1500），按段落对齐
  python3 tools/novel.py recent <章号> [k]      该章之前最近 k 章摘要（默认 10）
  python3 tools/novel.py check-cards <章节>     章节卡规则检查（主功能轮换、中脉冲、进度条、空字段）
  python3 tools/novel.py lint <章节>            按 style/banned.md 的"机检正则"扫描 AI 腔，并检查超长段落、章末升华
  python3 tools/novel.py health [--at 章号]     账本健康（开放悬念数、超期伏笔/悬念、梗次数）
  python3 tools/novel.py stats                  仪表盘数据与下一步建议
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CARDS, CHAPTERS, REVIEWS = ROOT / "cards", ROOT / "chapters", ROOT / "reviews"
STATE = ROOT / "state"

WORD_MIN, WORD_MAX = 2500, 3000
FUNCTIONS = ["推进主线", "关系变化", "纯喜剧", "悬念揭示", "高潮"]
PULSES = ["小脉冲", "中脉冲", "大脉冲"]
BARS = ["主线", "关系", "悬念", "喜剧组合"]
REQUIRED_FIELDS = [
    "所属卷/篇", "主功能（单选）", "脉冲级别（单选）", "推进的进度条（至少一项）", "视角",
    "出场角色", "开场状态（引自 ledger）", "核心冲突", "中段转折（本章必须有一次局势翻转）",
    "本章不允许解决的矛盾", "喜剧引擎与具体梗", "章末钩子", "字数预算",
]
CJK = re.compile(r"[㐀-䶿一-鿿豈-﫿]")


def fname(n):
    return f"ch{n:03d}.md"


def parse_spec(spec, folder=CHAPTERS):
    if spec == "all":
        return sorted(int(m.group(1)) for p in folder.glob("ch*.md")
                      if (m := re.fullmatch(r"ch(\d+)\.md", p.name)))
    m = re.fullmatch(r"(\d+)(?:-(\d+))?", spec)
    if not m:
        sys.exit(f"无法解析章节参数：{spec}（应为 47、41-50 或 all）")
    a = int(m.group(1))
    b = int(m.group(2) or a)
    return list(range(a, b + 1))


def read(path):
    return path.read_text(encoding="utf-8") if path.exists() else None


def body_of(text):
    """去掉标题行与场景分隔符，只留正文段落。"""
    lines = [l for l in text.splitlines()
             if l.strip() and not l.lstrip().startswith("#") and l.strip() not in ("* * *", "***", "---")]
    return lines


def count_words(text):
    lines = body_of(text)
    joined = "".join(lines)
    total = len(re.sub(r"\s", "", joined))
    hanzi = len(CJK.findall(joined))
    return total, hanzi, len(lines)


def md_table(text, first_header):
    """解析以 first_header 开头的 markdown 表格，返回 dict 列表。"""
    rows, header = [], None
    for line in text.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if header is None:
            if cells and cells[0] == first_header:
                header = cells
            continue
        if set("".join(cells)) <= set("-: "):
            continue
        if len(cells) < len(header):
            cells += [""] * (len(header) - len(cells))
        rows.append(dict(zip(header, cells)))
    return rows


def nums(s):
    return [int(x) for x in re.findall(r"\d+", s or "")]


def summaries():
    text = read(STATE / "summaries.md") or ""
    parts = re.split(r"^(## 第(\d+)章.*)$", text, flags=re.M)
    out = []
    for i in range(1, len(parts) - 2, 3):
        out.append((int(parts[i + 1]), parts[i].strip(), parts[i + 2].strip()))
    return out


def card_fields(n):
    text = read(CARDS / fname(n))
    if text is None:
        return None
    fields = {}
    for line in text.splitlines():
        m = re.match(r"^- (.+?)：(.*)$", line.strip())
        if m:
            fields[m.group(1).strip()] = m.group(2).strip()
    fields["__raw__"] = text
    return fields


def pick(value, options):
    return [o for o in options if o in (value or "")]


# ---------------------------------------------------------------- 子命令

def cmd_count(spec):
    print("| 章 | 正文字数 | 汉字 | 段落数 | 判定 |")
    print("|---|---|---|---|---|")
    grand = 0
    for n in parse_spec(spec):
        text = read(CHAPTERS / fname(n))
        if text is None:
            print(f"| {n:03d} | — | — | — | 文件不存在 |")
            continue
        total, hanzi, paras = count_words(text)
        grand += total
        verdict = "✅" if WORD_MIN <= total <= WORD_MAX else ("⚠️ 偏短" if total < WORD_MIN else "⚠️ 偏长")
        print(f"| {n:03d} | {total} | {hanzi} | {paras} | {verdict} |")
    print(f"\n合计正文字数：{grand}（正文字数=去空白后的全部字符，含标点；目标每章 {WORD_MIN}–{WORD_MAX}）")


def cmd_tail(n, chars=1500):
    text = read(CHAPTERS / fname(n))
    if text is None:
        print(f"chapters/{fname(n)} 不存在（如果是第 1 章，没有上一章，跳过此步）。")
        return
    lines = body_of(text)
    picked, acc = [], 0
    for line in reversed(lines):
        picked.append(line)
        acc += len(line)
        if acc >= chars:
            break
    print(f"<!-- chapters/{fname(n)} 结尾约 {acc} 字 -->")
    print("\n\n".join(reversed(picked)))


def cmd_recent(n, k=10):
    items = [s for s in summaries() if s[0] < n][-k:]
    if not items:
        print("（state/summaries.md 中没有更早的摘要。）")
        return
    for _, head, body in items:
        print(head)
        print(body)
        print()


def cmd_check_cards(spec):
    targets = parse_spec(spec, CARDS)
    problems, warns = [], []
    lo, hi = min(targets), max(targets)
    span = range(max(1, lo - 9), hi + 1)
    cards = {n: card_fields(n) for n in span}

    for n in targets:
        f = cards.get(n)
        if f is None:
            problems.append(f"ch{n:03d}：章节卡不存在")
            continue
        for key in REQUIRED_FIELDS:
            v = f.get(key, None)
            if v is None:
                problems.append(f"ch{n:03d}：缺少字段「{key}」")
            elif not v or v.strip("_ /") == "":
                problems.append(f"ch{n:03d}：字段「{key}」为空")
        fn = pick(f.get("主功能（单选）"), FUNCTIONS)
        if len(fn) != 1:
            problems.append(f"ch{n:03d}：主功能必须单选，当前为「{f.get('主功能（单选）', '')}」")
        if len(pick(f.get("脉冲级别（单选）"), PULSES)) != 1:
            problems.append(f"ch{n:03d}：脉冲级别必须单选")
        if not pick(f.get("推进的进度条（至少一项）"), BARS):
            problems.append(f"ch{n:03d}：未推动任何进度条（主线/关系/悬念/喜剧组合）")
        if "【待访谈】" in f["__raw__"]:
            problems.append(f"ch{n:03d}：章节卡引用了未确认设定（含【待访谈】）")

    # 连续 3 章同一主功能
    seq = [(n, (pick((cards.get(n) or {}).get("主功能（单选）"), FUNCTIONS) or [None])[0]) for n in span]
    for i in range(2, len(seq)):
        trio = seq[i - 2:i + 1]
        if trio[-1][0] in targets and trio[0][1] and len({t[1] for t in trio}) == 1 \
                and all(t[0] == trio[0][0] + j for j, t in enumerate(trio)):
            problems.append(f"ch{trio[0][0]:03d}–ch{trio[-1][0]:03d}：连续 3 章主功能均为「{trio[0][1]}」")

    # 任意连续 10 章至少 1 次中/大脉冲；两次中脉冲间隔不超过 8 章
    have = [n for n in span if cards.get(n)]
    big = [n for n in have if pick(cards[n].get("脉冲级别（单选）"), ["中脉冲", "大脉冲"])]
    for start in range(span.start, hi - 8):
        window = range(start, start + 10)
        if all(cards.get(x) for x in window) and window[-1] >= lo and not any(x in big for x in window):
            problems.append(f"ch{start:03d}–ch{start + 9:03d}：连续 10 章没有中脉冲")
    for a, b in zip(big, big[1:]):
        if b - a > 8 and b >= lo:
            warns.append(f"ch{a:03d} 与 ch{b:03d} 两次中/大脉冲间隔 {b - a} 章（规则：5–8 章）")

    print(f"## 章节卡检查 ch{lo:03d}–ch{hi:03d}")
    print("\n### 违规" if problems else "\n### 违规：无")
    for p in problems:
        print(f"- ❌ {p}")
    if warns:
        print("\n### 提醒")
        for w in warns:
            print(f"- ⚠️ {w}")
    print("\n### 主功能 / 脉冲序列（含范围前 9 章作为上下文）")
    for n in span:
        f = cards.get(n)
        if f:
            mark = "→" if n in targets else " "
            print(f"{mark} ch{n:03d} | {f.get('主功能（单选）', '')} | {f.get('脉冲级别（单选）', '')} | {f.get('推进的进度条（至少一项）', '')}")


def banned_patterns():
    text = read(ROOT / "style" / "banned.md") or ""
    m = re.search(r"机检正则.*?```regex\n(.*?)```", text, flags=re.S)
    pats = []
    for line in (m.group(1).splitlines() if m else []):
        line = line.strip()
        if line and not line.startswith("#"):
            pats.append(re.compile(line))
    return pats


def cmd_lint(spec):
    pats = banned_patterns()
    for n in parse_spec(spec):
        text = read(CHAPTERS / fname(n))
        print(f"## ch{n:03d} 机检")
        if text is None:
            print("- 文件不存在\n")
            continue
        hits = []
        lines = text.splitlines()
        for i, line in enumerate(lines, 1):
            for p in pats:
                for m in p.finditer(line):
                    hits.append(f"- L{i} 命中「{m.group(0)}」（规则 `{p.pattern}`）：{line.strip()[:60]}")
            if len(line.strip()) > 150 and not line.lstrip().startswith("#"):
                hits.append(f"- L{i} 段落过长（{len(line.strip())} 字，建议 ≤100–150）")
        body = body_of(text)
        if body and re.search(r"(也许|或许|终于明白|这就是|人生|成长|命运)", body[-1]):
            hits.append(f"- 末段疑似升华/总结：{body[-1][:60]}")
        print("\n".join(hits) if hits else "- 无命中")
        print()


def latest_synced():
    s = summaries()
    return s[-1][0] if s else 0


def health_report(at=None):
    at = at or latest_synced()
    lines = [f"## 账本健康（以第 {at:03d} 章为当前进度）" if at else "## 账本健康（尚无已同步章节）"]

    qs = md_table(read(STATE / "questions.md") or "", "悬念问题")
    open_q = [q for q in qs if q.get("状态") in ("开放", "部分回答")]
    tag = "✅" if 3 <= len(open_q) <= 5 else "⚠️"
    lines.append(f"\n### 开放悬念：{len(open_q)} 个 {tag}（理想 3–5）")
    for q in open_q:
        due = nums(q.get("计划回答章节"))
        late = f" ⏰ 超期（计划 {due[0]:03d}）" if due and at and due[0] < at else ""
        lines.append(f"- {q.get('悬念问题')}（{q.get('提出章节')} 提出，计划 {q.get('计划回答章节')}）{late}")

    fs = md_table(read(STATE / "foreshadow.md") or "", "伏笔")
    open_f = [f for f in fs if f.get("状态") == "未回收"]
    overdue = [f for f in open_f if nums(f.get("计划回收章节")) and at and nums(f.get("计划回收章节"))[0] < at]
    lines.append(f"\n### 待回收伏笔：{len(open_f)} 个，其中超期 {len(overdue)} 个")
    for f in open_f:
        flag = " ⏰ 超期" if f in overdue else ""
        lines.append(f"- {f.get('伏笔')}（{f.get('埋设章节')} 埋，计划 {f.get('计划回收章节')} 收）{flag}")

    gags = md_table(read(STATE / "gags.md") or "", "梗")
    lines.append(f"\n### 梗使用排行（共 {len(gags)} 个）")
    ranked = sorted(gags, key=lambda g: -len(nums(g.get("使用章节列表"))))
    for g in ranked:
        used = len(nums(g.get("使用章节列表")))
        recorded = nums(g.get("次数"))
        status = g.get("状态", "")
        issues = []
        if recorded and recorded[0] != used:
            issues.append(f"次数栏 {recorded[0]} 与章节列表 {used} 不一致")
        if used >= 5:
            issues.append("❌ 已超过 4 次上限")
        elif used == 4 and status != "退休":
            issues.append("应标为退休")
        elif used in (2, 3) and status == "活跃":
            issues.append("应标为需升级")
        note = f" ⚠️ {'；'.join(issues)}" if issues else ""
        lines.append(f"- {g.get('梗')}［{g.get('所属引擎')}］{used} 次 · {status}{note}")
    return "\n".join(lines)


def cmd_health(at=None):
    print(health_report(at))


def volumes():
    text = read(ROOT / "structure" / "outline.md") or ""
    out = []
    for m in re.finditer(r"\|\s*(第.卷)\s*\|\s*ch(\d+)\s*[–-]\s*ch(\d+)", text):
        out.append((m.group(1), int(m.group(2)), int(m.group(3))))
    return out


def cmd_stats():
    chapters = parse_spec("all", CHAPTERS)
    cards = parse_spec("all", CARDS)
    reviewed = sorted(int(m.group(1)) for p in REVIEWS.glob("ch*-review.md")
                      if (m := re.fullmatch(r"ch(\d+)-review\.md", p.name)))
    synced = [s[0] for s in summaries()]
    words = {n: count_words(read(CHAPTERS / fname(n)))[0] for n in chapters}

    print("## 产能")
    print(f"- 章节卡：{len(cards)} 张" + (f"（ch{cards[0]:03d}–ch{cards[-1]:03d}）" if cards else ""))
    print(f"- 正文：{len(chapters)} 章，合计 {sum(words.values())} 字（目标约 300000，"
          f"完成 {sum(words.values()) / 3000:.1f}%）")
    print(f"- 已审稿：{len(reviewed)} 章；已同步（完成）：{len(synced)} 章")

    print("\n## 分卷进度")
    for name, a, b in volumes():
        done = [n for n in synced if a <= n <= b]
        print(f"- {name}（ch{a:03d}–ch{b:03d}）：已完成 {len(done)}/{b - a + 1} 章")

    print("\n## 流水线断点")
    no_ch = [n for n in cards if n not in chapters]
    no_rv = [n for n in chapters if n not in reviewed]
    no_sync = [n for n in chapters if n not in synced]
    bad_len = [n for n, w in words.items() if not WORD_MIN <= w <= WORD_MAX]
    print(f"- 有卡未写：{', '.join(f'{n:03d}' for n in no_ch) or '无'}")
    print(f"- 已写未审：{', '.join(f'{n:03d}' for n in no_rv) or '无'}")
    print(f"- 已写未同步：{', '.join(f'{n:03d}' for n in no_sync) or '无'}")
    print(f"- 字数不达标：{', '.join(f'{n:03d}({words[n]})' for n in bad_len) or '无'}")
    gaps = [n for n in synced if n > 1 and n - 1 not in synced]
    if gaps:
        print(f"- ⚠️ 同步断档：第 {', '.join(f'{n:03d}' for n in gaps)} 章之前一章未同步")

    audited = [int(m.group(2)) for p in (ROOT / "audits").glob("audit-*.md")
               if (m := re.fullmatch(r"audit-(\d+)-(\d+)\.md", p.name))]
    last_audit = max(audited, default=0)
    print(f"- 最近体检覆盖到：{f'ch{last_audit:03d}' if last_audit else '尚未体检'}")

    print()
    print(health_report())

    print("\n## 下一步建议")
    last = synced[-1] if synced else 0
    tips = []
    if no_sync:
        n = no_sync[0]
        if n not in reviewed:
            tips.append(f"/review {n}（第 {n} 章已写未审）")
        else:
            tips.append(f"作者精修第 {n} 章 → 定稿后 /sync {n}")
    elif (last + 1) in cards:
        tips.append(f"/write {last + 1}")
    else:
        tips.append(f"/cards {last + 1}-{last + 10}（后续没有章节卡）")
    if last - last_audit >= 10:
        a = last_audit + 1
        tips.append(f"/audit {a}-{a + 9}（距上次体检已同步 {last - last_audit} 章）")
    for t in tips:
        print(f"- {t}")


def main(argv):
    if len(argv) < 2 or argv[1] in ("-h", "--help"):
        print(__doc__)
        return
    cmd, args = argv[1], argv[2:]
    if cmd == "count":
        cmd_count(args[0] if args else "all")
    elif cmd == "tail":
        cmd_tail(int(args[0]), int(args[1]) if len(args) > 1 else 1500)
    elif cmd == "recent":
        cmd_recent(int(args[0]), int(args[1]) if len(args) > 1 else 10)
    elif cmd == "check-cards":
        cmd_check_cards(args[0])
    elif cmd == "lint":
        cmd_lint(args[0] if args else "all")
    elif cmd == "health":
        cmd_health(int(args[1]) if len(args) > 1 and args[0] == "--at" else None)
    elif cmd == "stats":
        cmd_stats()
    else:
        sys.exit(f"未知子命令：{cmd}\n{__doc__}")


if __name__ == "__main__":
    main(sys.argv)
