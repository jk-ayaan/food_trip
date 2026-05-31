#!/usr/bin/env python3
"""data/<section>.json (5개) → index.html : '부산에 가면' 멀티섹션 가이드.
섹션탭(명소·음식·축제·숙박·쇼핑) + 지도(Leaflet/OSM) + 다국어(한·영·일·중)."""
import json, datetime, os

SECTIONS = ["sights", "food", "festival", "stay", "shopping"]


def mlf(i18n, field):
    o = {}
    for lang in ("ko", "en", "ja"):
        v = (i18n.get(lang) or {}).get(field, "")
        if v:
            o[lang] = v
    return o or None


def slim_row(r):
    i = r.get("i18n", {})
    out = {"c": r.get("category", "기타"), "g": r.get("district", ""),
           "t": r.get("thumb", ""), "lat": r.get("lat"), "lng": r.get("lng"),
           "u": r.get("detail_url", "")}
    for short, field in [("n", "name"), ("m", "menu"), ("a", "address"),
                          ("h", "hours"), ("x", "closed"), ("d", "desc"),
                          ("fee", "fee"), ("tr", "transport"), ("ty", "type")]:
        v = mlf(i, field)
        if v:
            out[short] = v
    if r.get("phone"):
        out["p"] = r["phone"]
    if r.get("homepage"):
        out["hp"] = r["homepage"]
    if r.get("views"):
        out["v"] = r["views"]
    if r.get("likes"):
        out["l"] = r["likes"]
    if r.get("period"):
        out["pd"] = r["period"]
    if r.get("pstart"):
        out["ps"] = r["pstart"]
    if r.get("pend"):
        out["pe"] = r["pend"]
    return out


data = {}
counts = {}
for s in SECTIONS:
    path = f"data/{s}.json"
    rows = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else []
    data[s] = [slim_row(r) for r in rows if (r.get("i18n", {}).get("ko", {}).get("name") or r.get("name_ko"))]
    counts[s] = len(data[s])

data_js = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
total = sum(counts.values())
updated = datetime.date.today().isoformat()
print("섹션별:", counts, "총", total)

HTML = r"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#0a6ebd">
<meta name="description" content="부산에 가면 — 명소·음식·축제·숙박·쇼핑 __TOTAL__곳 지도·다국어 가이드. 출처 비짓부산.">
<title>부산에 가면 · When in Busan</title>
<link rel="preconnect" href="https://cdn.jsdelivr.net">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css">
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css">
<style>
:root{--bg:#eef1f5;--card:#fff;--ink:#16202c;--sub:#5d6b7a;--line:#e6eaf0;--sea:#0a6ebd;--sea2:#0fa3b1;--shadow:0 6px 22px rgba(20,40,70,.08);--safe-t:env(safe-area-inset-top);--safe-b:env(safe-area-inset-bottom)}
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
html,body{margin:0}
body{font-family:"Pretendard","Pretendard Variable",-apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo","Hiragino Kaku Gothic ProN","Microsoft YaHei","Malgun Gothic",system-ui,sans-serif;background:var(--bg);color:var(--ink);line-height:1.5;-webkit-text-size-adjust:100%}
a{color:inherit;text-decoration:none}img{display:block}

.hero{background:linear-gradient(135deg,var(--sea) 0%,var(--sea2) 100%);color:#fff;padding:calc(16px + var(--safe-t)) 16px 0}
.hero .wrap{max-width:1180px;margin:0 auto}
.hero .topline{display:flex;justify-content:space-between;align-items:flex-start;gap:12px;padding:0 2px}
.hero h1{margin:0;font-size:22px;font-weight:800;letter-spacing:-.02em;display:flex;align-items:center;gap:7px}
.hero p{margin:5px 0 0;font-size:12.5px;opacity:.92;font-weight:500}
.langs{display:flex;gap:4px;background:rgba(255,255,255,.16);border-radius:999px;padding:3px;flex:none}
.langs button{border:0;background:transparent;color:#fff;font-weight:700;font-size:12px;padding:6px 9px;border-radius:999px;cursor:pointer;opacity:.8}
.langs button.on{background:#fff;color:var(--sea);opacity:1}
.tabs{display:flex;gap:6px;overflow-x:auto;margin-top:12px;padding:0 2px 0;scrollbar-width:none}
.tabs::-webkit-scrollbar{display:none}
.tab{flex:none;border:0;background:rgba(255,255,255,.14);color:#fff;border-radius:13px 13px 0 0;padding:11px 16px;font-size:14px;font-weight:700;cursor:pointer;opacity:.82;display:flex;align-items:center;gap:6px;white-space:nowrap}
.tab .tn{font-size:11px;opacity:.7;font-weight:700}
.tab.on{background:var(--bg);color:var(--ink);opacity:1}
.tab.on .tn{color:var(--sea);opacity:1}

.tools{position:sticky;top:0;z-index:1000;background:rgba(255,255,255,.93);backdrop-filter:saturate(1.4) blur(10px);border-bottom:1px solid var(--line);box-shadow:0 2px 10px rgba(20,40,70,.04)}
.tools .wrap{max-width:1180px;margin:0 auto;padding:11px 14px 7px}
.searchrow{display:flex;gap:8px;align-items:center}
.search{flex:1;display:flex;align-items:center;gap:8px;background:var(--bg);border:1.5px solid var(--line);border-radius:14px;padding:11px 14px;min-width:0}
.search:focus-within{border-color:var(--sea);background:#fff}
.search svg{flex:none;width:18px;height:18px;color:var(--sub)}
.search input{border:0;background:transparent;width:100%;font-size:15px;outline:none;color:var(--ink);min-width:0}
.viewtog{flex:none;display:flex;background:var(--bg);border:1.5px solid var(--line);border-radius:14px;overflow:hidden}
.viewtog button{border:0;background:transparent;padding:10px 12px;font-size:13px;font-weight:700;color:var(--sub);cursor:pointer;display:flex;align-items:center;gap:5px}
.viewtog button.on{background:var(--sea);color:#fff}
.viewtog svg{width:15px;height:15px}
.sortwrap{display:flex;align-items:center;gap:5px;background:var(--bg);border:1.5px solid var(--line);border-radius:14px;padding:10px 11px;margin-left:8px}
.sortwrap svg{width:15px;height:15px;color:var(--sub);flex:none}
.sortwrap select{border:0;background:transparent;font-weight:700;color:var(--ink);font-size:13px;outline:none;max-width:120px}
.chips{display:flex;gap:7px;overflow-x:auto;padding:8px 2px 3px;scrollbar-width:none}
.chips::-webkit-scrollbar{display:none}
.chip{flex:none;border:1.5px solid var(--line);background:#fff;color:var(--sub);border-radius:999px;padding:7px 13px;font-size:13px;font-weight:600;cursor:pointer;white-space:nowrap;transition:.12s}
.chip:hover{border-color:var(--sea)}
.chip.on{background:var(--ink);color:#fff;border-color:var(--ink)}
.chip .ct{opacity:.55;font-weight:700;margin-left:3px;font-size:11px}
.chip.on .ct{opacity:.7}
.chiplabel{flex:none;align-self:center;font-size:11px;font-weight:800;color:#9aa6b2;padding:0 4px 0 2px}
.count{max-width:1180px;margin:0 auto;padding:13px 16px 2px;font-size:13px;color:var(--sub);font-weight:600}
.count b{color:var(--sea);font-weight:800}

.grid{max-width:1180px;margin:0 auto;padding:10px 12px calc(60px + var(--safe-b));display:grid;grid-template-columns:1fr;gap:13px}
@media(min-width:560px){.grid{grid-template-columns:repeat(2,1fr);gap:14px;padding-inline:16px}}
@media(min-width:900px){.grid{grid-template-columns:repeat(3,1fr)}}
@media(min-width:1200px){.grid{grid-template-columns:repeat(4,1fr)}}
.grid.hidden{display:none}
.card{background:var(--card);border-radius:18px;overflow:hidden;box-shadow:var(--shadow);display:flex;flex-direction:column;transition:transform .15s,box-shadow .15s}
.card:active{transform:scale(.99)}
@media(hover:hover){.card:hover{transform:translateY(-3px);box-shadow:0 12px 30px rgba(20,40,70,.13)}}
.thumb{position:relative;aspect-ratio:16/10;background:#dde3ea;overflow:hidden}
.thumb img{width:100%;height:100%;object-fit:cover;transition:transform .4s}
@media(hover:hover){.card:hover .thumb img{transform:scale(1.05)}}
.thumb .ph{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font-size:32px;color:#aeb9c5}
.badge{position:absolute;top:10px;left:10px;padding:5px 10px;border-radius:999px;font-size:11.5px;font-weight:800;color:#fff;box-shadow:0 2px 8px rgba(0,0,0,.18)}
.gbadge{position:absolute;top:10px;right:10px;padding:5px 10px;border-radius:999px;font-size:11.5px;font-weight:700;color:#fff;background:rgba(15,28,42,.62)}
.statusb{position:absolute;bottom:10px;left:10px;padding:4px 9px;border-radius:999px;font-size:11px;font-weight:800;color:#fff}
.body{padding:13px 14px 14px;display:flex;flex-direction:column;gap:7px;flex:1}
.name{font-size:17px;font-weight:800;letter-spacing:-.02em;line-height:1.3}
.hl{font-size:13px;color:var(--sea);font-weight:700;display:flex;gap:6px;align-items:flex-start}
.hl .ic{flex:none;margin-top:1px}
.hl span{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.row{font-size:12.5px;color:var(--sub);display:flex;gap:6px;align-items:flex-start}
.row .ic{flex:none;margin-top:2px;opacity:.7}
.row span{overflow:hidden;display:-webkit-box;-webkit-line-clamp:1;-webkit-box-orient:vertical}
.desc{font-size:12.5px;color:#75808c;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.stat{font-size:11.5px;color:#9aa6b2;font-weight:600;display:flex;gap:11px}
.acts{display:flex;gap:7px;margin-top:auto;padding-top:11px}
.act{flex:1;display:flex;align-items:center;justify-content:center;gap:5px;padding:9px 6px;border-radius:11px;font-size:12.5px;font-weight:700;border:1.5px solid var(--line);color:var(--sub)}
.act svg{width:14px;height:14px}
.act.call{background:var(--sea);border-color:var(--sea);color:#fff}
.act:active{filter:brightness(.96)}

#map{display:none;width:100%;height:calc(100vh - var(--toolsH,260px));min-height:420px;background:#dfe6ee}
#map.show{display:block}
.leaflet-popup-content{margin:0;width:230px!important}
.leaflet-popup-content-wrapper{border-radius:14px;overflow:hidden;padding:0}
.pop{width:230px;font-family:inherit}
.pop .pimg{width:100%;height:118px;object-fit:cover;background:#dde3ea}
.pop .pbody{padding:10px 12px 12px}
.pop .pn{font-size:15px;font-weight:800;color:var(--ink);line-height:1.3;margin-bottom:4px}
.pop .pm{font-size:12px;color:var(--sea);font-weight:700;margin-bottom:4px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.pop .pa{font-size:11.5px;color:var(--sub);line-height:1.4;margin-bottom:8px}
.pop .pacts{display:flex;gap:6px}
.pop .pacts a{flex:1;text-align:center;padding:7px 4px;border-radius:9px;font-size:11.5px;font-weight:700;border:1.5px solid var(--line);color:var(--sub)}
.pop .pacts a.call{background:var(--sea);border-color:var(--sea);color:#fff}
.mk{width:16px;height:16px;border-radius:50% 50% 50% 0;transform:rotate(-45deg);border:2px solid #fff;box-shadow:0 2px 5px rgba(0,0,0,.35)}
.maphint{position:fixed;z-index:900;left:50%;transform:translateX(-50%);bottom:calc(16px + var(--safe-b));background:rgba(15,28,42,.82);color:#fff;font-size:12px;font-weight:600;padding:7px 14px;border-radius:999px;pointer-events:none;opacity:0;transition:.3s}
.maphint.show{opacity:1}
.empty{grid-column:1/-1;text-align:center;padding:70px 20px;color:var(--sub)}
.empty .em{font-size:42px}
.empty p{font-weight:600;margin:12px 0 0}
.top{position:fixed;right:16px;bottom:calc(16px + var(--safe-b));width:46px;height:46px;border-radius:50%;background:var(--ink);color:#fff;display:flex;align-items:center;justify-content:center;box-shadow:0 8px 20px rgba(0,0,0,.25);opacity:0;pointer-events:none;transition:.2s;z-index:1100;cursor:pointer}
.top.show{opacity:1;pointer-events:auto}
footer{max-width:1180px;margin:0 auto;padding:8px 18px calc(30px + var(--safe-b));color:#9aa6b2;font-size:11.5px;line-height:1.6;text-align:center}
footer a{text-decoration:underline}
.locate{position:fixed;left:16px;bottom:calc(16px + var(--safe-b));width:48px;height:48px;border-radius:50%;background:#fff;color:var(--sea);display:flex;align-items:center;justify-content:center;box-shadow:0 6px 18px rgba(0,0,0,.22);z-index:1100;cursor:pointer;border:0;transition:.15s}
.locate.on{background:var(--sea);color:#fff}
.locate:active{transform:scale(.93)}
.locate svg{width:23px;height:23px}
.locate[hidden]{display:none}
.radsel{margin-left:8px}
.dist{color:var(--sea);font-weight:800}
.udot{width:16px;height:16px;border-radius:50%;background:#1a73e8;border:3px solid #fff;box-shadow:0 0 0 2px rgba(26,115,232,.45),0 1px 5px rgba(0,0,0,.4);animation:bfpulse 2s infinite}
@keyframes bfpulse{0%{box-shadow:0 0 0 0 rgba(26,115,232,.5),0 1px 5px rgba(0,0,0,.4)}70%{box-shadow:0 0 0 16px rgba(26,115,232,0),0 1px 5px rgba(0,0,0,.4)}100%{box-shadow:0 0 0 0 rgba(26,115,232,0),0 1px 5px rgba(0,0,0,.4)}}
.dd{position:relative;margin-left:8px;flex:none}
.dd-btn{display:flex;align-items:center;gap:6px;background:var(--bg);border:1.5px solid var(--line);border-radius:14px;padding:10px 11px;font-size:13px;font-weight:700;color:var(--ink);cursor:pointer;white-space:nowrap;max-width:150px}
.dd-btn>span{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.dd-btn .lic{width:15px;height:15px;color:var(--sub);flex:none}
.dd-btn .chev{width:14px;height:14px;color:var(--sub);flex:none;transition:transform .2s}
.dd.open .dd-btn{border-color:var(--sea);background:#fff}
.dd.open .dd-btn .chev{transform:rotate(180deg)}
.dd-panel{position:absolute;right:0;top:calc(100% + 6px);width:208px;background:#fff;border:1px solid var(--line);border-radius:14px;box-shadow:0 14px 34px rgba(20,40,70,.18);padding:6px;z-index:1200;display:none;max-height:70vh;overflow:auto}
.dd.open .dd-panel{display:block}
.dd-h{font-size:11px;font-weight:800;color:#9aa6b2;padding:8px 10px 4px;letter-spacing:.02em}
.dd-opt{display:flex;align-items:center;justify-content:space-between;gap:8px;padding:9px 10px;border-radius:9px;font-size:13.5px;font-weight:600;color:var(--ink);cursor:pointer}
@media(hover:hover){.dd-opt:hover{background:var(--bg)}}
.dd-opt.on{background:rgba(10,110,189,.1);color:var(--sea);font-weight:800}
.dd-opt .ck{width:16px;height:16px;flex:none;opacity:0;color:var(--sea)}
.dd-opt.on .ck{opacity:1}
.dd-div{height:1px;background:var(--line);margin:6px 6px}
</style>
</head>
<body>
<header class="hero"><div class="wrap">
  <div class="topline">
    <div><h1>📍 <span id="brand">부산에 가면</span></h1><p id="subtitle"></p></div>
    <div class="langs" id="langs"><button data-l="ko" class="on">한</button><button data-l="en">EN</button><button data-l="ja">日</button><button data-l="zh">中</button></div>
  </div>
  <div class="tabs" id="tabs"></div>
</div></header>

<div class="tools"><div class="wrap">
  <div class="searchrow">
    <label class="search"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/></svg><input id="q" type="search" inputmode="search" autocomplete="off"></label>
    <div class="viewtog" id="viewtog">
      <button data-v="list" class="on"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"/></svg><span class="vlist"></span></button>
      <button data-v="map"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M9 4 3 6v14l6-2 6 2 6-2V4l-6 2-6-2z"/><path d="M9 4v14M15 6v14"/></svg><span class="vmap"></span></button>
    </div>
  </div>
  <div style="display:flex;align-items:center"><div class="chips" id="cats" style="flex:1"></div>
    <div class="dd" id="dd">
      <button class="dd-btn" id="ddBtn" type="button" aria-haspopup="true" aria-expanded="false"><svg class="lic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M3 6h18M6 12h12M10 18h4"/></svg><span id="ddLabel"></span><svg class="chev" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4"><path d="M6 9l6 6 6-6"/></svg></button>
      <div class="dd-panel" id="ddPanel" role="menu"></div>
    </div>
  </div>
  <div class="chips" id="gus"></div>
</div></div>

<div class="count" id="count"></div>
<main class="grid" id="grid"></main>
<div id="map"></div>
<div class="maphint" id="maphint"></div>
<button class="locate" id="locate" hidden aria-label="내 위치"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3.4"/><path d="M12 2v3.2M12 18.8V22M2 12h3.2M18.8 12H22"/><circle cx="12" cy="12" r="8"/></svg></button>
<div class="top" id="top"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4"><path d="M12 19V5M5 12l7-7 7 7"/></svg></div>
<footer id="footer"></footer>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script>
<script>
const DB=__DATA__;
const TODAY="__TODAY__";
const SEC=[{k:"sights",i:"🏞️"},{k:"food",i:"🍜"},{k:"festival",i:"🎉"},{k:"stay",i:"🏨"},{k:"shopping",i:"🛍️"}];
const PALETTE=["#0e7c86","#d2453b","#e8632c","#3f51b5","#7e57c2","#2e9e5b","#b5762e","#d6457f","#7a8b27","#0a6ebd","#7a8896"];

const SECNAME={
 sights:{ko:"명소",en:"Sights",ja:"名所",zh:"景点"},food:{ko:"음식",en:"Food",ja:"グルメ",zh:"美食"},
 festival:{ko:"축제",en:"Festivals",ja:"祭り",zh:"庆典"},stay:{ko:"숙박",en:"Stay",ja:"宿泊",zh:"住宿"},
 shopping:{ko:"쇼핑",en:"Shopping",ja:"買物",zh:"购物"}};
const GU_I18N={"중구":{en:"Jung-gu",ja:"中区",zh:"中区"},"서구":{en:"Seo-gu",ja:"西区",zh:"西区"},"동구":{en:"Dong-gu",ja:"東区",zh:"东区"},"영도구":{en:"Yeongdo-gu",ja:"影島区",zh:"影岛区"},"부산진구":{en:"Busanjin-gu",ja:"釜山鎮区",zh:"釜山镇区"},"동래구":{en:"Dongnae-gu",ja:"東莱区",zh:"东莱区"},"남구":{en:"Nam-gu",ja:"南区",zh:"南区"},"북구":{en:"Buk-gu",ja:"北区",zh:"北区"},"해운대구":{en:"Haeundae-gu",ja:"海雲台区",zh:"海云台区"},"사하구":{en:"Saha-gu",ja:"沙下区",zh:"沙下区"},"금정구":{en:"Geumjeong-gu",ja:"金井区",zh:"金井区"},"강서구":{en:"Gangseo-gu",ja:"江西区",zh:"江西区"},"연제구":{en:"Yeonje-gu",ja:"蓮堤区",zh:"莲堤区"},"수영구":{en:"Suyeong-gu",ja:"水営区",zh:"水营区"},"사상구":{en:"Sasang-gu",ja:"沙上区",zh:"沙上区"},"기장군":{en:"Gijang-gun",ja:"機張郡",zh:"机张郡"}};
const CAT_I18N={
 "카페·베이커리":{en:"Cafe & Bakery",ja:"カフェ",zh:"咖啡"},"일식":{en:"Japanese",ja:"和食",zh:"日料"},"해산물·회":{en:"Seafood",ja:"海鮮",zh:"海鲜"},"고기·구이":{en:"BBQ & Grill",ja:"焼肉",zh:"烤肉"},"중식":{en:"Chinese",ja:"中華",zh:"中餐"},"양식·세계요리":{en:"Western & World",ja:"洋食",zh:"西餐"},"분식·주점":{en:"Snacks & Pub",ja:"軽食・居酒屋",zh:"小吃"},"면·국물":{en:"Noodles & Soup",ja:"麺類",zh:"面食"},"한식·백반":{en:"Korean",ja:"韓定食",zh:"韩餐"},
 "바다·해변":{en:"Sea & Beach",ja:"海・ビーチ",zh:"海滨"},"전망·야경":{en:"Views & Night",ja:"展望・夜景",zh:"观景"},"역사·문화재":{en:"History",ja:"歴史",zh:"历史"},"박물관·전시":{en:"Museums",ja:"博物館",zh:"博物馆"},"테마·체험":{en:"Themes",ja:"テーマ",zh:"主题"},"공원·자연":{en:"Parks & Nature",ja:"公園・自然",zh:"公园"},"거리·시장":{en:"Streets",ja:"街・市場",zh:"街市"},
 "백화점·몰":{en:"Malls",ja:"百貨店・モール",zh:"商场"},"전통시장":{en:"Markets",ja:"伝統市場",zh:"传统市场"},"면세점":{en:"Duty Free",ja:"免税店",zh:"免税店"},"거리·테마":{en:"Shopping Streets",ja:"商店街",zh:"商业街"},
 "호텔":{en:"Hotel",ja:"ホテル",zh:"酒店"},"리조트·콘도":{en:"Resort & Condo",ja:"リゾート",zh:"度假村"},"게스트하우스":{en:"Guesthouse",ja:"ゲストハウス",zh:"青年旅舍"},"모텔":{en:"Motel",ja:"モーテル",zh:"汽车旅馆"},"펜션·민박":{en:"Pension",ja:"ペンション",zh:"民宿"},
 "축제·행사":{en:"Festival & Event",ja:"祭り・イベント",zh:"庆典活动"},"기타":{en:"Others",ja:"その他",zh:"其他"}};
const UI={
 ko:{brand:"부산에 가면",sub:(s,n)=>`${SECNAME[s].ko} ${n}곳 · 구·군과 종류로 찾아보세요`,src:`데이터 출처: <a href="https://www.visitbusan.net/index.do?menuCd=DOM_000000201001000000" target="_blank" rel="noopener">부산관광포털 비짓부산</a> · '부산에가면'`,search:"이름·지역·키워드 검색",list:"목록",map:"지도",catLabel:"종류",guLabel:"지역",all:"전체",count:n=>`<b>${n}</b>곳`,call:"전화",mapBtn:"길찾기",detail:"상세",home:"홈페이지",sorts:{def:"기본순",view:"인기순",like:"좋아요순",name:"가나다순"},empty:"조건에 맞는 곳이 없어요.<br>검색어·필터·섹션을 바꿔보세요.",hint:"핀을 누르면 정보가 나와요",ongoing:"진행중",upcoming:"예정",ended:"종료",foot:`비짓부산 공개 정보를 정리한 것으로 실제와 다를 수 있습니다. 방문 전 운영시간·휴무·행사기간을 확인하세요.<br>종류는 자동 분류 · 숙박·中文은 일부 정보가 한/영으로 표기 · 지도 © OpenStreetMap·CARTO · 갱신 __UPDATED__`},
 en:{brand:"When in Busan",sub:(s,n)=>`${n} ${SECNAME[s].en.toLowerCase()} spots · Filter by district & type`,src:`Data: <a href="https://www.visitbusan.net/index.do?menuCd=DOM_000000201001000000" target="_blank" rel="noopener">VisitBusan portal</a>`,search:"Search name · area · keyword",list:"List",map:"Map",catLabel:"Type",guLabel:"Area",all:"All",count:n=>`<b>${n}</b> places`,call:"Call",mapBtn:"Directions",detail:"Details",home:"Website",sorts:{def:"Default",view:"Popular",like:"Most liked",name:"Name A–Z"},empty:"Nothing matches.<br>Try another keyword, filter or section.",hint:"Tap a pin for details",ongoing:"Ongoing",upcoming:"Upcoming",ended:"Ended",foot:`Compiled from VisitBusan public data; details may differ. Check hours/closing/festival dates before visiting.<br>Type is auto-classified · Some stay info shown in Korean · Map © OpenStreetMap, CARTO · Updated __UPDATED__`},
 ja:{brand:"釜山に行ったら",sub:(s,n)=>`${SECNAME[s].ja} ${n}件 · 区・郡と種類で検索`,src:`データ出典: <a href="https://www.visitbusan.net/index.do?menuCd=DOM_000000201001000000" target="_blank" rel="noopener">VisitBusan 公式観光ポータル</a>`,search:"名前・エリア・キーワード",list:"リスト",map:"地図",catLabel:"種類",guLabel:"エリア",all:"すべて",count:n=>`<b>${n}</b>件`,call:"電話",mapBtn:"道案内",detail:"詳細",home:"ホームページ",sorts:{def:"標準",view:"人気順",like:"いいね順",name:"名前順"},empty:"該当なし。<br>キーワード・フィルター・セクションを変更してください。",hint:"ピンをタップで情報表示",ongoing:"開催中",upcoming:"予定",ended:"終了",foot:`VisitBusanの公開データを整理。実際と異なる場合があります。訪問前に営業時間・定休日・開催期間をご確認ください。<br>種類は自動分類 · 宿泊・中文は一部が韓/英表記 · 地図 © OpenStreetMap・CARTO · 更新 __UPDATED__`},
 zh:{brand:"来釜山",sub:(s,n)=>`${SECNAME[s].zh} ${n}处 · 按区·郡和类型筛选`,src:`数据来源: <a href="https://www.visitbusan.net/index.do?menuCd=DOM_000000201001000000" target="_blank" rel="noopener">VisitBusan 官方旅游门户</a>`,search:"搜索名称·地区·关键词",list:"列表",map:"地图",catLabel:"类型",guLabel:"地区",all:"全部",count:n=>`<b>${n}</b>处`,call:"电话",mapBtn:"导航",detail:"详情",home:"官网",sorts:{def:"默认",view:"人气",like:"点赞",name:"名称"},empty:"没有符合条件的结果。<br>请更换关键词·筛选或栏目。",hint:"点击图钉查看信息",ongoing:"进行中",upcoming:"即将",ended:"已结束",foot:`整理自VisitBusan公开数据，可能与实际不符，到访前请确认营业·休息·活动期间。<br>类型为自动分类 · 部分详情以韩/英显示 · 地图 © OpenStreetMap·CARTO · 更新 __UPDATED__`}};

const LOCT={
 ko:{me:"내 위치",nearest:"거리순",within:"이내",all:"전체",nearme:"내 위치 기준",sortLabel:"정렬",err:"위치 정보를 가져올 수 없어요. 브라우저 위치 권한을 확인해 주세요.",locating:"현재 위치 확인 중…",here:"현재 위치"},
 en:{me:"My location",nearest:"Nearest",within:"away",all:"All",nearme:"Near me",sortLabel:"Sort",err:"Couldn't get your location. Please allow location access.",locating:"Locating…",here:"You are here"},
 ja:{me:"現在地",nearest:"近い順",within:"以内",all:"すべて",nearme:"現在地から",sortLabel:"並び替え",err:"位置情報を取得できません。位置情報の許可をご確認ください。",locating:"現在地を取得中…",here:"現在地"},
 zh:{me:"我的位置",nearest:"距离最近",within:"以内",all:"全部",nearme:"我的位置",sortLabel:"排序",err:"无法获取位置，请允许定位权限。",locating:"定位中…",here:"我的位置"}};
function LT(){return LOCT[state.lang]}
const state={sec:"food",q:"",cat:"전체",gu:"전체",sort:"def",view:"list",radius:0,loc:null,lang:(()=>{const s=localStorage.getItem("bf_lang");if(s)return s;const n=(navigator.language||"ko").slice(0,2);return ["en","ja","zh"].includes(n)?n:"ko"})()};
function tr(o){if(!o)return "";const L=state.lang;if(L==="zh")return o.en||o.ko||"";return o[L]||o.en||o.ko||""}
function catName(k){const m=CAT_I18N[k];if(!m)return k;return state.lang==="ko"?k:(m[state.lang]||k)}
function guName(k){const m=GU_I18N[k];if(!m)return k;return state.lang==="ko"?k:(m[state.lang]||k)}
function secName(k){return SECNAME[k][state.lang]||SECNAME[k].ko}
function U(){return UI[state.lang]}
const rows=()=>DB[state.sec]||[];
const catColor=(()=>{const map={};return k=>{if(!(k in map)){const keys=Object.keys(map);map[k]=PALETTE[keys.length%PALETTE.length]}return map[k]}})();

// ── 현재 위치 ──
function haversine(la1,lo1,la2,lo2){const R=6371,d=x=>x*Math.PI/180;const dla=d(la2-la1),dlo=d(lo2-lo1);const a=Math.sin(dla/2)**2+Math.cos(d(la1))*Math.cos(d(la2))*Math.sin(dlo/2)**2;return 2*R*Math.asin(Math.sqrt(a))}
function distKm(r){return state.loc&&r.lat!=null?haversine(state.loc.lat,state.loc.lng,r.lat,r.lng):null}
function fmtDist(km){if(km==null)return"";return km<1?Math.round(km*1000)+"m":(km<10?km.toFixed(1):Math.round(km))+"km"}
let toastT;function toast(m){const h=document.getElementById("maphint");h.innerHTML=m;h.classList.add("show");clearTimeout(toastT);toastT=setTimeout(()=>h.classList.remove("show"),2800)}
let userMarker,userCircle;
function showUser(){if(!mapReady||!state.loc)return;const ll=[state.loc.lat,state.loc.lng];
  if(userMarker){userMarker.setLatLng(ll);userCircle.setLatLng(ll).setRadius(state.loc.acc||40)}
  else{userMarker=L.marker(ll,{icon:L.divIcon({className:"",html:'<div class="udot"></div>',iconSize:[16,16],iconAnchor:[8,8]}),zIndexOffset:2000,interactive:false}).addTo(map);
    userCircle=L.circle(ll,{radius:state.loc.acc||40,color:"#1a73e8",weight:1,fillColor:"#1a73e8",fillOpacity:.1,interactive:false}).addTo(map)}}
function locate(){
  if(!navigator.geolocation){toast(LT().err);return}
  toast(LT().locating);
  navigator.geolocation.getCurrentPosition(p=>{
    state.loc={lat:p.coords.latitude,lng:p.coords.longitude,acc:p.coords.accuracy};
    document.getElementById("locate").classList.add("on");
    if(state.view==="map"){initMap();showUser();map.setView([state.loc.lat,state.loc.lng],14)}
    renderDD();render();
  },()=>{toast(LT().err);let ch=false;if(state.sort==="dist"){state.sort="def";ch=true}if(state.radius>0){state.radius=0;ch=true}if(ch){renderDD();render()}},{enableHighAccuracy:true,timeout:9000,maximumAge:60000})}
const CK='<svg class="ck" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6"><path d="M5 12l5 5L20 6"/></svg>';
function sortName(k){return k==="dist"?LT().nearest:U().sorts[k]}
function ddLabelText(){return sortName(state.sort)+(state.radius>0?` · ${state.radius}km`:"")}
function renderDD(){const lt=LT();
  let h=`<div class="dd-h">${lt.sortLabel}</div>`;
  ["def","view","like","name","dist"].forEach(k=>h+=`<div class="dd-opt${state.sort===k?" on":""}" data-g="s" data-v="${k}"><span>${sortName(k)}</span>${CK}</div>`);
  h+=`<div class="dd-div"></div><div class="dd-h">📍 ${lt.nearme}</div>`;
  [[0,lt.all]].concat([1,3,5,10].map(n=>[n,`${n}km ${lt.within}`])).forEach(([v,lab])=>h+=`<div class="dd-opt${state.radius===v?" on":""}" data-g="r" data-v="${v}"><span>${lab}</span>${CK}</div>`);
  document.getElementById("ddPanel").innerHTML=h;
  document.getElementById("ddLabel").textContent=ddLabelText();
}
function ddOpen(o){document.getElementById("dd").classList.toggle("open",o);document.getElementById("ddBtn").setAttribute("aria-expanded",o?"true":"false")}

const PIN='<svg class="ic" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 21s-7-6.3-7-11a7 7 0 0114 0c0 4.7-7 11-7 11z"/><circle cx="12" cy="10" r="2.4"/></svg>';
const CLK='<svg class="ic" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>';
const STAR='<svg class="ic" width="13" height="13" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2l2.9 6.3 6.8.6-5.1 4.5 1.5 6.7L12 17.3 5.9 20.6l1.5-6.7L2.3 8.9l6.8-.6z"/></svg>';
const TAG='<svg class="ic" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 12l-8 8-9-9V3h8z"/><circle cx="7.5" cy="7.5" r="1.3"/></svg>';
const esc=s=>(s||"").replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const norm=s=>(s||"").toLowerCase().replace(/\s+/g,"");

function tally(key){const m=new Map();rows().forEach(r=>{const v=key==="c"?r.c:r.g;if(v)m.set(v,(m.get(v)||0)+1)});return [...m.entries()].sort((a,b)=>b[1]-a[1])}
function buildChips(elId,key,stateKey,nameFn){
  const el=document.getElementById(elId),label=key==="c"?U().catLabel:U().guLabel;
  let h=`<span class="chiplabel">${label}</span><button class="chip${state[stateKey]==="전체"?" on":""}" data-v="전체">${U().all}<i class="ct">${rows().length}</i></button>`;
  tally(key).forEach(([v,n])=>h+=`<button class="chip${state[stateKey]===v?" on":""}" data-v="${esc(v)}">${esc(nameFn(v))}<i class="ct">${n}</i></button>`);
  el.innerHTML=h;
  el.onclick=e=>{const b=e.target.closest(".chip");if(!b)return;state[stateKey]=b.dataset.v;[...el.children].forEach(c=>c.classList&&c.classList.toggle("on",c===b));render()};
}
function fstatus(r){if(!r.ps&&!r.pe)return null;if(r.pe&&r.pe<TODAY)return "ended";if(r.ps&&r.ps>TODAY)return "upcoming";return "ongoing"}
function filtered(){
  const q=norm(state.q);
  let list=rows().filter(r=>{
    if(state.cat!=="전체"&&r.c!==state.cat)return false;
    if(state.gu!=="전체"&&r.g!==state.gu)return false;
    if(state.radius>0&&state.loc){const dk=distKm(r);if(dk==null||dk>state.radius)return false}
    if(q){const hay=norm(tr(r.n)+tr(r.a)+r.g+r.c+(r.n&&r.n.ko||"")+tr(r.d));if(!hay.includes(q))return false}
    return true;
  });
  const s=state.sort;
  if(s==="dist"&&state.loc)list=[...list].sort((a,b)=>(distKm(a)??1e9)-(distKm(b)??1e9));
  else if(s==="view")list=[...list].sort((a,b)=>(b.v||0)-(a.v||0));
  else if(s==="like")list=[...list].sort((a,b)=>(b.l||0)-(a.l||0));
  else if(s==="name")list=[...list].sort((a,b)=>tr(a.n).localeCompare(tr(b.n),state.lang==="zh"?"zh":state.lang));
  return list;
}
function highlight(r){
  if(state.sec==="food"&&r.m)return {ic:'<svg class="ic" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 3v7a2 2 0 002 2 2 2 0 002-2V3M7 12v9M17 3c-1.5 0-2.5 2-2.5 5s1 4 2.5 4v9"/></svg>',t:tr(r.m).split("\n").filter(Boolean).join(" · ")};
  if(state.sec==="festival"&&r.pd)return {ic:CLK,t:r.pd};
  if(state.sec==="stay"&&r.ty)return {ic:TAG,t:tr(r.ty)};
  if(r.fee)return {ic:TAG,t:tr(r.fee)};
  return null;
}
function card(r){
  const col=catColor(r.c);
  const hl=highlight(r);
  const hrs=esc(tr(r.h)),cls=(tr(r.x)||"").trim();
  const closedTxt=cls&&!/^(연중무휴|연중 무휴|Open (365|every)|無休)/i.test(cls)?" · "+esc(cls):"";
  const tel=(r.p||"").replace(/[^0-9+]/g,"");
  const mapq=encodeURIComponent(tr(r.n)+" "+r.g);
  const st=state.sec==="festival"?fstatus(r):null;
  const stColor={ongoing:"#2e9e5b",upcoming:"#0a6ebd",ended:"#9aa6b2"}[st];
  const img=r.t?`<img loading="lazy" src="${esc(r.t)}" alt="${esc(tr(r.n))}" onerror="this.style.display='none';this.nextElementSibling.style.display='flex'"><div class="ph" style="display:none">📍</div>`:`<div class="ph">📍</div>`;
  return `<article class="card"><div class="thumb">${img}<span class="badge" style="background:${col}">${esc(catName(r.c))}</span>${r.g?`<span class="gbadge">${esc(guName(r.g))}</span>`:""}${st?`<span class="statusb" style="background:${stColor}">${U()[st]}</span>`:""}</div>
  <div class="body"><a class="name" href="${esc(r.u)}" target="_blank" rel="noopener">${esc(tr(r.n))}</a>
  ${hl&&hl.t?`<div class="hl">${hl.ic}<span>${esc(hl.t)}</span></div>`:""}
  ${(tr(r.a)||state.loc)?`<div class="row">${PIN}<span>${state.loc&&distKm(r)!=null?`<span class="dist">${fmtDist(distKm(r))}</span> · `:""}${esc(tr(r.a))}</span></div>`:""}
  ${hrs&&state.sec!=="festival"?`<div class="row">${CLK}<span>${hrs}${closedTxt}</span></div>`:""}
  ${tr(r.d)?`<div class="desc">${esc(tr(r.d))}</div>`:""}
  ${(r.v||r.l)?`<div class="stat">${r.v?"👁 "+r.v.toLocaleString():""} ${r.l?"&nbsp; ♥ "+r.l:""}</div>`:""}
  <div class="acts">${tel?`<a class="act call" href="tel:${tel}"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 16.9v3a2 2 0 01-2.2 2 19.8 19.8 0 01-8.6-3 19.5 19.5 0 01-6-6 19.8 19.8 0 01-3-8.6A2 2 0 014.1 2h3a2 2 0 012 1.7c.1.9.3 1.8.6 2.6a2 2 0 01-.5 2.1L8 9.6a16 16 0 006 6l1.2-1.2a2 2 0 012.1-.5c.8.3 1.7.5 2.6.6a2 2 0 011.7 2z"/></svg>${U().call}</a>`:""}
  <a class="act" href="https://map.kakao.com/?q=${mapq}" target="_blank" rel="noopener">${PIN.replace('class="ic" ','')}${U().mapBtn}</a>
  <a class="act" href="${esc(r.u)}" target="_blank" rel="noopener">${U().detail}</a></div></div></article>`;
}

let map,cluster,mapReady=false;
function initMap(){if(mapReady)return;map=L.map("map",{zoomControl:true}).setView([35.16,129.07],11);
  L.tileLayer("https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",{attribution:'© <a href="https://openstreetmap.org/copyright">OpenStreetMap</a> · © <a href="https://carto.com/">CARTO</a>',subdomains:"abcd",maxZoom:19}).addTo(map);
  cluster=L.markerClusterGroup({maxClusterRadius:48,showCoverageOnHover:false});map.addLayer(cluster);mapReady=true}
function popHtml(r){const tel=(r.p||"").replace(/[^0-9+]/g,"");const hl=highlight(r);const mapq=encodeURIComponent(tr(r.n)+" "+r.g);
  return `<div class="pop">${r.t?`<img class="pimg" src="${esc(r.t)}" alt="" onerror="this.style.display='none'">`:""}<div class="pbody"><div class="pn">${esc(tr(r.n))}</div>${hl&&hl.t?`<div class="pm">${esc(hl.t)}</div>`:""}<div class="pa">${state.loc&&distKm(r)!=null?`<span class="dist">${fmtDist(distKm(r))}</span> · `:""}${esc(catName(r.c))}${r.g?" · "+esc(guName(r.g)):""}<br>${esc(tr(r.a))}</div><div class="pacts">${tel?`<a class="call" href="tel:${tel}">${U().call}</a>`:""}<a href="https://map.kakao.com/?q=${mapq}" target="_blank" rel="noopener">${U().mapBtn}</a><a href="${esc(r.u)}" target="_blank" rel="noopener">${U().detail}</a></div></div></div>`}
function renderMap(list){initMap();cluster.clearLayers();const ms=[];
  list.forEach(r=>{if(r.lat==null||r.lng==null)return;const col=catColor(r.c);
    const m=L.marker([r.lat,r.lng],{icon:L.divIcon({className:"",html:`<div class="mk" style="background:${col}"></div>`,iconSize:[16,16],iconAnchor:[8,15],popupAnchor:[0,-14]})});
    m.bindPopup(popHtml(r));ms.push(m)});
  cluster.addLayers(ms);setTimeout(()=>map.invalidateSize(),60);
  if(ms.length){try{const b=cluster.getBounds();b.isValid()&&map.fitBounds(b.pad(.12),{maxZoom:14})}catch(e){}}}

function render(){const list=filtered();document.getElementById("count").innerHTML=U().count(list.length);
  if(state.view==="map")renderMap(list);
  else document.getElementById("grid").innerHTML=list.length?list.map(card).join(""):`<div class="empty"><div class="em">🔍</div><p>${U().empty}</p></div>`}

function setToolsH(){document.documentElement.style.setProperty("--toolsH",(document.querySelector(".tools").offsetHeight+document.querySelector(".hero").offsetHeight)+"px")}
function buildTabs(){document.getElementById("tabs").innerHTML=SEC.map(s=>`<button class="tab${s.k===state.sec?" on":""}" data-s="${s.k}">${s.i} ${secName(s.k)}<span class="tn">${(DB[s.k]||[]).length}</span></button>`).join("")}
function applyLang(){const u=U();document.documentElement.lang=state.lang;
  document.getElementById("brand").textContent=u.brand;
  document.getElementById("subtitle").textContent=u.sub(state.sec,rows().length);
  document.getElementById("q").placeholder=u.search;
  document.querySelector(".vlist").textContent=u.list;document.querySelector(".vmap").textContent=u.map;
  document.getElementById("footer").innerHTML=u.foot+" · "+u.src;
  document.getElementById("maphint").innerHTML=u.hint;
  renderDD();
  document.getElementById("locate").setAttribute("aria-label",LT().me);
  document.querySelectorAll("#langs button").forEach(b=>b.classList.toggle("on",b.dataset.l===state.lang));
  buildTabs();buildChips("cats","c","cat",catName);buildChips("gus","g","gu",guName);render();setToolsH()}

function switchSection(sec){state.sec=sec;state.cat="전체";state.gu="전체";state.q="";document.getElementById("q").value="";
  document.getElementById("subtitle").textContent=U().sub(sec,rows().length);
  buildTabs();buildChips("cats","c","cat",catName);buildChips("gus","g","gu",guName);
  if(mapReady)try{map.closePopup()}catch(e){}
  render();window.scrollTo({top:0,behavior:"instant"});setToolsH()}
function setView(v){state.view=v;document.querySelectorAll("#viewtog button").forEach(b=>b.classList.toggle("on",b.dataset.v===v));
  document.getElementById("grid").classList.toggle("hidden",v==="map");document.getElementById("map").classList.toggle("show",v==="map");
  document.getElementById("locate").hidden=(v!=="map");
  render();
  if(v==="map"){if(state.loc)showUser();toast(U().hint)}}

let t;document.getElementById("q").addEventListener("input",e=>{clearTimeout(t);state.q=e.target.value;t=setTimeout(render,120)});
document.getElementById("ddBtn").addEventListener("click",e=>{e.stopPropagation();ddOpen(!document.getElementById("dd").classList.contains("open"))});
document.getElementById("ddPanel").addEventListener("click",e=>{e.stopPropagation();const o=e.target.closest(".dd-opt");if(!o)return;
  const g=o.dataset.g,v=o.dataset.v;let need=false;
  if(g==="s"){state.sort=v;if(v==="dist"&&!state.loc)need=true}
  else{state.radius=+v;if(+v>0&&!state.loc)need=true}
  renderDD();if(need)locate();else render()});
document.addEventListener("click",e=>{if(!e.target.closest("#dd"))ddOpen(false)});
document.getElementById("locate").addEventListener("click",()=>{if(state.sort==="def")state.sort="dist";renderDD();locate()});
document.getElementById("viewtog").addEventListener("click",e=>{const b=e.target.closest("button");if(b)setView(b.dataset.v)});
document.getElementById("tabs").addEventListener("click",e=>{const b=e.target.closest(".tab");if(b&&b.dataset.s!==state.sec)switchSection(b.dataset.s)});
document.getElementById("langs").addEventListener("click",e=>{const b=e.target.closest("button");if(!b)return;state.lang=b.dataset.l;localStorage.setItem("bf_lang",state.lang);applyLang()});
const topBtn=document.getElementById("top");addEventListener("scroll",()=>topBtn.classList.toggle("show",state.view==="list"&&scrollY>600),{passive:true});
topBtn.addEventListener("click",()=>scrollTo({top:0,behavior:"smooth"}));addEventListener("resize",setToolsH);
applyLang();
</script>
</body>
</html>"""

out = (HTML.replace("__DATA__", data_js).replace("__TOTAL__", str(total))
           .replace("__TODAY__", updated).replace("__UPDATED__", updated))
with open("index.html", "w", encoding="utf-8") as f:
    f.write(out)
print(f"index.html 생성 ({len(out):,} bytes)")
