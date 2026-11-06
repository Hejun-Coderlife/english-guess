#!/usr/bin/env python3
"""从 shortlist 自动选出约 160 个视频 → work/selected.json
规则：有对白（语速 35~170 词/分）、配乐不压对白、5 分钟内、排除唱歌/讲座/暴力/重复，每个频道最多 15 个
先放人工初选的 picks，再按规则补足"""
import json, re, sys
from collections import Counter
from pathlib import Path

R = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R / "tools"))
from picks import PICKS

TARGET = 160
PER_CHANNEL = 15
BAD = re.compile(r"song|sing|music|lyric|dance|montage|monologue|stand-?up|podcast|interview|weekend update|explained|"
                 r"behind the scenes|bloopers|cast |kill|murder|shoot|gun|dead|blood|tortur|fight|battle|war\b|"
                 r"full episode|episode \d+ full|compilation|best of|moments|trailer|teaser|first look|script to screen|#shorts", re.I)
DROP_PICKS = {"HQloEkUc_fU"}  # 实际是混剪预告，不是完整场景
SCENE_FIX = {"X8PsYhkLDhU": "办公室"}  # 实际是警局晨会

short = {r["id"]: r for r in json.loads((R / "work/shortlist.json").read_text())}


def ok(r):
    if not r.get("words") or not 45 <= r["seconds"] <= 300:
        return False
    if not 35 <= r["wpm"] <= 170:
        return False
    if r["music_tags"] > max(3, len(r["lines"]) * 0.2):
        return False
    return not BAD.search(r["title"])


def key(title):  # 去重用：去掉频道后缀、括号、数字
    t = re.split(r"\s[|｜]\s", title.lower())[0]
    return re.sub(r"[^a-z]+", "", re.sub(r"\(.*?\)", "", t))[:28]


chosen, seen, per = [], set(), Counter()
for vid, scene, *_ in PICKS:
    if vid in DROP_PICKS or vid not in short:
        continue
    r = short[vid]
    chosen.append({**r, "scene": SCENE_FIX.get(vid, scene), "picked": True})
    seen.add(key(r["title"])); per[r["channel"]] += 1

pool = [r for r in short.values() if r["id"] not in {c["id"] for c in chosen} and ok(r)]
# 先近年的、播放量高的
pool.sort(key=lambda r: (r["published"] < "2020", -r["views"]))
for r in pool:
    if len(chosen) >= TARGET:
        break
    k = key(r["title"])
    if k in seen or per[r["channel"]] >= PER_CHANNEL:
        continue
    seen.add(k); per[r["channel"]] += 1
    chosen.append({**r, "picked": False})

out = [{k: c[k] for k in ("id", "title", "channel", "seconds", "scene", "published", "views", "wpm", "picked")} for c in chosen]
(R / "work/selected.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
print(f"选出 {len(out)}（人工初选 {sum(c['picked'] for c in out)}），候选池 {len(pool)}", file=sys.stderr)
print(Counter(c["scene"] for c in out).most_common(), file=sys.stderr)
print(per.most_common(12), file=sys.stderr)
