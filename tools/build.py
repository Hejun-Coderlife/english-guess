#!/usr/bin/env python3
"""把 data/curated/*.json 合并成 data/videos.js（script 标签加载，双击/本地服务器都能读）"""
import json, random
from pathlib import Path
D = Path(__file__).resolve().parent.parent / "data"
vids = [json.loads(p.read_text()) for p in sorted((D / "curated").glob("*.json"))]
for v in vids:
    assert v["lines"] and v["questions"], v["id"]
    for q in v["questions"]:
        assert 0 <= q["answer"] < len(q["options"]), (v["id"], q["q"])
        # 选项顺序按题目内容固定打乱，避免正确答案总在同一个位置
        right = q["options"][q["answer"]]
        random.Random(v["id"] + q["q"]).shuffle(q["options"])
        q["answer"] = q["options"].index(right)
vids.sort(key=lambda v: (-v.get("visual", 0), v["seconds"]))
(D / "videos.js").write_text("window.VIDEO_DATA=" + json.dumps({"videos": vids}, ensure_ascii=False) + ";\n")
print(f"写入 {len(vids)} 个视频")
