#!/usr/bin/env python3
"""把字幕碎片拼成句子，输出 work/prep/<id>.json（lines: [{t, en}]），并打印编号文本供出题
用法: python3 prep.py id1 id2 ...   (不带参数=处理 picks 里还没做的)"""
import json, re, sys
from pathlib import Path

R = Path(__file__).resolve().parent.parent
SUBS, PREP = R / "work/subs", R / "work/prep"
PREP.mkdir(exist_ok=True)
NOISE = re.compile(r"^\s*[\[\(（][^\]\)）]*[\]\)）]\s*$|^>>\s*$|^foreign$", re.I)


def events(vid):
    files = sorted(SUBS.glob(vid + ".*.json3"), key=lambda p: ("orig" in p.name, p.name))
    for f in files:
        try:
            ev = json.loads(f.read_text()).get("events", [])
        except Exception:
            continue
        out = []
        for e in ev:
            t = "".join(s.get("utf8", "") for s in e.get("segs") or []).replace("\n", " ").strip()
            t = re.sub(r"\s+", " ", t)
            if t and not NOISE.match(t):
                out.append((e.get("tStartMs", 0) / 1000, (e.get("tStartMs", 0) + e.get("dDurationMs", 0)) / 1000, t))
        if out:
            return out, "orig" in f.name
    return [], False


def merge(ev, auto):
    lines, cur, start, last_end = [], [], None, 0
    for s, e, t in ev:
        t = re.sub(r"^>>\s*", "", re.sub(r"\[[^\]]*\]", "", t)).strip()
        if not t:
            continue
        gap = s - last_end
        words = sum(len(x.split()) for x in cur)
        if cur and (gap > 1.2 or words >= 22 or (not auto and re.search(r"[.?!]['\"]?$", cur[-1]) and words >= 4)):
            lines.append({"t": round(start, 1), "en": " ".join(cur)})
            cur = []
        if not cur:
            start = s
        cur.append(t)
        last_end = max(e, s)
    if cur:
        lines.append({"t": round(start, 1), "en": " ".join(cur)})
    return lines


def main(ids):
    for vid in ids:
        ev, auto = events(vid)
        lines = merge(ev, auto)
        (PREP / f"{vid}.json").write_text(json.dumps({"auto": auto, "lines": lines}, ensure_ascii=False))
        print(f"### {vid} {'AUTO' if auto else 'MANUAL'} {len(lines)}")
        for i, l in enumerate(lines):
            print(f"{i}|{l['t']}|{l['en']}")


if __name__ == "__main__":
    ids = sys.argv[1:]
    if not ids:
        sys.path.insert(0, str(R / "tools"))
        from picks import PICKS
        done = {p.stem for p in (R / "data/curated").glob("*.json")}
        ids = [p[0] for p in PICKS if p[0] not in done]
    main(ids)
