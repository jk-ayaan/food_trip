#!/usr/bin/env python3
"""부산 맛집 데이터 수집기 — visitbusan.net '음식' 섹션 (부산의 맛).

1) 목록 페이지(22p)에서 uc_seq / 이름 / 썸네일 / 조회·리뷰·좋아요 수집
2) 각 상세 페이지에서 주소·전화·영업시간·휴무·대표메뉴·설명 파싱
3) 키워드 기반 카테고리(음식종류) 추론
4) data.json 으로 저장
"""
import re, json, sys, time, html
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.request import Request, urlopen

BASE = "https://www.visitbusan.net"
LIST_URL = BASE + "/index.do?menuCd=DOM_000000201002000000&page_no={p}&listCntPerPage2=16&order_type=NEW"
DETAIL_URL = BASE + "/index.do?menuCd=DOM_000000201002001000&uc_seq={seq}&lang_cd=ko"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"


def fetch(url, tries=3):
    for i in range(tries):
        try:
            req = Request(url, headers={"User-Agent": UA, "Accept-Language": "ko"})
            with urlopen(req, timeout=30) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:
            if i == tries - 1:
                print(f"  ! fail {url[:80]}: {e}", file=sys.stderr)
                return ""
            time.sleep(1.5)
    return ""


def clean(s):
    s = re.sub(r"<br\s*/?>", "\n", s or "", flags=re.I)
    s = re.sub(r"<[^>]+>", "", s)
    s = html.unescape(s)
    return re.sub(r"[ \t]+", " ", s).strip()


# ---- 목록 파싱 -------------------------------------------------------------
CARD_RE = re.compile(
    r'<div class="box actionImg3">\s*<a href="[^"]*?uc_seq=(\d+)[^"]*"[^>]*>\s*'
    r'<img src="([^"]+)" alt="([^"]*)"',
    re.S,
)
STATS_RE = re.compile(
    r'uc_seq=(\d+).*?클릭수"?>\s*([\d,]+).*?리뷰수"?>\s*([\d,]+).*?좋아요"?>\s*([\d,]+)',
    re.S,
)


def parse_list(page):
    out = {}
    h = fetch(LIST_URL.format(p=page))
    if not h:
        return out
    for seq, img, name in CARD_RE.findall(h):
        img = img if img.startswith("http") else BASE + img
        out[seq] = {"seq": seq, "name": clean(name), "thumb": img}
    for seq, v, rv, lk in STATS_RE.findall(h):
        if seq in out:
            out[seq].update(views=int(v.replace(",", "")),
                            reviews=int(rv.replace(",", "")),
                            likes=int(lk.replace(",", "")))
    return out


# ---- 상세 파싱 -------------------------------------------------------------
NAME_RE = re.compile(r'<section id="title">.*?<h4 class="tit">(.*?)</h4>', re.S)
DESC_RE = re.compile(r'<div class="cont">\s*(.*?)\s*</div>', re.S)
INFO_RE = re.compile(r'<li><p>([^<]+)</p><span>(.*?)</span></li>', re.S)
MAINIMG_RE = re.compile(r"imgLoadComm\([^,]+,\s*'(\d+)'\s*,\s*'mainImgPreViewBf'")


def parse_detail(seq):
    h = fetch(DETAIL_URL.format(seq=seq))
    if not h:
        return None
    d = {"seq": seq}
    m = NAME_RE.search(h)
    if m:
        d["name"] = clean(m.group(1))
    m = DESC_RE.search(h)
    d["desc"] = clean(m.group(1)) if m else ""
    info = {clean(k): clean(v) for k, v in INFO_RE.findall(h)}
    d["menu"] = info.get("대표 메뉴", "")
    d["address"] = info.get("주소", "")
    d["phone"] = info.get("전화번호", "")
    d["closed"] = info.get("휴무일", "")
    d["hours"] = info.get("운영요일 및 시간", "")
    # 기타 라벨도 보존
    extra = {k: v for k, v in info.items()
             if k not in ("대표 메뉴", "주소", "전화번호", "휴무일", "운영요일 및 시간")}
    if extra:
        d["extra"] = extra
    return d


# ---- 카테고리 추론 ---------------------------------------------------------
CATS = [
    ("카페·베이커리", ["커피", "카페", "로스터", "베이커리", "제과", "디저트", "케이크",
                    "라떼", "에스프레소", "브런치", "빵", "도넛", "티하우스", "찻집"]),
    ("일식",        ["야키토리", "스시", "초밥", "라멘", "우동", "돈카츠", "돈가스",
                    "이자카야", "로바타", "사시미", "텐동", "오마카세", "소바", "장어덮밥"]),
    ("해산물·회",    ["회", "횟집", "해물", "해산물", "조개", "대게", "게장", "갈치",
                    "생선", "수산", "활어", "멍게", "장어", "복국", "아구", "물회",
                    "전복", "굴", "낙지", "곰장어", "꼼장어", "해녀"]),
    ("고기·구이",    ["갈비", "삼겹", "고기", "구이", "곱창", "막창", "한우", "정육",
                    "양꼬치", "불고기", "스테이크", "바베큐", "bbq", "돼지", "소고기"]),
    ("중식",        ["중화", "짜장", "짬뽕", "마라", "딤섬", "양장피", "탕수육", "중국"]),
    ("양식·세계요리", ["파스타", "피자", "버거", "비스트로", "스테이크", "타코", "쌀국수",
                    "포케", "브런치", "이탈리", "프렌치", "스페인", "다이닝", "레스토랑",
                    "퓨전", "베트남", "태국", "인도"]),
    ("분식·주점",    ["포차", "포장마차", "떡볶이", "분식", "주점", "호프", "술집", "선술집",
                    "맥주", "와인", "바", "펍"]),
    ("면·국물",     ["국밥", "밀면", "냉면", "국수", "칼국수", "곰탕", "설렁탕", "수육",
                    "돼지국밥", "추어탕", "해장국", "순대", "탕", "찌개", "전골"]),
    ("한식·백반",    ["한정식", "백반", "비빔밥", "정식", "쌈밥", "보리밥", "가정식",
                    "한식", "솥밥", "전", "나물"]),
]


def infer_cat(d):
    # 1순위: 이름+대표메뉴 (가장 신뢰도 높은 신호) → 2순위: 설명까지 포함
    strong = " ".join([d.get("name", ""), d.get("menu", "")]).lower()
    full = strong + " " + d.get("desc", "").lower()
    for scope in (strong, full):
        for cat, kws in CATS:
            if any(k.lower() in scope for k in kws):
                return cat
    return "기타"


# ---- 실행 -----------------------------------------------------------------
def main():
    pages = int(sys.argv[1]) if len(sys.argv) > 1 else 22
    print(f"[1/3] 목록 {pages}p 수집…")
    listing = {}
    with ThreadPoolExecutor(max_workers=8) as ex:
        for fut in as_completed([ex.submit(parse_list, p) for p in range(1, pages + 1)]):
            listing.update(fut.result())
    seqs = sorted(listing, key=lambda s: int(s))
    print(f"    → {len(seqs)}곳 발견")

    print(f"[2/3] 상세 {len(seqs)}곳 수집…")
    details = {}
    done = 0
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(parse_detail, s): s for s in seqs}
        for fut in as_completed(futs):
            r = fut.result()
            done += 1
            if done % 25 == 0:
                print(f"    … {done}/{len(seqs)}")
            if r:
                details[r["seq"]] = r

    print("[3/3] 병합 + 카테고리 추론…")
    rows = []
    for s in seqs:
        row = dict(listing[s])
        row.update(details.get(s, {}))
        if not row.get("name"):
            continue
        row["category"] = infer_cat(row)
        row["detail_url"] = DETAIL_URL.format(seq=s)
        rows.append(row)

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)
    print(f"완료: {len(rows)}곳 → data.json")
    # 카테고리 분포
    from collections import Counter
    for c, n in Counter(r["category"] for r in rows).most_common():
        print(f"   {c}: {n}")


if __name__ == "__main__":
    main()
