#!/usr/bin/env python3
"""TourAPI KorService2의 경기 관광 데이터를 앱 JSON으로 저장."""
import argparse
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BASE_URL = "https://apis.data.go.kr/B551011/KorService2"
COMMON = {"MobileOS": "ETC", "MobileApp": "foodtrip", "_type": "json"}
REGIONS = {
    "suwon": {"kind": "area", "query": "수원"},
    "ansan": {"kind": "area", "query": "안산"},
    "pangyo": {"kind": "location", "mapX": "127.111217", "mapY": "37.394761"},
    "jeongja": {"kind": "location", "mapX": "127.108727", "mapY": "37.365994"},
    "seohyeon": {"kind": "location", "mapX": "127.123674", "mapY": "37.385166"},
}
SECTIONS = {
    "sights": ("12", "14"),
    "food": ("39",),
    "festival": ("15",),
    "stay": ("32",),
    "shopping": ("38",),
}

# TourAPI 구분류 코드 → 앱에서 쓸 간결한 한글 분류
CATEGORY_MAP = {
    "A0101": "자연관광지", "A0102": "관광자원",
    "A0201": "역사관광지", "A0202": "휴양관광지",
    "A0203": "체험관광지", "A0204": "산업관광지",
    "A0205": "건축·조형물", "A0206": "문화시설",
    "A0207": "축제·행사", "A0208": "공연·행사",
    "A0401": "쇼핑", "B0201": "숙박",
    "A01010100": "국립공원", "A01010200": "도립공원",
    "A01010300": "군립공원", "A01010400": "산",
    "A01010500": "자연생태관광지", "A01010600": "자연휴양림",
    "A01010700": "수목원", "A01010800": "폭포",
    "A01010900": "계곡", "A01011000": "약수터",
    "A01011100": "해안", "A01011200": "해수욕장",
    "A01011300": "섬", "A01011400": "항구·포구",
    "A01011600": "등대", "A01011700": "호수",
    "A01011800": "강", "A01011900": "동굴",
    "A02010100": "고궁", "A02010200": "성",
    "A02010300": "문", "A02010400": "고택",
    "A02010500": "생가", "A02010600": "민속마을",
    "A02010700": "유적지", "A02010800": "사찰",
    "A02010900": "종교성지", "A02011000": "안보관광지",
    "A02020200": "관광단지", "A02020300": "온천",
    "A02020400": "이색찜질방", "A02020500": "헬스투어",
    "A02020600": "테마공원", "A02020700": "공원",
    "A02020800": "유람선", "A02030100": "농어촌체험",
    "A02030200": "전통체험", "A02030300": "산사체험",
    "A02030400": "이색체험", "A02030600": "이색거리",
    "A02040400": "발전소", "A02040600": "식음료",
    "A02040800": "기타 산업관광지", "A02050100": "다리",
    "A02050200": "기념탑·기념비", "A02050300": "분수",
    "A02050400": "동상", "A02050500": "터널",
    "A02050600": "유명건물", "A02060100": "박물관",
    "A02060200": "기념관", "A02060300": "전시관",
    "A02060400": "컨벤션센터", "A02060500": "미술관·화랑",
    "A02060600": "공연장", "A02060700": "문화원",
    "A02060800": "외국문화원", "A02060900": "도서관",
    "A02061000": "대형서점", "A02061100": "문화전수시설",
    "A02061200": "영화관", "A02061300": "어학당",
    "A02061400": "학교", "A02070100": "문화관광축제",
    "A02070200": "일반축제", "A02080100": "전통공연",
    "A02080200": "연극", "A02080300": "뮤지컬",
    "A02080400": "오페라", "A02080500": "전시회",
    "A02080600": "박람회", "A02080800": "무용",
    "A02080900": "클래식", "A02081000": "대중콘서트",
    "A02081100": "영화", "A02081200": "스포츠경기",
    "A02081300": "기타행사", "A04010100": "5일장",
    "A04010200": "상설시장", "A04010300": "백화점",
    "A04010400": "면세점", "A04010500": "대형마트",
    "A04010600": "전문매장", "A04010700": "공예·공방",
    "A04010900": "특산물판매점", "A04011000": "사후면세점",
    "B02010100": "관광호텔", "B02010500": "콘도미니엄",
    "B02010600": "유스호스텔", "B02010700": "펜션",
    "B02010900": "모텔", "B02011000": "민박",
    "B02011100": "게스트하우스", "B02011200": "홈스테이",
    "B02011300": "서비스드레지던스", "B02011600": "한옥스테이",
}
FOOD_CODE_MAP = {
    "A05020100": "한식·백반", "A05020200": "양식·세계요리",
    "A05020300": "일식", "A05020400": "중식",
    "A05020500": "양식·세계요리", "A05020600": "양식·세계요리",
    "A05020700": "양식·세계요리", "A05020900": "카페·베이커리",
    "A05021000": "분식·주점",
}

_last_request = 0.0


def api_get(endpoint, service_key, **params):
    """0.2초 간격과 실패 후 3회 재시도를 적용한 JSON 요청."""
    global _last_request
    query = dict(COMMON)
    query.update(params)
    query["serviceKey"] = service_key
    url = f"{BASE_URL}/{endpoint}?{urllib.parse.urlencode(query)}"

    last_error = None
    for attempt in range(1, 5):
        wait = 0.2 - (time.monotonic() - _last_request)
        if wait > 0:
            time.sleep(wait)
        _last_request = time.monotonic()
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "foodtrip/1.0"})
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = json.load(response)
            if not isinstance(payload, dict):
                raise RuntimeError("API 응답이 JSON 객체가 아닙니다")
            # KorService2는 일부 파라미터 오류를 response 바깥에 반환하기도 함
            if "response" not in payload:
                code = str(payload.get("resultCode", "UNKNOWN"))
                message = payload.get("resultMsg", "응답 형식을 확인할 수 없습니다")
                raise RuntimeError(f"API 오류 {code}: {message}")
            result = payload.get("response", {})
            header = result.get("header", {})
            code = str(header.get("resultCode", "0000"))
            if code != "0000":
                raise RuntimeError(f"API 오류 {code}: {header.get('resultMsg', '알 수 없는 오류')}")
            return result.get("body", {}) or {}
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError,
                RuntimeError) as exc:
            last_error = exc
            if attempt < 4:
                print(f"  {endpoint} 요청 실패, 재시도 {attempt}/3", file=sys.stderr)
    reason = getattr(last_error, "reason", None) or str(last_error)
    raise RuntimeError(f"{endpoint} 요청을 완료하지 못했습니다: {reason}")


def item_list(body):
    """빈 응답·단일 객체·배열 응답을 모두 리스트로 통일."""
    items = body.get("items") or {}
    if not isinstance(items, dict):
        return []
    rows = items.get("item") or []
    if isinstance(rows, dict):
        return [rows]
    return rows if isinstance(rows, list) else []


def fetch_all(endpoint, service_key, label="", **params):
    """numOfRows=100으로 전체 페이지 수집."""
    out, page = [], 1
    while True:
        body = api_get(endpoint, service_key, numOfRows=100, pageNo=page, **params)
        rows = item_list(body)
        out.extend(rows)
        try:
            total = int(body.get("totalCount", len(out)))
        except (TypeError, ValueError):
            total = len(out)
        print(f"  {label or endpoint}: {len(out)}/{total} (page {page})")
        if not rows or len(out) >= total:
            break
        page += 1
    return out


def find_sigungu(service_key, query):
    rows = fetch_all("areaCode2", service_key, f"{query} 시군구 검색", areaCode=31)
    matches = [r for r in rows if query in str(r.get("name", ""))]
    if not matches:
        names = ", ".join(str(r.get("name", "")) for r in rows)
        raise RuntimeError(f"areaCode2에서 '{query}' 시군구를 찾지 못했습니다. 응답: {names}")
    exact = next((r for r in matches if r.get("name") == f"{query}시"), matches[0])
    print(f"  {query}: {exact.get('name')} sigunguCode={exact.get('code')}")
    return str(exact["code"])


def clean_text(value):
    text = str(value or "")
    text = re.sub(r"<\s*br\s*/?\s*>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text).replace("\r", "")
    return "\n".join(line.strip() for line in text.split("\n") if line.strip())


def homepage_url(value):
    raw = html.unescape(str(value or "")).strip()
    match = re.search(r"href\s*=\s*['\"]([^'\"]+)", raw, flags=re.I)
    return (match.group(1) if match else clean_text(raw)).strip()


def to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def district_from(address, region):
    """주소의 시·구를 사용하되 역세권은 분당구처럼 구 단위로 표시."""
    address = clean_text(address)
    match = re.search(r"(?:경기도|경기)\s+([가-힣]+시)\s+([가-힣]+구)", address)
    if not match:
        match = re.search(r"\b([가-힣]+시)\s+([가-힣]+구)\b", address)
    if match:
        return match.group(2) if REGIONS[region]["kind"] == "location" else f"{match.group(1)} {match.group(2)}"
    match = re.search(r"(?:경기도|경기)\s+([가-힣]+(?:시|군))", address)
    if not match:
        match = re.search(r"\b([가-힣]+(?:시|군|구))\b", address)
    return match.group(1) if match else ""


def food_category(row):
    """음식 세부코드에 상호명 단서를 보태 앱 카테고리에 맞춤."""
    title = str(row.get("title", "")).replace(" ", "")
    rules = (
        ("카페·베이커리", ("카페", "커피", "로스터", "베이커", "제과", "빵", "디저트", "다방", "떡집")),
        ("해산물·회", ("횟집", "회관", "수산", "해물", "생선", "대게", "조개", "아구", "아귀", "낙지", "쭈꾸미", "문어", "장어", "굴비", "게장", "복어")),
        ("고기·구이", ("갈비", "고기", "한우", "정육", "삼겹", "돼지", "곱창", "막창", "닭갈비", "불고기", "바비큐", "숯불")),
        ("면·국물", ("국수", "냉면", "밀면", "라면", "우동", "소바", "칼국수", "수제비", "설렁탕", "곰탕", "국밥", "해장국", "감자탕", "추어탕")),
        ("분식·주점", ("분식", "떡볶이", "김밥", "튀김", "포차", "호프", "주점", "막걸리", "맥주", "이자카야")),
    )
    for category, words in rules:
        if any(word in title for word in words):
            return category
    return FOOD_CODE_MAP.get(str(row.get("cat3", "")), "기타")


def category_for(row, section):
    if section == "food":
        return food_category(row)
    cat3, cat2 = str(row.get("cat3", "")), str(row.get("cat2", ""))
    return CATEGORY_MAP.get(cat3, CATEGORY_MAP.get(cat2, "기타"))


def first_detail(endpoint, service_key, content_id, content_type_id=None):
    params = {"contentId": content_id}
    if content_type_id:
        params["contentTypeId"] = content_type_id
    return (item_list(api_get(endpoint, service_key, **params)) or [{}])[0]


def iso_date(value):
    digits = re.sub(r"\D", "", str(value or ""))
    return f"{digits[:4]}-{digits[4:6]}-{digits[6:8]}" if len(digits) >= 8 else ""


def convert(row, region, section, common_detail, intro_detail):
    name = clean_text(row.get("title"))
    address = clean_text(row.get("addr1"))
    detail = common_detail or {}
    ko = {
        "name": name,
        "desc": clean_text(detail.get("overview")),
        "address": address,
    }
    out = {
        "section": section,
        "name_ko": name,
        "district": district_from(address, region),
        "category": category_for(row, section),
        "lat": to_float(row.get("mapy")),
        "lng": to_float(row.get("mapx")),
        "phone": clean_text(row.get("tel")),
        "thumb": str(row.get("firstimage2") or row.get("firstimage") or ""),
        "i18n": {"ko": ko},
    }
    homepage = homepage_url(detail.get("homepage") or row.get("homepage"))
    if homepage:
        out["homepage"] = homepage
    if section == "festival":
        pstart = iso_date((intro_detail or {}).get("eventstartdate"))
        pend = iso_date((intro_detail or {}).get("eventenddate"))
        out.update({
            "pstart": pstart,
            "pend": pend,
            "period": f"{pstart.replace('-', '.')}~{pend.replace('-', '.')}" if pstart and pend else "",
        })
    return out


def collect_section(region, section, service_key, sigungu_code, no_desc,
                    common_cache, intro_cache):
    spec = REGIONS[region]
    collected = []
    for content_type_id in SECTIONS[section]:
        params = {"contentTypeId": content_type_id, "arrange": "A"}
        if spec["kind"] == "area":
            endpoint = "areaBasedList2"
            params.update(areaCode=31, sigunguCode=sigungu_code)
        else:
            endpoint = "locationBasedList2"
            params.update(mapX=spec["mapX"], mapY=spec["mapY"], radius=2000)
        label = f"{region}/{section} type={content_type_id}"
        collected.extend(fetch_all(endpoint, service_key, label, **params))

    # 관광지+문화시설처럼 여러 타입을 합칠 때 contentId 중복 제거
    unique = {}
    for row in collected:
        unique[str(row.get("contentid", ""))] = row
    rows = []
    total = len(unique)
    for index, row in enumerate(unique.values(), 1):
        content_id = str(row.get("contentid", ""))
        content_type_id = str(row.get("contenttypeid") or SECTIONS[section][0])
        detail = {}
        if not no_desc:
            if content_id not in common_cache:
                try:
                    common_cache[content_id] = first_detail("detailCommon2", service_key, content_id)
                except RuntimeError as exc:
                    print(f"  경고: {content_id} overview 생략 ({exc})", file=sys.stderr)
                    common_cache[content_id] = {}
            detail = common_cache[content_id]
        intro = {}
        if section == "festival":
            if content_id not in intro_cache:
                try:
                    intro_cache[content_id] = first_detail(
                        "detailIntro2", service_key, content_id, content_type_id)
                except RuntimeError as exc:
                    print(f"  경고: {content_id} 행사 기간 생략 ({exc})", file=sys.stderr)
                    intro_cache[content_id] = {}
            intro = intro_cache[content_id]
        rows.append(convert(row, region, section, detail, intro))
        if index == total or index % 10 == 0:
            print(f"  {region}/{section} 상세: {index}/{total}")
    return rows


def save_rows(region, section, rows):
    directory = os.path.join("data", region)
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, f"{section}.json")
    with open(path, "w", encoding="utf-8") as file:
        json.dump(rows, file, ensure_ascii=False, indent=1)
        file.write("\n")
    print(f"  {path} 저장: {len(rows)}곳")


def parse_args():
    parser = argparse.ArgumentParser(description="TourAPI 경기 지역 관광 데이터 수집")
    parser.add_argument("regions", nargs="*", choices=REGIONS, metavar="region",
                        help="suwon ansan pangyo jeongja seohyeon (생략 시 전체)")
    parser.add_argument("--no-desc", action="store_true",
                        help="detailCommon2 overview 수집 생략")
    return parser.parse_args()


def main():
    args = parse_args()
    raw_key = os.environ.get("TOURAPI_KEY", "").strip()
    if not raw_key:
        raise SystemExit("오류: 환경변수 TOURAPI_KEY가 없습니다. 발급받은 TourAPI 서비스키를 설정해 주세요.")
    # 포털이 제공하는 인코딩 키와 일반 키를 모두 허용
    service_key = urllib.parse.unquote(raw_key)
    regions = list(dict.fromkeys(args.regions or REGIONS.keys()))
    summary = {region: {} for region in regions}
    common_cache, intro_cache = {}, {}

    for region in regions:
        print(f"\n[{region}] 수집 시작")
        sigungu_code = None
        if REGIONS[region]["kind"] == "area":
            sigungu_code = find_sigungu(service_key, REGIONS[region]["query"])
        for section in SECTIONS:
            print(f"- {section}")
            rows = collect_section(region, section, service_key, sigungu_code,
                                   args.no_desc, common_cache, intro_cache)
            save_rows(region, section, rows)
            summary[region][section] = len(rows)

    print("\n=== 수집 요약 ===")
    for region in regions:
        counts = "  ".join(f"{section} {summary[region][section]}" for section in SECTIONS)
        print(f"{region}: {counts}")


if __name__ == "__main__":
    main()
