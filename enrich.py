#!/usr/bin/env python3
"""data.json 확장: 좌표(lat/lng) + 영어·일본어 공식 번역 수집 → data.json (i18n 포함).

- 좌표: 상세페이지 default_lat/default_lng
- 번역: lang_cd=en / lang_cd=ja 상세페이지의 이름·메뉴·주소·휴무·시간·설명
- 한국어는 기존 data.json 값 사용. 전화번호는 언어 공통.
"""
import re, json, sys, time, html
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.request import Request, urlopen

BASE = "https://www.visitbusan.net"
URL = BASE + "/index.do?menuCd=DOM_000000201002001000&uc_seq={seq}&lang_cd={lang}"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"

NAME_RE = re.compile(r'<section id="title">.*?<h4 class="tit">(.*?)</h4>', re.S)
DESC_RE = re.compile(r'<div class="cont">\s*(.*?)\s*</div>', re.S)
INFO_RE = re.compile(r'<li><p>([^<]+)</p><span>(.*?)</span></li>', re.S)
LAT_RE = re.compile(r'default_lat\s*=\s*([0-9.]+)')
LNG_RE = re.compile(r'default_lng\s*=\s*([0-9.]+)')

LABELMAP = {
    "대표 메뉴": "menu", "대표메뉴": "menu", "Best Menu": "menu", "代表メニュー": "menu",
    "주소": "address", "Address": "address", "住所": "address",
    "전화번호": "phone", "Inquiry": "phone", "電話番号": "phone",
    "휴무일": "closed", "Closing Dates": "closed", "休業日": "closed",
    "운영요일 및 시간": "hours", "Hours": "hours", "営業曜日及び時間": "hours",
}
HANGUL = re.compile(r"[가-힣]")


def fetch(url, tries=3):
    for i in range(tries):
        try:
            req = Request(url, headers={"User-Agent": UA, "Accept-Language": "ko"})
            with urlopen(req, timeout=30) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:
            if i == tries - 1:
                print(f"  ! {url[:70]}: {e}", file=sys.stderr); return ""
            time.sleep(1.2)
    return ""


def clean(s):
    s = re.sub(r"<br\s*/?>", "\n", s or "", flags=re.I)
    s = re.sub(r"<[^>]+>", "", s)
    return re.sub(r"[ \t]+", " ", html.unescape(s)).strip()


def split_name(raw, lang):
    """영/일 이름은 'Translated (한글)' 형태 → 번역명만, 한글 원문은 별도."""
    raw = clean(raw)
    if lang == "ko":
        return raw, ""
    m = re.match(r"^(.*?)\s*\(([^)]*)\)\s*$", raw, re.S)
    if m and HANGUL.search(m.group(2)):
        return m.group(1).strip(), m.group(2).strip()
    return raw, ""


def parse(html_text, lang):
    out = {}
    m = NAME_RE.search(html_text)
    name, ko_in_name = split_name(m.group(1) if m else "", lang)
    out["name"] = name
    if ko_in_name:
        out["name_ko"] = ko_in_name
    m = DESC_RE.search(html_text)
    desc = clean(m.group(1)) if m else ""
    if desc:
        out["desc"] = desc
    for label, val in INFO_RE.findall(html_text):
        key = LABELMAP.get(clean(label))
        if key and key != "phone":
            v = clean(val)
            if v:
                out[key] = v
    return out


def enrich(row):
    seq = row["seq"]
    en_html = fetch(URL.format(seq=seq, lang="en"))
    ja_html = fetch(URL.format(seq=seq, lang="ja"))
    lat = lng = None
    if en_html:
        ml, mg = LAT_RE.search(en_html), LNG_RE.search(en_html)
        if ml and mg:
            lat, lng = float(ml.group(1)), float(mg.group(1))
    en = parse(en_html, "en") if en_html else {}
    ja = parse(ja_html, "ja") if ja_html else {}
    ko = {"name": row.get("name", ""), "menu": row.get("menu", ""),
          "address": row.get("address", ""), "hours": row.get("hours", ""),
          "closed": row.get("closed", ""), "desc": row.get("desc", "")}
    return seq, lat, lng, {"ko": ko, "en": en, "ja": ja}


def main():
    rows = json.load(open("data.json", encoding="utf-8"))
    by_seq = {r["seq"]: r for r in rows}
    print(f"확장 대상 {len(rows)}곳 (영·일 = {len(rows)*2} 요청)…")
    done = nocoord = 0
    with ThreadPoolExecutor(max_workers=8) as ex:
        for fut in as_completed([ex.submit(enrich, r) for r in rows]):
            seq, lat, lng, i18n = fut.result()
            r = by_seq[seq]
            r["lat"], r["lng"] = lat, lng
            r["i18n"] = i18n
            done += 1
            if lat is None:
                nocoord += 1
            if done % 40 == 0:
                print(f"  … {done}/{len(rows)}")
    json.dump(rows, open("data.json", "w"), ensure_ascii=False, indent=1)
    # 검증 요약
    en_named = sum(1 for r in rows if r.get("i18n", {}).get("en", {}).get("name"))
    ja_named = sum(1 for r in rows if r.get("i18n", {}).get("ja", {}).get("name"))
    print(f"완료. 좌표없음 {nocoord}곳 · 영문명 {en_named}곳 · 일문명 {ja_named}곳")
    print("샘플:", json.dumps({k: rows[0][k] for k in ("name", "lat", "lng")}, ensure_ascii=False))
    print("  en:", json.dumps(rows[0]["i18n"]["en"], ensure_ascii=False)[:160])


if __name__ == "__main__":
    main()
