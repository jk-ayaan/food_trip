#!/usr/bin/env python3
"""TourAPI로 전국 시·도 데이터 수집 → data/<region>/<section>.json.
쿼터 절약을 위해 상세설명(detailCommon2)은 생략 — 목록 정보만.
축제는 searchFestival2(응답에 기간 포함) 사용. 지역 인자 생략 시 전부."""
import json, os, re, sys, time

from grab_gyeonggi import api_get, fetch_all, category_for, clean_text, to_float

AREAS = {  # region key → (areaCode, 시·도 표기)
    "seoul": (1, "서울"), "incheon": (2, "인천"), "daejeon": (3, "대전"),
    "daegu": (4, "대구"), "gwangju": (5, "광주"), "ulsan": (7, "울산"),
    "sejong": (8, "세종"), "gyeonggi": (31, "경기"), "gangwon": (32, "강원"),
    "chungbuk": (33, "충북"), "chungnam": (34, "충남"), "gyeongbuk": (35, "경북"),
    "gyeongnam": (36, "경남"), "jeonbuk": (37, "전북"), "jeonnam": (38, "전남"),
    "jeju": (39, "제주"),
}
SECTIONS = {"sights": ("12", "14"), "food": ("39",), "stay": ("32",), "shopping": ("38",)}
SIDO_PREFIX = re.compile(r"^(서울|부산|대구|인천|광주|대전|울산|세종|경기|강원|충청북|충청남|경상북|경상남|전라북|전라남|전북|제주)[가-힣]*(?:특별자치)?(?:시|도)?\s*")


def district_from(address):
    """시도 제거 후 첫 시·군·구 단위 (세종은 시 단위 없음 → 읍·면·동)."""
    rest = SIDO_PREFIX.sub("", clean_text(address))
    m = re.match(r"([가-힣]+(?:시|군|구))", rest)
    if m:
        return m.group(1)
    m = re.match(r"([가-힣]+(?:읍|면|동))", rest)
    return m.group(1) if m else ""


def convert(row, section, extra=None):
    name = clean_text(row.get("title"))
    address = clean_text(row.get("addr1"))
    thumb = str(row.get("firstimage2") or row.get("firstimage") or "")
    out = {
        "section": section, "name_ko": name,
        "district": district_from(address),
        "category": category_for(row, section if section != "festival" else "sights"),
        "lat": to_float(row.get("mapy")), "lng": to_float(row.get("mapx")),
        "phone": clean_text(row.get("tel")), "thumb": thumb,
        "i18n": {"ko": {"name": name, "desc": "", "address": address}},
    }
    if extra:
        out.update(extra)
    return out


def iso(v):
    d = re.sub(r"\D", "", str(v or ""))
    return f"{d[:4]}-{d[4:6]}-{d[6:8]}" if len(d) >= 8 else ""


def collect(region, key):
    code, _label = AREAS[region]
    os.makedirs(f"data/{region}", exist_ok=True)
    summary = {}
    for section, types in SECTIONS.items():
        rows, seen = [], set()
        for t in types:
            for it in fetch_all("areaBasedList2", key, f"{region}/{section} type={t}",
                                areaCode=code, contentTypeId=t, arrange="A"):
                cid = str(it.get("contentid", ""))
                if cid in seen:
                    continue
                seen.add(cid)
                rows.append(convert(it, section))
        json.dump(rows, open(f"data/{region}/{section}.json", "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        summary[section] = len(rows)
    # 축제: searchFestival2 — 목록 응답에 행사 기간 포함
    fest = []
    for it in fetch_all("searchFestival2", key, f"{region}/festival",
                        areaCode=code, eventStartDate="20250101", arrange="A"):
        ps, pe = iso(it.get("eventstartdate")), iso(it.get("eventenddate"))
        fest.append(convert(it, "festival", {
            "pstart": ps, "pend": pe,
            "period": f"{ps.replace('-', '.')}~{pe.replace('-', '.')}" if ps and pe else "",
        }))
    json.dump(fest, open(f"data/{region}/festival.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    summary["festival"] = len(fest)
    return summary


def main():
    key = os.environ.get("TOURAPI_KEY", "").strip()
    if not key:
        raise SystemExit("오류: 환경변수 TOURAPI_KEY가 없습니다.")
    import urllib.parse
    key = urllib.parse.unquote(key)
    regions = [a for a in sys.argv[1:] if a in AREAS] or list(AREAS)
    total = {}
    for region in regions:
        print(f"\n[{region}] 수집 시작", flush=True)
        try:
            total[region] = collect(region, key)
        except Exception as exc:
            print(f"  !! {region} 중단: {exc}", flush=True)
            break
        print(f"  {region}: {total[region]}", flush=True)
    print("\n=== 요약 ===", flush=True)
    for r, s in total.items():
        print(f"{r}: {s} 소계 {sum(s.values())}", flush=True)


if __name__ == "__main__":
    main()
