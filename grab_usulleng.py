#!/usr/bin/env python3
"""우슐랭(jk-ayaan/usulleng) restaurants.json → data/usulleng.json 변환.
부산지방우정청 「우체국 추천 맛집가이드」(2024·2025) 부산·울산·경남 맛집."""
import json, urllib.request

SRC = "https://raw.githubusercontent.com/jk-ayaan/usulleng/main/data/restaurants.json"

with urllib.request.urlopen(SRC) as f:
    rows = json.load(f)

out = []
for r in rows:
    district = r["district"] if r["region"] == "부산" else f'{r["region"]} {r["district"]}'
    out.append({
        "section": "usulleng",
        "name_ko": r["name"],
        "district": district,
        "category": r["category"],
        "lat": r["lat"], "lng": r["lng"],
        "phone": r.get("phone", ""),
        "office": r.get("office", ""),
        "editions": "·".join(e[2:] for e in r.get("editions", [])),  # "24·25"
        "i18n": {"ko": {
            "name": r["name"],
            "desc": r.get("desc", ""),
            "menu": r.get("menu", ""),
            "address": r.get("addr", ""),
            "hours": r.get("hours", ""),
        }},
    })

with open("data/busan/usulleng.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print(f"data/busan/usulleng.json 저장: {len(out)}곳")
