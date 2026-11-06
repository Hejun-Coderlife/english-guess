#!/usr/bin/env python3
"""从粗筛结果挑官方/稳定频道 → 下载英文字幕 → 算语速、对白特征，输出 work/shortlist.json"""
import json, re, subprocess, sys
from collections import Counter, defaultdict
from pathlib import Path

W = Path(__file__).resolve().parent.parent / "work"
SUBS = W / "subs"
SUBS.mkdir(exist_ok=True)

# 官方或长期稳定的片段频道（转载号容易被下架，不收）
OFFICIAL = re.compile(r"^(Movieclips|The Office|TBS|Parks and Recreation|Brooklyn Nine-Nine|Disney Kids|Superstore|"
                      r"Rotten Tomatoes.*|Friends|DreamWorks.*|Peacock|Pixar|JoBlo.*|Prime Video|Still Watching Netflix|Netflix|"
                      r"Modern Family Clips|StudiocanalUK|Saturday Night Live|FX Networks|Netflix Is A Joke|Disney|"
                      r"Universal Pictures|BBC|HBO Max|Disney Jr\.|Comedy Central.*|Sony Pictures.*|Warner Bros.*|"
                      r"Illumination|Paramount.*|Lionsgate.*|ABC|NBC|FOX|Apple TV|Hulu|20th Century Studios|"
                      r"Entertainment Access|Binge Society|The Simpsons|Animation Domination|Adult Swim|Cartoon Network|"
                      r"Nickelodeon|Sesame Street|Bluey.*|Peppa Pig.*|Timeless Moments)$")

d = [r for r in json.loads((W / "candidates.json").read_text()) if not r["reject"]]
pool = [r for r in d if OFFICIAL.match(r["channel"].strip()) and r["views"] >= 100_000]
pool.sort(key=lambda r: -r["views"])
per = Counter()
short = []
for r in pool:
    if per[r["channel"]] >= 14:
        continue
    per[r["channel"]] += 1
    short.append(r)
print(f"官方频道候选 {len(pool)} → 每频道最多14条后 {len(short)}", file=sys.stderr)

need = [r["id"] for r in short if not list(SUBS.glob(r["id"] + ".*"))]
if need:
    urls = [f"https://www.youtube.com/watch?v={i}" for i in need]
    subprocess.run(["yt-dlp", "--skip-download", "--write-subs", "--write-auto-subs", "--ignore-errors",
                    "--sub-langs", "en,en-US,en-GB,en-orig", "--sub-format", "json3", "-q", "--no-warnings",
                    "--sleep-subtitles", "1", "-o", str(SUBS / "%(id)s"), *urls])


def load_sub(vid):
    files = sorted(SUBS.glob(vid + ".*.json3"), key=lambda p: ("orig" in p.name, p.name))  # 人工字幕优先
    for f in files:
        try:
            ev = json.loads(f.read_text()).get("events", [])
        except Exception:
            continue
        lines = []
        for e in ev:
            t = "".join(s.get("utf8", "") for s in e.get("segs", []) or []).strip()
            if t and t != "\n":
                lines.append({"t": round(e.get("tStartMs", 0) / 1000, 1), "text": t.replace("\n", " ")})
        if lines:
            return lines, ("auto" if "orig" in f.name else "manual")
    return [], None


out = []
for r in short:
    lines, kind = load_sub(r["id"])
    text = " ".join(l["text"] for l in lines)
    words = len(re.findall(r"[A-Za-z']+", text))
    r = r | {"sub_kind": kind, "words": words, "wpm": round(words / max(r["seconds"], 1) * 60),
             "questions": text.count("?"), "music_tags": len(re.findall(r"\[(music|Music|MUSIC)\]", text)),
             "lines": lines}
    out.append(r)
(W / "shortlist.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
has = [r for r in out if r["words"] > 0]
print(f"有字幕 {len(has)}/{len(out)}", file=sys.stderr)
