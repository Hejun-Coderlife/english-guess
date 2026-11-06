#!/usr/bin/env python3
"""第二轮补搜：更多场景 + 更多剧/动画，合并进 work/candidates.json"""
import json, sys
import search as S

QUERIES = [
 ("餐厅点餐","coffee shop order scene clip"),("餐厅点餐","waiter restaurant comedy sketch"),
 ("酒店","hotel front desk scene comedy"),("机场","airport security scene comedy clip"),
 ("机场","flight attendant airplane scene clip"),("看医生","hospital scene comedy clip"),
 ("看医生","dentist scene comedy clip"),("购物","supermarket scene comedy clip"),
 ("购物","car dealership scene movie clip"),("问路/开车","driving lesson scene comedy"),
 ("问路/开车","taxi ride scene movie clip"),("初次约会","blind date scene comedy clip"),
 ("求婚/婚礼","marriage proposal scene movie clip"),("求婚/婚礼","wedding scene comedy clip"),
 ("搬家/租房","moving day scene comedy clip"),("搬家/租房","apartment tour scene comedy"),
 ("学校","first day of school scene movie clip"),("学校","school principal office scene clip"),
 ("运动","gym workout scene comedy clip"),("运动","coach locker room scene clip"),
 ("宠物","dog scene comedy movie clip"),("厨房做饭","baking scene comedy clip"),
 ("生日/派对","birthday party scene comedy clip"),("家庭晚餐","thanksgiving dinner scene clip"),
 ("广告","super bowl commercial funny"),("广告","funniest commercials 2024"),
 ("动画","Bluey episode clip"),("动画","Despicable Me minions clip"),("动画","Ice Age scene clip"),
 ("动画","Moana scene clip"),("动画","Encanto scene clip"),("动画","Turning Red clip"),
 ("动画","Luca clip Pixar"),("动画","Ratatouille clip"),("动画","Up Pixar clip"),
 ("动画","Finding Nemo clip"),("动画","How to Train Your Dragon clip"),("动画","Kung Fu Panda clip"),
 ("动画","The Bad Guys movie clip"),("动画","Puss in Boots The Last Wish clip"),
 ("美剧","Young Sheldon scene"),("美剧","The Big Bang Theory scene"),("美剧","Abbott Elementary clip"),
 ("美剧","New Girl scene clip"),("美剧","How I Met Your Mother scene"),("美剧","Schitt's Creek scene"),
 ("美剧","Fresh Off the Boat clip"),("美剧","Mr Bean"),
]
S.QUERIES = QUERIES
old = json.loads(S.OUT.read_text())
seen = {r["id"] for r in old}
S.main()
new = json.loads(S.OUT.read_text())
merged = old + [r for r in new if r["id"] not in seen]
S.OUT.write_text(json.dumps(merged, ensure_ascii=False, indent=1))
print("合并后", len(merged), "通过", sum(1 for r in merged if not r["reject"]), file=sys.stderr)
