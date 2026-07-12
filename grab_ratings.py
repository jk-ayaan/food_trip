#!/usr/bin/env python3
"""카카오맵 별점 매칭 (지역 인자: busan suwon ansan pangyo jeongja seohyeon, 생략 시 전부).
검색 결과의 lat/lon으로 300m 이내 + 이름 유사(또는 전화 일치)만 채택.
rating(별점)·rcount(평가수) 필드 저장, 썸네일 없으면 검색 img로 보충."""
import json, math, os, re, sys, time, urllib.parse, urllib.request

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"
SIDO = {"seoul": "서울", "incheon": "인천", "daejeon": "대전", "daegu": "대구",
        "gwangju": "광주", "ulsan": "울산", "sejong": "세종", "gyeonggi": "경기",
        "gangwon": "강원", "chungbuk": "충북", "chungnam": "충남", "gyeongbuk": "경북",
        "gyeongnam": "경남", "jeonbuk": "전북", "jeonnam": "전남", "jeju": "제주"}
REGION_FILES = {
    "busan": [f"data/busan/{s}.json" for s in ("food", "usulleng", "sights", "stay", "shopping")],
    **{r: [f"data/{r}/{s}.json" for s in ("food", "sights", "stay", "shopping", "festival")]
       for r in ("suwon", "ansan", "pangyo", "jeongja", "seohyeon")},
    **{r: [f"data/{r}/food.json"] for r in SIDO},  # 전국 시·도는 음식만
}
regions = [a for a in sys.argv[1:] if a in REGION_FILES] or list(REGION_FILES)
TARGETS = [f for r in regions for f in REGION_FILES[r]]

digits = lambda s: re.sub(r"\D", "", str(s or ""))
norm = lambda s: re.sub(r"[\s()\[\]·.-]", "", str(s or ""))


def hav(la1, lo1, la2, lo2):
    R, d = 6371, math.radians
    a = math.sin(d(la2 - la1) / 2) ** 2 + math.cos(d(la1)) * math.cos(d(la2)) * math.sin(d(lo2 - lo1) / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def search(query):
    url = "https://search.map.kakao.com/mapsearch/map.daum?q=" + urllib.parse.quote(query) + "&msFlag=A&sort=0"
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": "https://map.kakao.com/"})
    for _ in range(3):
        try:
            with urllib.request.urlopen(req, timeout=20) as f:
                return json.loads(f.read().decode("utf-8", "ignore")).get("place", []) or []
        except Exception:
            time.sleep(0.8)
    return []


def pick(row, places):
    """전화 일치 > 300m 이내+이름 유사 > 300m 이내(유일 후보)."""
    tel = digits(row.get("phone"))
    my_name = norm(row["name_ko"])
    near = []
    for p in places:
        if tel and digits(p.get("tel")) == tel:
            return p
        try:
            dk = hav(float(row["lat"]), float(row["lng"]), float(p["lat"]), float(p["lon"]))
        except (TypeError, ValueError, KeyError):
            continue
        if dk <= 0.3:
            near.append(p)
    for p in near:
        k = norm(p.get("name"))
        if my_name and k and (my_name in k or k in my_name):
            return p
    return near[0] if len(near) == 1 else None


total_rated, total_img = 0, 0
for path in TARGETS:
    if not os.path.exists(path):
        continue
    rows = json.load(open(path, encoding="utf-8"))
    rated = imgs = 0
    for r in rows:
        if not r.get("name_ko"):
            continue
        d = str(r.get("district", ""))
        reg = path.split("/")[1]
        if " " not in d:  # 시·도명 보강 (동명 구·군 오매칭 방지)
            if reg == "busan":
                d = f"부산 {d}"
            elif reg in SIDO:
                d = f"{SIDO[reg]} {d}"
        p = pick(r, search(f"{r['name_ko']} {d}")) or pick(r, search(r["name_ko"]))
        time.sleep(0.3)
        if not p:
            continue
        ra, rc = p.get("rating_average"), p.get("rating_count")
        if isinstance(ra, (int, float)) and ra > 0 and isinstance(rc, int) and rc > 0:
            r["rating"], r["rcount"] = round(float(ra), 1), rc
            rated += 1
        if not r.get("thumb") and p.get("img"):
            img = str(p["img"])
            r["thumb"] = "https://" + img[7:] if img.startswith("http://") else img
            imgs += 1
    json.dump(rows, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    total_rated += rated
    total_img += imgs
    print(f"{path}: {len(rows)}곳 중 별점 {rated} · 썸네일 보충 {imgs}", flush=True)

print(f"\n별점 {total_rated}곳 · 썸네일 {total_img}곳 추가", flush=True)
