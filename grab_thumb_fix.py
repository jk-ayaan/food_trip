#!/usr/bin/env python3
"""썸네일 정비: ① 깨진 이미지 URL 전수 검사 후 비움 ② 빈 곳을 카카오맵
플레이스 대표사진으로 재매칭(다중 검색어 + 이름·행정구 검증, 채택 전 로드 확인)."""
import concurrent.futures as cf
import json, os, re, sys, time, urllib.parse, urllib.request

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"
ALL_FILES = [f"data/busan/{s}.json" for s in ("sights", "food", "usulleng", "festival", "stay", "shopping")] + [
    f"data/{r}/{s}.json"
    for r in ("suwon", "ansan", "pangyo", "jeongja", "seohyeon")
    for s in ("sights", "food", "festival", "stay", "shopping")
]
KAKAO_TARGETS = ["data/busan/usulleng.json"] + [f for f in ALL_FILES if "busan" not in f]

digits = lambda s: re.sub(r"\D", "", str(s or ""))
norm = lambda s: re.sub(r"[\s()\[\]·.-]", "", str(s or ""))


def url_alive(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=12) as f:
            if getattr(f, "status", 200) != 200:
                return False
            return bool(f.read(64))
    except Exception:
        return False


def get(url, referer):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": referer})
    for _ in range(3):
        try:
            with urllib.request.urlopen(req, timeout=20) as f:
                return f.read().decode("utf-8", "ignore")
        except Exception:
            time.sleep(0.8)
    return ""


def search_places(query):
    url = "https://search.map.kakao.com/mapsearch/map.daum?q=" + urllib.parse.quote(query) + "&msFlag=A&sort=0"
    try:
        return json.loads(get(url, "https://map.kakao.com/")).get("place", []) or []
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
    if "kakaocdn.net/cthumb" not in img and "fname=" not in img:
        return ""
    return img


def norm_addr(s):
    s = str(s or "")
    for a, b in (("부산광역시", "부산"), ("울산광역시", "울산"), ("경상남도", "경남"), ("경기도", "경기")):
        s = s.replace(a, b)
    return re.sub(r"\s+", "", s)


def road_token(addr):
    m = re.search(r"([가-힣A-Za-z0-9]+(?:로|길)(?:\s*\d+(?:번길)?)?)\s*(\d+(?:-\d+)?)?", str(addr or ""))
    return re.sub(r"\s+", "", (m.group(0) if m else ""))


def district_tokens(row):
    """행정구 검증용 토큰: '수원시 팔달구'→['팔달구'], '경남 진주시'→['진주시'], '중구'→['중구']"""
    parts = str(row.get("district", "")).split()
    return [p for p in parts if p.endswith(("구", "군", "시"))][-1:] or parts[-1:]


def queries(path, row):
    name, d = row["name_ko"], str(row.get("district", ""))
    if "busan" in path and " " not in d:
        d = f"부산 {d}"
    region = d.split()[0] if d else ""
    qs = [f"{name} {d}", f"{name} {region}", name]
    return list(dict.fromkeys(q.strip() for q in qs if q.strip()))


def pick(row, places):
    tel = digits(row.get("phone"))
    my_road = road_token(row.get("i18n", {}).get("ko", {}).get("address"))
    my_name = norm(row["name_ko"])
    dts = district_tokens(row)
    for p in places:
        k_addr = norm_addr(p.get("new_address") or p.get("address"))
        k_name = norm(p.get("name"))
        d_ok = any(t in k_addr for t in dts)
        tel_ok = tel and digits(p.get("tel")) == tel
        road_ok = my_road and len(my_road) >= 4 and my_road in k_addr
        name_ok = my_name and k_name and (my_name in k_name or k_name in my_name)
        if tel_ok or (d_ok and (road_ok or name_ok)):
            return p
    return None


# ── 1단계: 깨진 썸네일 전수 검사 ──
print("1) 썸네일 URL 전수 검사...", flush=True)
dead_total = 0
for path in ALL_FILES:
    if not os.path.exists(path):
        continue
    rows = json.load(open(path, encoding="utf-8"))
    withthumb = [r for r in rows if r.get("thumb")]
    if not withthumb:
        continue
    dead = 0
    with cf.ThreadPoolExecutor(8) as ex:
        for r, ok in zip(withthumb, ex.map(lambda r: url_alive(r["thumb"]), withthumb)):
            if not ok:
                r["thumb"] = ""
                dead += 1
    if dead:
        json.dump(rows, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        dead_total += dead
    print(f"  {path}: {len(withthumb)}개 중 깨짐 {dead}", flush=True)
print(f"깨진 썸네일 {dead_total}개 비움\n", flush=True)

# ── 2단계: 빈 썸네일 카카오 재매칭 ──
print("2) 카카오맵 대표사진 재매칭...", flush=True)
total = 0
for path in KAKAO_TARGETS:
    if not os.path.exists(path):
        continue
    rows = json.load(open(path, encoding="utf-8"))
    missing = [r for r in rows if not r.get("thumb") and r.get("name_ko")]
    if not missing:
        continue
    fixed = 0
    for r in missing:
        img = ""
        for q in queries(path, r):
            p = pick(r, search_places(q))
            time.sleep(0.35)
            if p and p.get("confirmid"):
                img = og_image(p["confirmid"])
                time.sleep(0.35)
                if img and url_alive(img):
                    break
                img = ""
        if img:
            r["thumb"] = img
            fixed += 1
    if fixed:
        json.dump(rows, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        total += fixed
    print(f"  {path}: 빈 {len(missing)} → 매칭 {fixed}", flush=True)

print(f"\n대표사진 {total}곳 추가 · 깨진 URL {dead_total}개 정리", flush=True)
