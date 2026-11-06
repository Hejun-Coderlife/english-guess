#!/usr/bin/env python3
"""并行下载 shortlist 里还没字幕的视频（3 路）"""
import subprocess, json, re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
R = Path(__file__).resolve().parent.parent
src = (R / "tools/shortlist.py").read_text().split("need = ")[0].replace("Path(__file__).resolve().parent.parent", f'Path("{R}")')
g = {}; exec(src, g)
SUBS = R / "work/subs"
done = {p.name.split(".")[0] for p in SUBS.glob("*.json3")}
need = [r["id"] for r in g["short"] if r["id"] not in done]
chunks = [need[i::3] for i in range(3)]
def run(ids):
    subprocess.run(["yt-dlp", "--skip-download", "--write-subs", "--write-auto-subs", "--ignore-errors", "--sub-langs", "en,en-US,en-GB,en-orig",
                    "--sub-format", "json3", "-q", "--no-warnings", "-o", str(SUBS / "%(id)s"), *[f"https://www.youtube.com/watch?v={i}" for i in ids]],
                   stderr=subprocess.DEVNULL)
with ThreadPoolExecutor(3) as ex: list(ex.map(run, chunks))
print("完成，剩余没字幕:", len([i for i in need if not list(SUBS.glob(i + ".*"))]))
