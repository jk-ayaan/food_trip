#!/usr/bin/env python3
"""부산관광포털 '부산에가면' 전 섹션 범용 수집기 → data/<section>.json
사용: python3 grab.py <section>   (sights|food|shopping|stay|festival|all)

- 표준 섹션(명소·음식·쇼핑·축제): box actionImg3 목록 + 상세(h4.tit, InfoD, 좌표, 설명) + 영·일 번역
- 숙박: acm_ 목록(이름·구·유형·주소·좌표) + 상세 썸네일 + 영·일 목록 번역
- ucg_seq(1~16)로 구·군 정확 매핑 / 섹션별 카테고리 추론 / 축제 기간 추출
"""
import re, json, sys, time, html, os
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.request import Request, urlopen

BASE = "https://www.visitbusan.net"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"

SECTIONS = {
    "sights":   {"code": "201001", "name": "명소",  "std": True},
    "food":     {"code": "201002", "name": "음식",  "std": True},
    "shopping": {"code": "201003", "name": "쇼핑",  "std": True},
    "stay":     {"code": "201004", "name": "숙박",  "std": False},
    "festival": {"code": "201005", "name": "축제",  "std": True, "festival": True},
}
GU = {1:"중구",2:"동구",3:"영도구",4:"부산진구",5:"동래구",6:"남구",7:"북구",8:"해운대구",
      9:"서구",10:"사하구",11:"금정구",12:"강서구",13:"연제구",14:"수영구",15:"사상구",16:"기장군"}

def fetch(url, tries=3):
    for i in range(tries):
        try:
            with urlopen(Request(url, headers={"User-Agent": UA, "Accept-Language": "ko"}), timeout=30) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:
            if i == tries-1:
                print(f"  ! {url[:70]}: {e}", file=sys.stderr); return ""
            time.sleep(1.2)
    return ""

def clean(s):
    s = re.sub(r"<br\s*/?>", "\n", s or "", flags=re.I)
    s = re.sub(r"<[^>]+>", "", s)
    return re.sub(r"[ \t]+", " ", html.unescape(s)).strip()

def listurl(code, page, ucg=None):
    u = f"{BASE}/index.do?menuCd=DOM_000000{code}000000&page_no={page}&order_type=NEW"
    return u + (f"&ucg_seq={ucg}" if ucg else "")
def deturl(code, seq, lang="ko"):
    return f"{BASE}/index.do?menuCd=DOM_000000{code}001000&uc_seq={seq}&lang_cd={lang}"

# ── 표준 파서 ──────────────────────────────────────────────
CARD_RE = re.compile(r'<div class="box actionImg3">\s*<a href="[^"]*?uc_seq=(\d+)[^"]*"[^>]*>\s*<img src="([^"]+)" alt="([^"]*)"', re.S)
STATS_RE = re.compile(r'uc_seq=(\d+).*?클릭수"?>\s*([\d,]+).*?리뷰수"?>\s*([\d,]+).*?좋아요"?>\s*([\d,]+)', re.S)
NAME_RE = re.compile(r'<section id="title">.*?<h4 class="tit">(.*?)</h4>', re.S)
DESC_RE = re.compile(r'<div class="cont">\s*(.*?)\s*</div>', re.S)
INFO_RE = re.compile(r'<li><p>([^<]+)</p><span>(.*?)</span></li>', re.S)
LAT_RE = re.compile(r'default_lat\s*=\s*([0-9.]+)')
LNG_RE = re.compile(r'default_lng\s*=\s*([0-9.]+)')
_FULL = r'(?:운영기간|행사기간|축제기간|개최기간|전시기간|이벤트기간|기간)\s*[:：]?\s*(20\d{2})\D{1,3}(\d{1,2})\D{1,3}(\d{1,2})\.?\s*[~∼\-]+\s*(20\d{2})\D{1,3}(\d{1,2})\D{1,3}(\d{1,2})'
PERIOD_LABELED = re.compile(_FULL)

def parse_fest_dates(s):
    """축제 운영시간 필드(기간)에서 시작·종료 ISO 날짜 파싱. 다양한 형식 대응."""
    if not s: return None
    m = re.search(r'(20\d{2})\D{1,3}(\d{1,2})\D{1,3}(\d{1,2})', s)
    if not m: return None
    y1, mo1, d1 = int(m.group(1)), int(m.group(2)), int(m.group(3))
    start = f"{y1}-{mo1:02d}-{d1:02d}"
    m2 = re.search(r'[~∼\-]\s*(?:(20\d{2})\D{1,3})?(\d{1,2})\D{1,3}(\d{1,2})', s[m.end():])
    if m2:
        y2 = int(m2.group(1)) if m2.group(1) else y1
        end = f"{y2}-{int(m2.group(2)):02d}-{int(m2.group(3)):02d}"
    else:
        end = start
    return start, end

LABELMAP = {
    "대표 메뉴":"menu","대표메뉴":"menu","Best Menu":"menu","代表メニュー":"menu",
    "주소":"address","Address":"address","住所":"address",
    "전화번호":"phone","Inquiry":"phone","電話番号":"phone","문의":"phone","문의처":"phone",
    "휴무일":"closed","Closing Dates":"closed","休業日":"closed",
    "운영요일 및 시간":"hours","Hours":"hours","営業曜日及び時間":"hours",
    "홈페이지":"homepage","Homepage":"homepage","Website":"homepage","ホームページ":"homepage",
    "교통정보":"transport","Transportation":"transport","交通":"transport","交通情報":"transport",
    "이용요금":"fee","Fee":"fee","Admission":"fee","利用料金":"fee","料金":"fee",
    "주요장소":"places","主要場所":"places","Main Places":"places",
}
TRANSLATABLE = {"menu","address","hours","closed","fee","transport","places","type"}

def parse_info_ordered(h):
    out = []
    for label, val in INFO_RE.findall(h):
        out.append((clean(label), clean(val)))
    return out

FEST_CARD_RE = re.compile(r'<img src="(/uploadImgs/files/cntnts/[^"]+)"[^>]*>.*?<p class="tit"><a href="[^"]*?uc_seq=(\d+)[^"]*"[^>]*>(.*?)</a>', re.S)

def std_list(code, page, ucg=None, fest=False):
    h = fetch(listurl(code, page, ucg))
    cards = {}
    pairs = ((s, i, n) for i, s, n in FEST_CARD_RE.findall(h)) if fest else CARD_RE.findall(h)
    for seq, img, name in pairs:
        cards[seq] = {"seq": seq, "name": clean(name),
                      "thumb": img if img.startswith("http") else BASE+img}
    for seq, v, rv, lk in STATS_RE.findall(h):
        if seq in cards:
            cards[seq].update(views=int(v.replace(",","")), reviews=int(rv.replace(",","")), likes=int(lk.replace(",","")))
    return cards

def std_detail(code, seq, festival=False):
    out = {"seq": seq, "i18n": {}}
    h = fetch(deturl(code, seq, "ko"))
    if h:
        m = LAT_RE.search(h); g = LNG_RE.search(h)
        if m and g: out["lat"], out["lng"] = float(m.group(1)), float(g.group(1))
        info = parse_info_ordered(h)
        ko = {}
        m = NAME_RE.search(h); ko["name"] = clean(m.group(1)) if m else ""
        m = DESC_RE.search(h); ko["desc"] = clean(m.group(1)) if m else ""
        canon = []  # 위치기반 매핑용 표준키 순서
        for label, val in info:
            key = LABELMAP.get(label)
            canon.append(key)
            if key == "phone": out["phone"] = val
            elif key == "homepage": out["homepage"] = val
            elif key: ko[key] = val
        out["_canon"] = canon
        out["i18n"]["ko"] = ko
        if festival:
            src = (ko.get("hours") or "").strip()
            g = parse_fest_dates(src)
            if not g:  # 폴백: 설명 내 라벨된 기간
                lm = PERIOD_LABELED.search(ko.get("desc", ""))
                if lm:
                    y1,m1,d1,y2,m2,d2 = (int(x) for x in lm.groups())
                    src = f"{y1}.{m1:02d}.{d1:02d} ~ {y2}.{m2:02d}.{d2:02d}"
                    g = (f"{y1}-{m1:02d}-{d1:02d}", f"{y2}-{m2:02d}-{d2:02d}")
            out["period"] = src
            if g:
                out["pstart"], out["pend"] = g
    # 영·일 (위치기반 매핑)
    canon = out.get("_canon", [])
    for lang in ("en", "ja"):
        hh = fetch(deturl(code, seq, lang))
        if not hh: continue
        t = {}
        m = NAME_RE.search(hh)
        nm = clean(m.group(1)) if m else ""
        nm = re.sub(r"\s*\(([^)]*[가-힣][^)]*)\)\s*$", "", nm).strip() or nm
        t["name"] = nm
        m = DESC_RE.search(hh);
        if m and clean(m.group(1)): t["desc"] = clean(m.group(1))
        vals = [v for _, v in parse_info_ordered(hh)]
        for idx, val in enumerate(vals):
            if idx < len(canon) and canon[idx] in TRANSLATABLE and val:
                t[canon[idx]] = val
        out["i18n"][lang] = t
    out.pop("_canon", None)
    return out

# ── 숙박(acm_) 파서 ────────────────────────────────────────
ACM_RE = re.compile(
    r'<div class="acm_name"><a href="[^"]*?uc_seq=(\d+)[^"]*">(.*?)</a></div>\s*'
    r'<div class="acm_loc">(.*?)</div>\s*'
    r'<div class="acm_info">(.*?)</div>\s*'
    r'<div class="acm_add">\s*<span class="address">(.*?)</span>'
    r'(?:.*?openGoogleMap\(\s*\'([0-9.]+)\'\s*,\s*\'([0-9.]+)\'\s*\))?', re.S)
ACM_THUMB_RE = re.compile(r'uploadImgs/files/cntnts/[0-9]+_thumb[A-Z]?')

def acm_list(code, page, lang="ko"):
    u = listurl(code, page) + ("" if lang == "ko" else f"&lang_cd={lang}")
    h = fetch(u)
    out = {}
    for seq, name, loc, info, addr, lat, lng in ACM_RE.findall(h):
        gu = ""
        mloc = re.search(r"([가-힣]+구|기장군)", clean(loc))
        if mloc: gu = mloc.group(1)
        typ = clean(re.sub(r"</?span[^>]*>", " ", info))
        rec = {"seq": seq, "name": clean(name), "district": gu, "type": typ, "address": clean(addr)}
        if lat and lng: rec["lat"], rec["lng"] = float(lat), float(lng)
        out[seq] = rec
    return out

def stay_thumb(code, seq):
    h = fetch(deturl(code, seq, "ko"))
    m = ACM_THUMB_RE.search(h)
    return BASE + "/" + m.group(0) if m else ""

# ── 카테고리 추론 ──────────────────────────────────────────
def cat_food(t):
    CATS=[("카페·베이커리",["커피","카페","로스터","베이커리","제과","디저트","케이크","라떼","브런치","빵","도넛"]),
        ("일식",["야키토리","스시","초밥","라멘","우동","돈카츠","돈가스","이자카야","로바타","사시미","텐동","오마카세","소바"]),
        ("해산물·회",["회","횟집","해물","해산물","조개","대게","게장","갈치","수산","활어","장어","복국","아구","물회","전복","굴","낙지","곰장어","꼼장어"]),
        ("고기·구이",["갈비","삼겹","고기","구이","곱창","막창","한우","정육","양꼬치","불고기","스테이크","바베큐","돼지","소고기"]),
        ("중식",["중화","짜장","짬뽕","마라","딤섬","양장피","탕수육","중국"]),
        ("양식·세계요리",["파스타","피자","버거","비스트로","스테이크","타코","쌀국수","포케","이탈리","프렌치","스페인","다이닝","레스토랑","퓨전","베트남","태국"]),
        ("분식·주점",["포차","포장마차","떡볶이","분식","주점","호프","술집","선술집","맥주","와인","펍"]),
        ("면·국물",["국밥","밀면","냉면","국수","칼국수","곰탕","설렁탕","수육","돼지국밥","추어탕","해장국","순대","찌개","전골"]),
        ("한식·백반",["한정식","백반","비빔밥","정식","쌈밥","보리밥","가정식","한식","솥밥"])]
    for c,ks in CATS:
        if any(k in t for k in ks): return c
    return "기타"
def cat_sights(t):
    CATS=[("바다·해변",["해변","해수욕장","바닷","해안","포구","등대","갯벌","방파제","해상","해변로"]),
        ("전망·야경",["전망","야경","타워","스카이","케이블카","전망대","루프탑","파노라마"]),
        ("역사·문화재",["사찰","향교","서원","유적","고분","문화재","왕릉","읍성","기념관","고택","종교","대웅전","유산"]),
        ("박물관·전시",["박물관","미술관","전시","갤러리","아트","과학관","기념"]),
        ("테마·체험",["테마","체험","랜드","월드","아쿠아","수족관","빌리지","마을","스튜디오","온천","스파","놀이","워터"]),
        ("공원·자연",["공원","수목원","숲","계곡","폭포","호수","정원","둘레길","산책","생태","습지","유원지"]),
        ("거리·시장",["거리","골목","로데오","상점가","먹자","시장"])]
    for c,ks in CATS:
        if any(k in t for k in ks): return c
    return "기타"
def cat_shopping(t):
    CATS=[("백화점·몰",["백화점","쇼핑몰","쇼핑센터","스퀘어","프리미엄","아울렛","롯데","신세계","현대","몰 "]),
        ("전통시장",["시장","상가","상점가","골목시장"]),
        ("면세점",["면세"]),
        ("거리·테마",["거리","골목","로데오","스트리트","타운","특화"])]
    for c,ks in CATS:
        if any(k in t for k in ks): return c
    return "기타"
def infer_category(section, name, menu, desc):
    """이름+메뉴 우선, 설명은 폴백(설명 키워드 오염 방지)."""
    if section == "festival":
        return "축제·행사"
    fn = {"food": cat_food, "sights": cat_sights, "shopping": cat_shopping}[section]
    strong = f"{name or ''} {menu or ''}"
    c = fn(strong)
    return c if c != "기타" else fn(f"{strong} {desc or ''}")

def cat_stay(typ):
    t=typ or ""
    if any(k in t for k in ["관광호텔","호텔","Hotel"]): return "호텔"
    if any(k in t for k in ["리조트","콘도","Resort","Condo"]): return "리조트·콘도"
    if any(k in t for k in ["게스트","Guest","호스텔","Hostel"]): return "게스트하우스"
    if any(k in t for k in ["모텔","Motel"]): return "모텔"
    if any(k in t for k in ["펜션","Pension","민박"]): return "펜션·민박"
    return "기타"

# ── 섹션 실행 ──────────────────────────────────────────────
def gu_map(code, std=True):
    """ucg_seq별로 seq→구 매핑."""
    seq2gu = {}
    def one(g):
        seqs=set(); page=1
        while page<=12:
            h=fetch(listurl(code,page,g))
            new=set(re.findall(r'uc_seq=(\d+)', h))
            if not new or new<=seqs: break
            b=len(seqs); seqs|=new
            if len(seqs)==b: break
            page+=1
        return g, seqs
    with ThreadPoolExecutor(max_workers=8) as ex:
        for fut in as_completed([ex.submit(one,g) for g in GU]):
            g,seqs=fut.result()
            for s in seqs: seq2gu[s]=GU[g]
    return seq2gu

def npages(code):
    h=fetch(listurl(code,1))
    ps=[int(x) for x in re.findall(r'page_no=(\d+)', h)]
    return max(ps) if ps else 1

def run_standard(key):
    s=SECTIONS[key]; code=s["code"]; fest=s.get("festival",False)
    pages=npages(code); print(f"[{s['name']}] {pages}페이지 목록 수집…")
    listing={}
    with ThreadPoolExecutor(max_workers=8) as ex:
        for fut in as_completed([ex.submit(std_list,code,p,None,fest) for p in range(1,pages+1)]):
            listing.update(fut.result())
    seqs=sorted(listing,key=int); print(f"  → {len(seqs)}곳")
    print(f"[{s['name']}] 구·군 매핑…"); seq2gu=gu_map(code)
    print(f"[{s['name']}] 상세+번역 수집 ({len(seqs)}곳)…")
    details={}; done=0
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs={ex.submit(std_detail,code,sq,fest):sq for sq in seqs}
        for fut in as_completed(futs):
            r=fut.result(); details[r["seq"]]=r; done+=1
            if done%40==0: print(f"  … {done}/{len(seqs)}")
    rows=[]
    for sq in seqs:
        base=listing[sq]; det=details.get(sq,{})
        i18n=det.get("i18n",{}); ko=i18n.get("ko",{})
        name=ko.get("name") or base["name"]
        if not name: continue
        row={"seq":sq,"section":key,"name_ko":name,"thumb":base.get("thumb",""),
             "views":base.get("views",0),"likes":base.get("likes",0),
             "district":seq2gu.get(sq,""),"lat":det.get("lat"),"lng":det.get("lng"),
             "phone":det.get("phone",""),"homepage":det.get("homepage",""),
             "category":infer_category(key,name,ko.get("menu",""),ko.get("desc","")),
             "i18n":i18n,"detail_url":deturl(code,sq,"ko")}
        ko.setdefault("name",name)
        if fest:
            row["period"]=det.get("period",""); row["pstart"]=det.get("pstart",""); row["pend"]=det.get("pend","")
            row["category"]="축제·행사"
        rows.append(row)
    return rows

def run_stay(key="stay"):
    s=SECTIONS[key]; code=s["code"]
    pages=npages(code); print(f"[숙박] {pages}페이지 acm 목록 수집…")
    ko={}
    with ThreadPoolExecutor(max_workers=8) as ex:
        for fut in as_completed([ex.submit(acm_list,code,p,"ko") for p in range(1,pages+1)]):
            ko.update(fut.result())
    seqs=sorted(ko,key=int); print(f"  → {len(seqs)}곳")
    # 비짓부산은 숙박명을 번역하지 않음(영문 목록도 한글명) → en/ja는 ko 폴백
    print(f"[숙박] 상세 썸네일 수집 ({len(seqs)}곳)…")
    thumbs={}; done=0
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs={ex.submit(stay_thumb,code,sq):sq for sq in seqs}
        for fut in as_completed(futs):
            sq=futs[fut]; thumbs[sq]=fut.result(); done+=1
            if done%50==0: print(f"  … {done}/{len(seqs)}")
    rows=[]
    for sq in seqs:
        k=ko[sq]
        i18n={"ko":{"name":k["name"],"address":k.get("address",""),"type":k.get("type","")}}
        rows.append({"seq":sq,"section":"stay","name_ko":k["name"],"thumb":thumbs.get(sq,""),
            "views":0,"likes":0,"district":k.get("district",""),"lat":k.get("lat"),"lng":k.get("lng"),
            "phone":"","homepage":"","category":cat_stay(k.get("type","")),"stay_type":k.get("type",""),
            "i18n":i18n,"detail_url":deturl(code,sq,"ko")})
    return rows

def main():
    target=sys.argv[1] if len(sys.argv)>1 else "all"
    keys=list(SECTIONS) if target=="all" else [target]
    os.makedirs("data", exist_ok=True)
    for key in keys:
        t0=time.time()
        rows=run_stay(key) if not SECTIONS[key]["std"] else run_standard(key)
        json.dump(rows, open(f"data/{key}.json","w"), ensure_ascii=False, separators=(",",":"))
        coords=sum(1 for r in rows if r.get("lat"))
        en=sum(1 for r in rows if r.get("i18n",{}).get("en",{}).get("name"))
        print(f"✅ {SECTIONS[key]['name']}({key}): {len(rows)}곳 · 좌표 {coords} · 영문명 {en} · {time.time()-t0:.0f}s → data/{key}.json\n")

if __name__=="__main__":
    main()
