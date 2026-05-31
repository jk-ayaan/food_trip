#!/usr/bin/env python3
"""data.json → index.html : 다국어(한·영·일·중) + 지도(Leaflet/OSM) 부산 맛집 페이지."""
import json, datetime

rows = json.load(open("data.json", encoding="utf-8"))


def ml(i18n, field, ko_fallback=""):
    ko = i18n["ko"].get(field) or ko_fallback
    return {"ko": ko, "en": i18n["en"].get(field, ""), "ja": i18n["ja"].get(field, "")}


slim = []
for r in rows:
    i = r["i18n"]
    slim.append({
        "n": ml(i, "name", r.get("name", "")),
        "m": ml(i, "menu", r.get("menu", "")),
        "a": ml(i, "address", r.get("address", "")),
        "h": ml(i, "hours", r.get("hours", "")),
        "x": ml(i, "closed", r.get("closed", "")),
        "d": ml(i, "desc", r.get("desc", "")),
        "c": r.get("category", "기타"),
        "g": r.get("district", ""),
        "p": r.get("phone", ""),
        "t": r.get("thumb", ""),
        "lat": r.get("lat"), "lng": r.get("lng"),
        "v": r.get("views", 0), "l": r.get("likes", 0),
        "u": r.get("detail_url", ""),
    })

data_js = json.dumps(slim, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
updated = datetime.date.today().isoformat()

HTML = r"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#0a6ebd">
<meta name="description" content="부산광역시 맛집 __COUNT__곳 지도·다국어 가이드 — 구·군과 음식 종류로 찾기. 출처 부산의 맛(부산광역시, 2026)·비짓부산.">
<title>부산의 맛 · Taste of Busan</title>
<link rel="preconnect" href="https://cdn.jsdelivr.net">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css">
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css">
<style>
:root{
  --bg:#eef1f5; --card:#fff; --ink:#16202c; --sub:#5d6b7a; --line:#e6eaf0;
  --sea:#0a6ebd; --sea2:#0fa3b1; --shadow:0 6px 22px rgba(20,40,70,.08);
  --safe-t:env(safe-area-inset-top); --safe-b:env(safe-area-inset-bottom);
}
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
html,body{margin:0}
body{font-family:"Pretendard","Pretendard Variable",-apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo","Hiragino Kaku Gothic ProN","Microsoft YaHei","Malgun Gothic",system-ui,sans-serif;
  background:var(--bg);color:var(--ink);line-height:1.5;-webkit-text-size-adjust:100%}
a{color:inherit;text-decoration:none}
img{display:block}

.hero{background:linear-gradient(135deg,var(--sea) 0%,var(--sea2) 100%);color:#fff;padding:calc(18px + var(--safe-t)) 18px 16px}
.hero .wrap{max-width:1180px;margin:0 auto}
.hero .topline{display:flex;justify-content:space-between;align-items:flex-start;gap:12px}
.hero h1{margin:0;font-size:23px;font-weight:800;letter-spacing:-.02em;display:flex;align-items:center;gap:8px}
.hero p{margin:6px 0 0;font-size:13px;opacity:.93;font-weight:500}
.hero .src{margin-top:9px;font-size:11px;opacity:.78;line-height:1.5}
.hero .src a{text-decoration:underline;text-underline-offset:2px}
.langs{display:flex;gap:4px;background:rgba(255,255,255,.16);border-radius:999px;padding:3px;flex:none}
.langs button{border:0;background:transparent;color:#fff;font-weight:700;font-size:12px;padding:6px 9px;border-radius:999px;cursor:pointer;opacity:.8;white-space:nowrap}
.langs button.on{background:#fff;color:var(--sea);opacity:1}

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
.sortwrap select{border:0;background:transparent;font-weight:700;color:var(--ink);font-size:13px;outline:none}

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
.thumb .ph{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font-size:30px;color:#aeb9c5}
.badge{position:absolute;top:10px;left:10px;padding:5px 10px;border-radius:999px;font-size:11.5px;font-weight:800;color:#fff;box-shadow:0 2px 8px rgba(0,0,0,.18)}
.gbadge{position:absolute;top:10px;right:10px;padding:5px 10px;border-radius:999px;font-size:11.5px;font-weight:700;color:#fff;background:rgba(15,28,42,.62)}
.body{padding:13px 14px 14px;display:flex;flex-direction:column;gap:7px;flex:1}
.name{font-size:17px;font-weight:800;letter-spacing:-.02em;line-height:1.3}
.menu{font-size:13px;color:var(--sea);font-weight:700;display:flex;gap:6px;align-items:flex-start}
.menu .ic{flex:none;margin-top:1px}
.menu span{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
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

/* 지도 */
#map{display:none;width:100%;height:calc(100vh - var(--toolsH,210px));min-height:420px;background:#dfe6ee}
#map.show{display:block}
.leaflet-popup-content{margin:0;width:230px!important}
.leaflet-popup-content-wrapper{border-radius:14px;overflow:hidden;padding:0}
.pop{width:230px;font-family:inherit}
.pop .pimg{width:100%;height:120px;object-fit:cover;background:#dde3ea}
.pop .pbody{padding:10px 12px 12px}
.pop .pn{font-size:15px;font-weight:800;color:var(--ink);line-height:1.3;margin-bottom:4px}
.pop .pm{font-size:12px;color:var(--sea);font-weight:700;margin-bottom:4px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.pop .pa{font-size:11.5px;color:var(--sub);line-height:1.4;margin-bottom:8px}
.pop .pacts{display:flex;gap:6px}
.pop .pacts a{flex:1;text-align:center;padding:7px 4px;border-radius:9px;font-size:11.5px;font-weight:700;border:1.5px solid var(--line);color:var(--sub)}
.pop .pacts a.call{background:var(--sea);border-color:var(--sea);color:#fff}
.mk{width:16px;height:16px;border-radius:50% 50% 50% 0;transform:rotate(-45deg);border:2px solid #fff;box-shadow:0 2px 5px rgba(0,0,0,.35)}
.maphint{position:absolute;z-index:900;left:50%;transform:translateX(-50%);bottom:calc(14px + var(--safe-b));background:rgba(15,28,42,.82);color:#fff;font-size:12px;font-weight:600;padding:7px 14px;border-radius:999px;pointer-events:none;opacity:0;transition:.3s}
.maphint.show{opacity:1}

.empty{grid-column:1/-1;text-align:center;padding:70px 20px;color:var(--sub)}
.empty .em{font-size:42px}
.empty p{font-weight:600;margin:12px 0 0}
.top{position:fixed;right:16px;bottom:calc(16px + var(--safe-b));width:46px;height:46px;border-radius:50%;background:var(--ink);color:#fff;display:flex;align-items:center;justify-content:center;box-shadow:0 8px 20px rgba(0,0,0,.25);opacity:0;pointer-events:none;transition:.2s;z-index:1100;cursor:pointer}
.top.show{opacity:1;pointer-events:auto}
footer{max-width:1180px;margin:0 auto;padding:8px 18px calc(30px + var(--safe-b));color:#9aa6b2;font-size:11.5px;line-height:1.6;text-align:center}
footer a{text-decoration:underline}
</style>
</head>
<body>

<header class="hero">
  <div class="wrap">
    <div class="topline">
      <div>
        <h1>🍜 <span id="brand">부산의 맛</span></h1>
        <p id="subtitle"></p>
      </div>
      <div class="langs" id="langs">
        <button data-l="ko" class="on">한</button>
        <button data-l="en">EN</button>
        <button data-l="ja">日</button>
        <button data-l="zh">中</button>
      </div>
    </div>
    <div class="src" id="src"></div>
  </div>
</header>

<div class="tools">
  <div class="wrap">
    <div class="searchrow">
      <label class="search">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/></svg>
        <input id="q" type="search" inputmode="search" autocomplete="off">
      </label>
      <div class="viewtog" id="viewtog">
        <button data-v="list" class="on"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"/></svg><span class="vlist"></span></button>
        <button data-v="map"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M9 4 3 6v14l6-2 6 2 6-2V4l-6 2-6-2z"/><path d="M9 4v14M15 6v14"/></svg><span class="vmap"></span></button>
      </div>
    </div>
    <div style="display:flex;align-items:center">
      <div class="chips" id="cats" style="flex:1"></div>
      <div class="sortwrap">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M3 6h18M6 12h12M10 18h4"/></svg>
        <select id="sort"></select>
      </div>
    </div>
    <div class="chips" id="gus"></div>
  </div>
</div>

<div class="count" id="count"></div>
<main class="grid" id="grid"></main>
<div id="map"></div>
<div class="maphint" id="maphint"></div>

<div class="top" id="top"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4"><path d="M12 19V5M5 12l7-7 7 7"/></svg></div>
<footer id="footer"></footer>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script>
<script>
const DATA = __DATA__;

const CAT_COLORS={"카페·베이커리":"#b5762e","일식":"#3f51b5","해산물·회":"#0e7c86","고기·구이":"#d2453b","중식":"#e8632c","양식·세계요리":"#7e57c2","분식·주점":"#d6457f","면·국물":"#2e9e5b","한식·백반":"#7a8b27","기타":"#7a8896"};

const CAT_I18N={
 "카페·베이커리":{ko:"카페·베이커리",en:"Cafe & Bakery",ja:"カフェ・ベーカリー",zh:"咖啡·烘焙"},
 "일식":{ko:"일식",en:"Japanese",ja:"和食",zh:"日本料理"},
 "해산물·회":{ko:"해산물·회",en:"Seafood",ja:"海鮮・刺身",zh:"海鲜·生鱼片"},
 "고기·구이":{ko:"고기·구이",en:"BBQ & Grill",ja:"焼肉・グリル",zh:"烤肉·烧烤"},
 "중식":{ko:"중식",en:"Chinese",ja:"中華",zh:"中餐"},
 "양식·세계요리":{ko:"양식·세계요리",en:"Western & World",ja:"洋食・世界料理",zh:"西餐·各国料理"},
 "분식·주점":{ko:"분식·주점",en:"Snacks & Pub",ja:"軽食・居酒屋",zh:"小吃·酒馆"},
 "면·국물":{ko:"면·국물",en:"Noodles & Soup",ja:"麺・スープ",zh:"面·汤"},
 "한식·백반":{ko:"한식·백반",en:"Korean",ja:"韓定食",zh:"韩餐"},
 "기타":{ko:"기타",en:"Others",ja:"その他",zh:"其他"}};

const GU_I18N={
 "중구":{ko:"중구",en:"Jung-gu",ja:"中区",zh:"中区"},"서구":{ko:"서구",en:"Seo-gu",ja:"西区",zh:"西区"},
 "동구":{ko:"동구",en:"Dong-gu",ja:"東区",zh:"东区"},"영도구":{ko:"영도구",en:"Yeongdo-gu",ja:"影島区",zh:"影岛区"},
 "부산진구":{ko:"부산진구",en:"Busanjin-gu",ja:"釜山鎮区",zh:"釜山镇区"},"동래구":{ko:"동래구",en:"Dongnae-gu",ja:"東莱区",zh:"东莱区"},
 "남구":{ko:"남구",en:"Nam-gu",ja:"南区",zh:"南区"},"북구":{ko:"북구",en:"Buk-gu",ja:"北区",zh:"北区"},
 "해운대구":{ko:"해운대구",en:"Haeundae-gu",ja:"海雲台区",zh:"海云台区"},"사하구":{ko:"사하구",en:"Saha-gu",ja:"沙下区",zh:"沙下区"},
 "금정구":{ko:"금정구",en:"Geumjeong-gu",ja:"金井区",zh:"金井区"},"강서구":{ko:"강서구",en:"Gangseo-gu",ja:"江西区",zh:"江西区"},
 "연제구":{ko:"연제구",en:"Yeonje-gu",ja:"蓮堤区",zh:"莲堤区"},"수영구":{ko:"수영구",en:"Suyeong-gu",ja:"水営区",zh:"水营区"},
 "사상구":{ko:"사상구",en:"Sasang-gu",ja:"沙上区",zh:"沙上区"},"기장군":{ko:"기장군",en:"Gijang-gun",ja:"機張郡",zh:"机张郡"}};

const UI={
 ko:{brand:"부산의 맛",sub:n=>`부산광역시 맛집 ${n}곳 · 구·군과 음식 종류로 찾아보세요`,
   src:`제공: <b>부산의 맛</b> (부산광역시, 2026) · 데이터 출처: <a href="https://www.visitbusan.net/index.do?menuCd=DOM_000000201002000000" target="_blank" rel="noopener">부산관광포털 비짓부산</a>`,
   search:"가게·메뉴·지역 검색",list:"목록",map:"지도",catLabel:"종류",guLabel:"지역",all:"전체",
   count:n=>`<b>${n}</b>곳`,call:"전화",mapBtn:"길찾기",detail:"상세",
   sorts:{def:"기본순",view:"조회순",like:"좋아요순",name:"가나다순"},
   empty:"조건에 맞는 맛집이 없어요.<br>검색어나 필터를 바꿔보세요.",
   hint:"핀을 누르면 가게 정보가 나와요",
   foot:`데이터는 부산관광포털(비짓부산) 공개 정보를 정리한 것으로 실제와 다를 수 있습니다. 방문 전 영업시간·휴무 확인을 권합니다.<br>음식 종류는 메뉴·소개 기반 자동 분류 · 지도 © OpenStreetMap·CARTO · 갱신 __UPDATED__`},
 en:{brand:"Taste of Busan",sub:n=>`${n} restaurants in Busan · Filter by district & cuisine`,
   src:`Source: <b>Taste of Busan</b> (Busan Metropolitan City, 2026) · Data: <a href="https://www.visitbusan.net/index.do?menuCd=DOM_000000201002000000" target="_blank" rel="noopener">VisitBusan portal</a>`,
   search:"Search name · menu · area",list:"List",map:"Map",catLabel:"Cuisine",guLabel:"Area",all:"All",
   count:n=>`<b>${n}</b> places`,call:"Call",mapBtn:"Directions",detail:"Details",
   sorts:{def:"Default",view:"Most viewed",like:"Most liked",name:"Name A–Z"},
   empty:"No places match your filters.<br>Try a different keyword or filter.",
   hint:"Tap a pin to see the place",
   foot:`Compiled from VisitBusan public data; details may differ. Please check hours/closing days before visiting.<br>Cuisine type is auto-classified · Map © OpenStreetMap, CARTO · Updated __UPDATED__`},
 ja:{brand:"釜山の味",sub:n=>`釜山広域市のグルメ ${n}軒 · 区・郡と料理ジャンルで検索`,
   src:`提供: <b>釜山の味</b> (釜山広域市, 2026) · データ出典: <a href="https://www.visitbusan.net/index.do?menuCd=DOM_000000201002000000" target="_blank" rel="noopener">VisitBusan 公式観光ポータル</a>`,
   search:"店名・メニュー・エリア検索",list:"リスト",map:"地図",catLabel:"ジャンル",guLabel:"エリア",all:"すべて",
   count:n=>`<b>${n}</b>軒`,call:"電話",mapBtn:"道案内",detail:"詳細",
   sorts:{def:"標準",view:"閲覧数順",like:"いいね順",name:"名前順"},
   empty:"条件に合う店がありません。<br>キーワードやフィルターを変更してください。",
   hint:"ピンをタップすると店舗情報が表示されます",
   foot:`VisitBusanの公開データを整理したもので、実際と異なる場合があります。訪問前に営業時間・定休日をご確認ください。<br>料理ジャンルは自動分類 · 地図 © OpenStreetMap・CARTO · 更新 __UPDATED__`},
 zh:{brand:"釜山的味道",sub:n=>`釜山广域市美食 ${n}家 · 按区·郡和菜系筛选`,
   src:`提供: <b>釜山的味道</b> (釜山广域市, 2026) · 数据来源: <a href="https://www.visitbusan.net/index.do?menuCd=DOM_000000201002000000" target="_blank" rel="noopener">VisitBusan 官方旅游门户</a>`,
   search:"搜索店名·菜单·地区",list:"列表",map:"地图",catLabel:"菜系",guLabel:"地区",all:"全部",
   count:n=>`<b>${n}</b>家`,call:"电话",mapBtn:"导航",detail:"详情",
   sorts:{def:"默认",view:"浏览最多",like:"点赞最多",name:"名称"},
   empty:"没有符合条件的餐厅。<br>请更换关键词或筛选条件。",
   hint:"点击图钉查看店铺信息",
   foot:`内容整理自VisitBusan公开数据，可能与实际不符，到店前请确认营业时间·休息日。中文模式下店铺详情以英文显示。<br>菜系为自动分类 · 地图 © OpenStreetMap·CARTO · 更新 __UPDATED__`}};

const state={q:"",cat:"전체",gu:"전체",sort:"def",view:"list",
  lang:(()=>{const s=localStorage.getItem("bf_lang");if(s)return s;const n=(navigator.language||"ko").slice(0,2);return ["en","ja","zh"].includes(n)?n:"ko"})()};

// 다국어 텍스트 선택: zh는 en으로 폴백, en/ja 없으면 ko
function tr(o){if(!o)return "";const L=state.lang;if(L==="zh")return o.en||o.ko||"";return o[L]||o.en||o.ko||""}
function catName(k){return (CAT_I18N[k]||{})[state.lang]||k}
function guName(k){return (GU_I18N[k]||{})[state.lang]||k}
function U(){return UI[state.lang]}

const PIN='<svg class="ic" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 21s-7-6.3-7-11a7 7 0 0114 0c0 4.7-7 11-7 11z"/><circle cx="12" cy="10" r="2.4"/></svg>';
const CLK='<svg class="ic" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>';
const FORK='<svg class="ic" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 3v7a2 2 0 002 2 2 2 0 002-2V3M7 12v9M17 3c-1.5 0-2.5 2-2.5 5s1 4 2.5 4v9"/></svg>';
const esc=s=>(s||"").replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const norm=s=>(s||"").toLowerCase().replace(/\s+/g,"");

function tally(key){const m=new Map();DATA.forEach(r=>m.set(r[key],(m.get(r[key])||0)+1));return [...m.entries()].sort((a,b)=>b[1]-a[1])}

function buildChips(elId,key,stateKey,nameFn){
  const el=document.getElementById(elId);
  const label=key==="c"?U().catLabel:U().guLabel;
  let h=`<span class="chiplabel">${label}</span><button class="chip${state[stateKey]==="전체"?" on":""}" data-v="전체">${U().all}<i class="ct">${DATA.length}</i></button>`;
  tally(key).forEach(([v,n])=>h+=`<button class="chip${state[stateKey]===v?" on":""}" data-v="${esc(v)}">${esc(nameFn(v))}<i class="ct">${n}</i></button>`);
  el.innerHTML=h;
  el.onclick=e=>{const b=e.target.closest(".chip");if(!b)return;state[stateKey]=b.dataset.v;[...el.children].forEach(c=>c.classList&&c.classList.toggle("on",c===b));render()};
}

function filtered(){
  const q=norm(state.q);
  let list=DATA.filter(r=>{
    if(state.cat!=="전체"&&r.c!==state.cat)return false;
    if(state.gu!=="전체"&&r.g!==state.gu)return false;
    if(q){const hay=norm(tr(r.n)+tr(r.m)+tr(r.a)+r.g+r.c+(r.n.ko||"")+(r.n.en||""));if(!hay.includes(q))return false}
    return true;
  });
  const s=state.sort;
  if(s==="view")list=[...list].sort((a,b)=>b.v-a.v);
  else if(s==="like")list=[...list].sort((a,b)=>b.l-a.l);
  else if(s==="name")list=[...list].sort((a,b)=>tr(a.n).localeCompare(tr(b.n),state.lang==="zh"?"zh":state.lang));
  return list;
}

function card(r){
  const col=CAT_COLORS[r.c]||"#7a8896";
  const menu=tr(r.m).split("\n").filter(Boolean).join(" · ");
  const cls=esc((tr(r.x)||"").trim()), hrs=esc(tr(r.h));
  const closedTxt=cls&&!/^(연중무휴|연중 무휴|Open (365|every))/i.test(cls)?" · "+cls:"";
  const tel=(r.p||"").replace(/[^0-9+]/g,"");
  const mapq=encodeURIComponent(tr(r.n)+" "+r.g);
  const img=r.t?`<img loading="lazy" src="${esc(r.t)}" alt="${esc(tr(r.n))}" onerror="this.style.display='none';this.nextElementSibling.style.display='flex'"><div class="ph" style="display:none">🍽️</div>`:`<div class="ph">🍽️</div>`;
  return `<article class="card"><div class="thumb">${img}<span class="badge" style="background:${col}">${esc(catName(r.c))}</span><span class="gbadge">${esc(guName(r.g))}</span></div>
  <div class="body"><a class="name" href="${esc(r.u)}" target="_blank" rel="noopener">${esc(tr(r.n))}</a>
  ${menu?`<div class="menu">${FORK}<span>${esc(menu)}</span></div>`:""}
  <div class="row">${PIN}<span>${esc(tr(r.a))}</span></div>
  ${hrs?`<div class="row">${CLK}<span>${hrs}${closedTxt}</span></div>`:""}
  ${tr(r.d)?`<div class="desc">${esc(tr(r.d))}</div>`:""}
  <div class="stat">👁 ${r.v.toLocaleString()} &nbsp; ♥ ${r.l}</div>
  <div class="acts">${tel?`<a class="act call" href="tel:${tel}"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 16.9v3a2 2 0 01-2.2 2 19.8 19.8 0 01-8.6-3 19.5 19.5 0 01-6-6 19.8 19.8 0 01-3-8.6A2 2 0 014.1 2h3a2 2 0 012 1.7c.1.9.3 1.8.6 2.6a2 2 0 01-.5 2.1L8 9.6a16 16 0 006 6l1.2-1.2a2 2 0 012.1-.5c.8.3 1.7.5 2.6.6a2 2 0 011.7 2z"/></svg>${U().call}</a>`:""}
  <a class="act" href="https://map.kakao.com/?q=${mapq}" target="_blank" rel="noopener">${PIN.replace('class="ic" ','')}${U().mapBtn}</a>
  <a class="act" href="${esc(r.u)}" target="_blank" rel="noopener">${U().detail}</a></div></div></article>`;
}

/* ── 지도 ── */
let map,cluster,mapReady=false;
function initMap(){
  if(mapReady)return;
  map=L.map("map",{zoomControl:true,attributionControl:true}).setView([35.16,129.07],11);
  L.tileLayer("https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",{
    attribution:'© <a href="https://openstreetmap.org/copyright">OpenStreetMap</a> · © <a href="https://carto.com/">CARTO</a>',
    subdomains:"abcd",maxZoom:19}).addTo(map);
  cluster=L.markerClusterGroup({maxClusterRadius:48,spiderfyOnMaxZoom:true,showCoverageOnHover:false});
  map.addLayer(cluster);
  mapReady=true;
}
function popHtml(r){
  const tel=(r.p||"").replace(/[^0-9+]/g,"");
  const menu=tr(r.m).split("\n").filter(Boolean).join(" · ");
  const mapq=encodeURIComponent(tr(r.n)+" "+r.g);
  return `<div class="pop">${r.t?`<img class="pimg" src="${esc(r.t)}" alt="" onerror="this.style.display='none'">`:""}
  <div class="pbody"><div class="pn">${esc(tr(r.n))}</div>
  ${menu?`<div class="pm">${esc(menu)}</div>`:""}
  <div class="pa">${esc(catName(r.c))} · ${esc(guName(r.g))}<br>${esc(tr(r.a))}</div>
  <div class="pacts">${tel?`<a class="call" href="tel:${tel}">${U().call}</a>`:""}<a href="https://map.kakao.com/?q=${mapq}" target="_blank" rel="noopener">${U().mapBtn}</a><a href="${esc(r.u)}" target="_blank" rel="noopener">${U().detail}</a></div></div></div>`;
}
function renderMap(list){
  initMap();cluster.clearLayers();
  const ms=[];
  list.forEach(r=>{
    if(r.lat==null||r.lng==null)return;
    const col=CAT_COLORS[r.c]||"#7a8896";
    const m=L.marker([r.lat,r.lng],{icon:L.divIcon({className:"",html:`<div class="mk" style="background:${col}"></div>`,iconSize:[16,16],iconAnchor:[8,15],popupAnchor:[0,-14]})});
    m.bindPopup(popHtml(r),{closeButton:true});
    ms.push(m);
  });
  cluster.addLayers(ms);
  setTimeout(()=>map.invalidateSize(),60);
  if(list.length){try{cluster.getBounds().isValid()&&map.fitBounds(cluster.getBounds().pad(.12),{maxZoom:14})}catch(e){}}
}

function render(){
  const list=filtered();
  document.getElementById("count").innerHTML=U().count(list.length);
  if(state.view==="map"){renderMap(list);}
  else{
    const g=document.getElementById("grid");
    g.innerHTML=list.length?list.map(card).join(""):`<div class="empty"><div class="em">🔍</div><p>${U().empty}</p></div>`;
  }
}

/* ── 언어/뷰 적용 ── */
function setToolsH(){document.documentElement.style.setProperty("--toolsH",(document.querySelector(".tools").offsetHeight+document.querySelector(".hero").offsetHeight)+"px")}
function applyLang(){
  const u=U();document.documentElement.lang=state.lang;
  document.getElementById("brand").textContent=u.brand;
  document.getElementById("subtitle").textContent=u.sub(DATA.length);
  document.getElementById("src").innerHTML=u.src;
  document.getElementById("q").placeholder=u.search;
  document.querySelector(".vlist").textContent=u.list;
  document.querySelector(".vmap").textContent=u.map;
  document.getElementById("footer").innerHTML=u.foot;
  document.getElementById("maphint").innerHTML=u.hint;
  const sel=document.getElementById("sort");sel.innerHTML=Object.entries(u.sorts).map(([k,v])=>`<option value="${k}"${state.sort===k?" selected":""}>${v}</option>`).join("");
  document.querySelectorAll("#langs button").forEach(b=>b.classList.toggle("on",b.dataset.l===state.lang));
  buildChips("cats","c","cat",catName);
  buildChips("gus","g","gu",guName);
  render();setToolsH();
}

function setView(v){
  state.view=v;
  document.querySelectorAll("#viewtog button").forEach(b=>b.classList.toggle("on",b.dataset.v===v));
  document.getElementById("grid").classList.toggle("hidden",v==="map");
  document.getElementById("map").classList.toggle("show",v==="map");
  document.getElementById("top").classList.toggle("show",false);
  render();
  if(v==="map"){const h=document.getElementById("maphint");h.classList.add("show");setTimeout(()=>h.classList.remove("show"),2600)}
}

// 이벤트
let t;document.getElementById("q").addEventListener("input",e=>{clearTimeout(t);state.q=e.target.value;t=setTimeout(render,120)});
document.getElementById("sort").addEventListener("change",e=>{state.sort=e.target.value;render()});
document.getElementById("viewtog").addEventListener("click",e=>{const b=e.target.closest("button");if(b)setView(b.dataset.v)});
document.getElementById("langs").addEventListener("click",e=>{const b=e.target.closest("button");if(!b)return;state.lang=b.dataset.l;localStorage.setItem("bf_lang",state.lang);applyLang()});
const topBtn=document.getElementById("top");
addEventListener("scroll",()=>topBtn.classList.toggle("show",state.view==="list"&&scrollY>600),{passive:true});
topBtn.addEventListener("click",()=>scrollTo({top:0,behavior:"smooth"}));
addEventListener("resize",setToolsH);

applyLang();
</script>
</body>
</html>"""

out = (HTML.replace("__DATA__", data_js)
           .replace("__COUNT__", str(len(slim)))
           .replace("__UPDATED__", updated))
with open("index.html", "w", encoding="utf-8") as f:
    f.write(out)
print(f"index.html 생성 ({len(out):,} bytes, {len(slim)}곳)")
