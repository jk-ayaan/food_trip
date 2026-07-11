#!/usr/bin/env python3
"""썸네일 없는 항목만 카카오맵 플레이스 대표사진(og:image)으로 채움.
검색(이름+지역) → 전화번호 또는 도로명주소 일치 검증 → place 페이지 og:image.
기존 thumb가 있는 항목은 건드리지 않음."""
import json, os, re, sys, time, urllib.parse, urllib.request

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"
TARGETS = ["data/busan/usulleng.json"] + [
    f"data/{reg}/{sec}.json"
    for reg in ("suwon", "ansan", "pangyo", "jeongja", "seohyeon")
    for sec in ("sights", "food", "festival", "stay", "shopping")
]

digits = lambda s: re.sub(r"\D", "", str(s or ""))


def norm_addr(s):
    s = str(s or "")
    for a, b in (("부산광역시", "부산"), ("울산광역시", "울산"), ("경상남도", "경남"), ("경기도", "경기")):
        s = s.replace(a, b)
    return re.sub(r"\s+", "", s)


def road_token(addr):
    """도로명+건물번호 토큰 추출 (예: 대청로137번길7-2)."""
    m = re.search(r"([가-힣A-Za-z0-9]+(?:로|길)(?:\s*\d+(?:번길)?)?)\s*(\d+(?:-\d+)?)?", str(addr or ""))
    return re.sub(r"\s+", "", (m.group(0) if m else ""))


def get(url, referer):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": referer})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=20) as f:
                return f.read().decode("utf-8", "ignore")
        except Exception:
            time.sleep(1.0)
    return ""


def search_places(query):
    url = "https://search.map.kakao.com/mapsearch/map.daum?q=" + urllib.parse.quote(query) + "&msFlag=A&sort=0"
    body = get(url, "https://map.kakao.com/")
    try:
        return json.loads(body).get("place", []) or []
    except json.JSONDecodeError:
        return []


def og_image(place_id):
    html = get(f"https://place.map.kakao.com/{place_id}", "https://map.kakao.com/")
    m = re.search(r'<meta property="og:image" content="([^"]+)"', html)
    if not m:
        return ""
    img = m.group(1)
    if img.startswith("//"):
        img = "https:" + img
    # 사진 미등록 시 기본 아이콘류(daumcdn 정적 에셋)는 제외 — 실제 등록 사진만
    if "kakaocdn.net/cthumb" not in img and "fname=" not in img:
        return ""
    return img


def region_query(path, row):
    d = str(row.get("district", ""))
    if "busan" in path and " " not in d:
        return f'{row["name_ko"]} 부산 {d}'
    return f'{row["name_ko"]} {d}'


def match(row, places):
    """전화번호 일치 최우선, 없으면 도로명주소 토큰 일치."""
    tel = digits(row.get("phone"))
    my_road = road_token(row.get("i18n", {}).get("ko", {}).get("address"))
    my_addr = norm_addr(row.get("i18n", {}).get("ko", {}).get("address"))
    by_road = None
    for p in places:
        if tel and digits(p.get("tel")) == tel:
            return p
        k_addr = norm_addr(p.get("new_address") or p.get("address"))
        if by_road is None and my_road and len(my_road) >= 4 and my_road in k_addr:
            by_road = p
        elif by_road is None and my_addr and len(my_addr) >= 10 and (my_addr in k_addr or k_addr[:14] == my_addr[:14] != ""):
            by_road = p
    return by_road


total = 0
for path in TARGETS:
    if not os.path.exists(path):
        continue
    rows = json.load(open(path, encoding="utf-8"))
    missing = [r for r in rows if not r.get("thumb")]
    if not missing:
        continue
    fixed = 0
    for r in missing:
        if not r.get("name_ko"):
            continue
        p = match(r, search_places(region_query(path, r)))
        time.sleep(0.4)
        if not p or not p.get("confirmid"):
            continue
        img = og_image(p["confirmid"])
        time.sleep(0.4)
        if img:
            r["thumb"] = img
            fixed += 1
    if fixed:
        json.dump(rows, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        total += fixed
    print(f"{path}: 빈 썸네일 {len(missing)} → 대표사진 {fixed}", flush=True)

print(f"\n총 {total}곳 대표사진 추가")
