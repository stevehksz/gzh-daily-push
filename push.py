# -*- coding: utf-8 -*-
"""GitHub Trending 每日推送（GitHub Actions 版）
数据源：https://github.com/trending?since=daily
输出：Server酱 -> 微信（每天 1 条，带明文网址）
凭证：SendKey 从环境变量 SCT_SENDKEY 读取，绝不写进代码。
只用标准库，Actions 里无需 pip install。
"""
import html as htmllib
import json
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

TRENDING_URL = "https://github.com/trending?since=daily"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

# ⭐高相关关键词（AI / 开发者工具 / 效率类）
HIGH_KEYWORDS = [
    "ai", "agent", "llm", "gpt", "claude", "mcp", "copilot", "codex",
    "tts", "voice", "speech", "model", "security-audit", "skill",
    "plugin", "rag", "prompt", "devtool", "cli-tool", "automation",
]


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")


def strip_tags(s):
    return htmllib.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def parse_trending(page):
    repos = []
    for block in page.split("<article")[1:]:
        m = re.search(r'<h2[^>]*>\s*<a[^>]*href="/([^"]+)"', block)
        if not m:
            continue
        name = m.group(1).strip("/")
        if "/" not in name:
            continue
        dm = re.search(r'<p class="col-9[^"]*"[^>]*>(.*?)</p>', block, re.S)
        desc = strip_tags(dm.group(1)) if dm else ""
        lm = re.search(r'itemprop="programmingLanguage">([^<]+)<', block)
        lang = lm.group(1).strip() if lm else "-"
        sm = re.search(r'href="/[^"]+/stargazers"[^>]*>\s*([\d,]+)\s*</a>', block)
        stars = sm.group(1) if sm else "-"
        tm = re.search(r'([\d,]+)\s+stars\s+today', block)
        today = tm.group(1) if tm else "0"
        repos.append({"name": name, "desc": desc, "lang": lang,
                      "stars": stars, "today": today})
    return repos


def is_high(repo):
    text = (repo["name"] + " " + repo["desc"]).lower()
    return any(k in text for k in HIGH_KEYWORDS)


def build_desp(repos):
    now = datetime.now(timezone(timedelta(hours=8)))
    title = "GitHub 热点早报 | %d月%d日" % (now.month, now.day)
    highs = [r for r in repos if is_high(r)]
    lows = [r for r in repos if not is_high(r)]
    ordered = highs + lows
    n_high = len(highs)
    lines = ["今日 Trending 前 %d 个仓库里，%d 个和 AI/开发者工具沾边。" % (len(ordered), n_high), ""]
    for i, r in enumerate(ordered, 1):
        mark = "⭐ " if is_high(r) else ""
        lines.append("**%d. %s%s**" % (i, mark, r["name"]))
        lines.append("%s · **%s** star · 今日 **+%s**" % (r["lang"], r["stars"], r["today"]))
        lines.append("网址：https://github.com/%s" % r["name"])
        lines.append("")
        lines.append(r["desc"] if r["desc"] else "（暂无描述）")
        lines.append("")
    return title, "\n".join(lines)


def push(title, desp):
    key = None
    import os
    raw = os.environ.get("SCT_SENDKEY", "")
    m = re.search(r"(SCT[0-9A-Za-z]+)", raw)
    if not m:
        print("ERROR: SCT_SENDKEY 里提取不到 SCT 开头的合法 SendKey，请检查 Secret 值")
        sys.exit(2)
    key = m.group(1)
    if not key:
        print("ERROR: SCT_SENDKEY 环境变量为空")
        sys.exit(2)
    payload = urllib.parse.urlencode({"title": title, "desp": desp}).encode("utf-8")
    req = urllib.request.Request(
        "https://sctapi.ftqq.com/%s.send" % key, data=payload, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded; charset=utf-8")
    with urllib.request.urlopen(req, timeout=30) as r:
        body = r.read().decode("utf-8")
    print("RAW:", body)
    d = json.loads(body)
    if d.get("code") != 0:
        print("PUSH FAILED: code=%s msg=%s" % (d.get("code"), d.get("message")))
        sys.exit(3)
    print("PUSH OK pushid=%s" % d.get("data", {}).get("pushid"))


def main():
    try:
        page = fetch(TRENDING_URL)
    except Exception as e:
        print("FETCH FAILED:", repr(e))
        sys.exit(1)
    repos = parse_trending(page)
    if len(repos) < 3:
        print("PARSE FAILED: 只解析到 %d 个仓库，页面结构可能变了" % len(repos))
        sys.exit(1)
    repos = repos[:8]
    for r in repos:
        print("PARSED:", r["name"], r["stars"], "+" + r["today"], r["lang"])
    title, desp = build_desp(repos)
    print("---TITLE---")
    print(title)
    push(title, desp)


if __name__ == "__main__":
    main()
