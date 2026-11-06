#!/usr/bin/env python3
"""合并成 data/videos.js（script 标签加载）
视频列表 = work/selected.json（select.py 选出的）；data/curated/<id>.json 里有题目的视频会带上题目和原文"""
import json, random
from pathlib import Path

R = Path(__file__).resolve().parent.parent
D = R / "data"
sel = json.loads((R / "work/selected.json").read_text())
curated = {p.stem: json.loads(p.read_text()) for p in (D / "curated").glob("*.json")}

out = []
for s in sel:
    v = {k: s[k] for k in ("id", "title", "channel", "seconds", "scene", "published")}
    c = curated.get(s["id"])
    if c:
        v |= {k: c[k] for k in ("summary", "lines", "questions") if k in c}
        for q in v["questions"]:
            assert 0 <= q["answer"] < len(q["options"]), (v["id"], q["q"])
            right = q["options"][q["answer"]]
            q["options"] = q["options"][:]
            random.Random(v["id"] + q["q"]).shuffle(q["options"])   # 打乱选项，正确答案不固定位置
            q["answer"] = q["options"].index(right)
    out.append(v)

(D / "videos.js").write_text("window.VIDEO_DATA=" + json.dumps({"videos": out}, ensure_ascii=False) + ";\n")
print(f"写入 {len(out)} 个视频（其中带题目 {sum(1 for v in out if v.get('questions'))} 个）")
