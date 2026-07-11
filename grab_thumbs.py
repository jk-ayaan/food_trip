#!/usr/bin/env python3
"""썸네일 없는 항목에 TourAPI searchKeyword2로 이미지 매칭.
이름 검색 → 좌표 1.5km 이내(또는 정확히 같은 이름)만 채택해 오매칭 방지.
대상: data/busan/usulleng.json + 경기 지역 전체(thumb 빈 항목만)."""
import json, math, os, re, sys, time, urllib.parse, urllib.request

KEY = os.environ.get("TOURAPI_KEY", "").strip()
if not KEY:
    raise SystemExit("오류: 환경변수 TOURAPI_KEY가 없습니다.")
KEY = urllib.parse.unquote(KEY)

BASE = "https://apis.data.go.kr/B551011/KorService2/searchKeyword2"
TARGETS = ["data/busan/usulleng.json"] + [
    f"data/{reg}/{sec}.json"
    for reg in ("suwon", "ansan", "pangyo", "jeongja", "seohyeon")
    for sec in ("sights", "food", "festival", "stay", "shopping")
]


def area_of(path, row):
    """행정구역 → TourAPI areaCode (부산6 · 울산7 · 경남36 · 경기31)."""
    if "busan" not in path:
        return "31"
    d = row.get("district", "")
    if d.startswith("울산"):
        return "7"
    if d.startswith("경남"):
        return "36"
    return "6"


def hav(la1, lo1, la2, lo2):
    R, d = 6371, math.radians
    a = math.sin(d(la2 - la1) / 2) ** 2 + math.cos(d(la1)) * math.cos(d(la2)) * math.sin(d(lo2 - lo1) / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def search(name, area):
    q = {"serviceKey": KEY, "MobileOS": "ETC", "MobileApp": "foodtrip", "_type": "json",
         "numOfRows": 10, "pageNo": 1, "keyword": name, "areaCode": area, "arrange": "A"}
    url = BASE + "?" + urllib.parse.urlencode(q)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "foodtrip/1.0"}), timeout=20) as f:
                p = json.load(f)
            body = p.get("response", {}).get("body", {})
            items = (body.get("items") or {}).get("item") or []
            return [items] if isinstance(items, dict) else items
        except Exception:
            time.sleep(0.5)
    return []


norm = lambda s: re.sub(r"\s+", "", str(s or ""))

total_fixed = 0
for path in TARGETS:
    if not os.path.exists(path):
        continue
    rows = json.load(open(path, encoding="utf-8"))
    missing = [r for r in rows if not r.get("thumb")]
    if not missing:
        continue
    fixed = 0
    for r in missing:
        name = r.get("name_ko", "")
        if not name:
            continue
        best, best_d = None, 9e9
        for it in search(name, area_of(path, r)):
            img = it.get("firstimage2") or it.get("firstimage")
            if not img:
                continue
            same = norm(it.get("title")) == norm(name)
            try:
                dk = hav(float(r["lat"]), float(r["lng"]), float(it["mapy"]), float(it["mapx"]))
            except (TypeError, ValueError, KeyError):
                dk = None
            # 좌표 1.5km 이내이거나, 좌표 불명이면 이름이 정확히 같아야 채택
            if dk is not None and dk <= 1.5:
                if dk < best_d:
                    best, best_d = img, dk
            elif dk is None and same:
                best, best_d = img, 0
        if best:
            if best.startswith("http://"):
                best = "https://" + best[7:]
            r["thumb"] = best
            fixed += 1
        time.sleep(0.15)
    if fixed:
        json.dump(rows, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        total_fixed += fixed
    print(f"{path}: 빈 썸네일 {len(missing)} → 매칭 {fixed}")

print(f"\n총 {total_fixed}곳 이미지 추가")
