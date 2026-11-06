#!/usr/bin/env python3
"""第一轮粗筛：按场景搜 YouTube，过滤时长/年份/可嵌入/非教学频道，输出 work/candidates.json"""
import json, re, subprocess, sys, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "work" / "candidates.json"
KEY = subprocess.check_output(["security", "find-generic-password", "-s", "youtube-api", "-w"], text=True).strip()
API = "https://www.googleapis.com/youtube/v3/"

# (场景, 搜索词)
QUERIES = [
    ("餐厅点餐", "restaurant ordering scene movie clip"),
    ("餐厅点餐", "diner waitress scene clip"),
    ("机场", "airport scene movie clip"),
    ("酒店", "hotel check in scene movie clip"),
    ("求职面试", "job interview scene movie clip"),
    ("吵架", "couple argument scene movie clip"),
    ("看医生", "doctor appointment scene comedy clip"),
    ("购物", "shopping store clerk scene clip"),
    ("问路/开车", "car ride scene comedy clip"),
    ("初次约会", "first date scene movie clip"),
    ("道歉", "apology scene movie clip"),
    ("家庭晚餐", "family dinner scene comedy clip"),
    ("办公室", "the office scene clip"),
    ("办公室", "office meeting scene comedy clip"),
    ("警察", "pulled over by police scene comedy clip"),
    ("生日/派对", "surprise party scene clip"),
    ("搞砸了", "awkward moment scene comedy clip"),
    ("找东西", "looking for lost keys scene clip"),
    ("学校", "classroom scene movie clip"),
    ("厨房做饭", "cooking disaster scene comedy clip"),
    ("动画", "Pixar movie clip scene"),
    ("动画", "Disney animation movie clip"),
    ("动画", "DreamWorks movie clip scene"),
    ("动画", "Toy Story clip"),
    ("动画", "Shrek scene clip"),
    ("动画", "Zootopia clip"),
    ("动画", "Inside Out clip"),
    ("动画", "The Simpsons clip"),
    ("美剧", "Friends scene clip"),
    ("美剧", "Modern Family scene clip"),
    ("美剧", "Brooklyn Nine-Nine scene clip"),
    ("美剧", "Parks and Recreation scene clip"),
    ("美剧", "Superstore scene clip"),
    ("美剧", "Ted Lasso scene clip"),
    ("广告", "funny commercial ad"),
]

BAD_CHANNEL = re.compile(r"english|esl|learn|lesson|teacher|ielts|toefl|vocabulary|grammar|accent|英语|英文|学习", re.I)
BAD_TITLE = re.compile(r"learn english|english lesson|with subtitles|英语|英文|reaction|reacts|review|explained|breakdown|interview with|podcast|trailer|teaser|compilation|full movie|#shorts", re.I)


def get(endpoint, **params):
    params["key"] = KEY
    url = API + endpoint + "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.load(r)


def iso_seconds(d):
    m = re.fullmatch(r"P(?:\d+D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", d)
    if not m:
        return 0
    h, mi, s = (int(x or 0) for x in m.groups())
    return h * 3600 + mi * 60 + s


def main():
    found = {}
    for scene, q in QUERIES:
        for dur in ("short", "medium"):
            res = get("search", part="snippet", q=q, type="video", maxResults=25,
                      videoDuration=dur, videoEmbeddable="true", relevanceLanguage="en",
                      publishedAfter="2016-01-01T00:00:00Z", safeSearch="moderate")
            for it in res.get("items", []):
                vid = it["id"]["videoId"]
                found.setdefault(vid, {"id": vid, "scene": scene, "query": q})
        print(f"{scene:8} {q:45} 累计 {len(found)}", file=sys.stderr)

    ids = list(found)
    out = []
    for i in range(0, len(ids), 50):
        res = get("videos", part="snippet,contentDetails,status,statistics", id=",".join(ids[i:i + 50]))
        for v in res.get("items", []):
            sn, cd, st = v["snippet"], v["contentDetails"], v["status"]
            sec = iso_seconds(cd["duration"])
            lang = (sn.get("defaultAudioLanguage") or sn.get("defaultLanguage") or "en").lower()
            reason = None
            if not 45 <= sec <= 300: reason = "时长"
            elif not st.get("embeddable"): reason = "不可嵌入"
            elif st.get("privacyStatus") != "public": reason = "非公开"
            elif sn["publishedAt"] < "2016": reason = "太旧"
            elif not lang.startswith("en"): reason = f"语言{lang}"
            elif BAD_CHANNEL.search(sn["channelTitle"]): reason = "教学频道"
            elif BAD_TITLE.search(sn["title"]): reason = "标题排除"
            blocked = cd.get("regionRestriction", {}).get("blocked", [])
            if "US" in blocked or "JP" in blocked: reason = reason or "地区限制"
            rec = found[v["id"]] | {
                "title": sn["title"], "channel": sn["channelTitle"], "channelId": sn["channelId"],
                "published": sn["publishedAt"][:10], "seconds": sec,
                "views": int(v.get("statistics", {}).get("viewCount", 0)),
                "caption": cd.get("caption") == "true",
                "description": sn.get("description", "")[:300],
                "thumb": f"https://i.ytimg.com/vi/{v['id']}/mqdefault.jpg",
                "reject": reason,
            }
            out.append(rec)
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1))
    keep = [r for r in out if not r["reject"]]
    print(f"共 {len(out)} 条，粗筛通过 {len(keep)} 条", file=sys.stderr)
    from collections import Counter
    print(Counter(r["reject"] for r in out), file=sys.stderr)


if __name__ == "__main__":
    main()
