#!/usr/bin/env python3
"""生成候选清单页 review/index.html：缩略图+简介+分数，默认全选，你取消不要的"""
import json, html
from pathlib import Path
from picks import PICKS
R = Path(__file__).resolve().parent.parent
sl = {r["id"]: r for r in json.loads((R / "work/shortlist.json").read_text())}
LV = {1: "入门", 2: "中等", 3: "较难"}
cards = []
for vid, scene, lv, vis, zh in PICKS:
    r = sl[vid]
    m, s = divmod(r["seconds"], 60)
    cards.append(f'''<label class="c"><input type="checkbox" value="{vid}" checked>
<a href="https://www.youtube.com/watch?v={vid}" target="_blank"><img src="https://i.ytimg.com/vi/{vid}/mqdefault.jpg" loading="lazy"><span class="d">{m}:{s:02d}</span></a>
<div class="t">{html.escape(zh)}</div>
<div class="m"><span>{scene}</span><span>{LV[lv]}</span><span class="v">{"●"*vis}{"○"*(5-vis)}</span></div>
<div class="e">{html.escape(r["title"])}</div></label>''')
page = f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>候选清单 · {len(PICKS)} 个</title>
<style>
body{{margin:0;background:#0f0f0f;color:#f1f1f1;font:14px/1.45 -apple-system,"PingFang SC",sans-serif;padding:24px 32px 120px}}
h1{{font-size:22px;margin:0 0 4px}}p{{color:#aaa;margin:0 0 20px}}
.g{{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:22px 16px}}
.c{{display:block;cursor:pointer;border-radius:12px;padding:8px;transition:.15s}}
.c:has(input:not(:checked)){{opacity:.28}}
.c input{{width:18px;height:18px;accent-color:#f60;float:right;margin:4px 2px 0 6px}}
.c a{{display:block;position:relative;aspect-ratio:16/9;border-radius:10px;overflow:hidden;background:#222}}
.c img{{width:100%;height:100%;object-fit:cover;display:block}}
.d{{position:absolute;right:6px;bottom:6px;background:#000c;padding:1px 5px;border-radius:4px;font-size:12px}}
.t{{font-weight:500;margin-top:8px;font-size:15px}}
.m{{display:flex;gap:10px;color:#aaa;margin-top:4px;font-size:13px}}.v{{color:#f60;letter-spacing:1px}}
.e{{color:#666;font-size:12px;margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.bar{{position:fixed;left:0;right:0;bottom:0;background:#1d1d1dee;backdrop-filter:blur(8px);padding:14px 32px;display:flex;gap:14px;align-items:center}}
button{{font:inherit;border:0;border-radius:18px;padding:8px 18px;background:#f60;color:#fff;font-weight:600;cursor:pointer}}
button.s{{background:#333}}
</style>
<h1>候选清单（{len(PICKS)} 个）</h1>
<p>默认全选。<b>取消勾选你不想要的</b>，点缩略图可以在 YouTube 预览。橙色圆点 = 我估计“只看画面能懂几成”（5 = 最容易猜）。</p>
<div class="g">{"".join(cards)}</div>
<div class="bar"><span id="n"></span><span style="flex:1"></span>
<button class="s" onclick="all_(true)">全选</button><button class="s" onclick="all_(false)">全不选</button>
<button onclick="copy_()">复制结果，粘给 Claude</button></div>
<script>
const bs=[...document.querySelectorAll('input')];
const K='gt-review';const saved=JSON.parse(localStorage.getItem(K)||'null');
if(saved)bs.forEach(b=>b.checked=!saved.includes(b.value));
const upd=()=>{{document.getElementById('n').textContent=`已选 ${{bs.filter(b=>b.checked).length}} / ${{bs.length}}`;localStorage.setItem(K,JSON.stringify(bs.filter(b=>!b.checked).map(b=>b.value)))}};
bs.forEach(b=>b.onchange=upd);upd();
function all_(v){{bs.forEach(b=>b.checked=v);upd()}}
function copy_(){{const no=bs.filter(b=>!b.checked).map(b=>b.value);const t=no.length?'不要这些：'+no.join(' '):'全部都要';
navigator.clipboard.writeText(t).then(()=>alert_('已复制：'+t.slice(0,60)+(t.length>60?'…':'')))}}
function alert_(s){{document.getElementById('n').textContent=s}}
</script></html>'''
(R / "review/index.html").write_text(page)
print("写入", R / "review/index.html", len(PICKS))
