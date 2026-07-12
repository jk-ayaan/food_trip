#!/usr/bin/env python3
"""data/<region>/<section>.json → index.html + pack/<region>.json : '그곳에 가면' 전국 가이드.
지역(부산 + 전국 시·도 + 수도권 상세) × 섹션탭(명소·음식·우슐랭·축제·숙박·쇼핑).
데이터는 지역별 pack JSON으로 분리(lazy-load) — 선택한 지역만 내려받음.
지도(Leaflet/OSM) + 다국어(한·영·일·중) + 계정 저장(찜·가본 곳)."""
import json, datetime, os

REGIONS = ["busan", "seoul", "incheon", "gyeonggi", "suwon", "ansan", "pangyo",
           "jeongja", "seohyeon", "gangwon", "daejeon", "sejong", "chungbuk",
           "chungnam", "daegu", "gyeongbuk", "ulsan", "gyeongnam", "gwangju",
           "jeonbuk", "jeonnam", "jeju"]
SECTIONS = ["sights", "food", "usulleng", "festival", "stay", "shopping"]


def mlf(i18n, field):
    o = {}
    for lang in ("ko", "en", "ja"):
        v = (i18n.get(lang) or {}).get(field, "")
        if v:
            o[lang] = v
    return o or None


def slim_row(r):
    i = r.get("i18n", {})
    thumb = r.get("thumb", "")
    if thumb.startswith("http://"):  # https 페이지 mixed-content 차단 방지 (visitkorea CDN은 https 지원)
        thumb = "https://" + thumb[7:]
    out = {"c": r.get("category", "기타"), "g": r.get("district", ""),
           "t": thumb, "lat": r.get("lat"), "lng": r.get("lng"),
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
    if r.get("office"):
        out["of"] = r["office"]
    if r.get("editions"):
        out["ed"] = r["editions"]
    if r.get("rating"):
        out["rt"] = r["rating"]
        out["rc"] = r.get("rcount", 0)
    return out


os.makedirs("pack", exist_ok=True)
counts = {}
for reg in REGIONS:
    rd = {}
    for s in SECTIONS:
        path = f"data/{reg}/{s}.json"
        rows = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else []
        rd[s] = [slim_row(r) for r in rows if (r.get("i18n", {}).get("ko", {}).get("name") or r.get("name_ko"))]
    if any(rd.values()):  # 데이터 있는 지역만 pack 생성
        packed = {k: v for k, v in rd.items() if v}
        with open(f"pack/{reg}.json", "w", encoding="utf-8") as f:
            json.dump(packed, f, ensure_ascii=False, separators=(",", ":"))
        counts[reg] = {k: len(v) for k, v in packed.items()}

meta_js = json.dumps(counts, ensure_ascii=False, separators=(",", ":"))
total = sum(sum(c.values()) for c in counts.values())
updated = datetime.date.today().isoformat()
for reg, c in counts.items():
    print(f"{reg}: {c} 소계 {sum(c.values())}")
print("총", total, f"· pack {len(counts)}개 지역")

HTML = r"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#0a6ebd">
<meta name="description" content="그곳에 가면 — 전국 시·도 명소·음식·축제·숙박·쇼핑 __TOTAL__곳. 카카오 별점·지도·다국어 여행 가이드.">
<title>그곳에 가면 · Food Trip Korea</title>
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
.regs{display:flex;gap:6px;overflow-x:auto;margin-top:12px;padding:0 2px;scrollbar-width:none}
.regs::-webkit-scrollbar{display:none}
.regs[hidden]{display:none}
.reg{flex:none;border:1.5px solid rgba(255,255,255,.32);background:rgba(255,255,255,.1);color:#fff;border-radius:999px;padding:7px 13px;font-size:12.5px;font-weight:700;cursor:pointer;display:flex;align-items:center;gap:5px;opacity:.85;white-space:nowrap}
.reg.on{background:#fff;color:var(--sea);opacity:1;border-color:#fff}
.reg .rn{font-size:10.5px;opacity:.6;font-weight:800}
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
.thumb .ph{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font-size:42px;color:#aeb9c5}
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
.stat{font-size:11.5px;color:#9aa6b2;font-weight:600;display:flex;gap:11px;align-items:center}
.rate{color:#e8930c;font-weight:800;font-size:12px}
.rate i{font-style:normal;color:#9aa6b2;font-weight:600;font-size:11px;margin-left:2px}
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
.savebar{position:absolute;bottom:8px;right:8px;display:flex;gap:6px;align-items:center;z-index:5}
.sbtn{width:32px;height:32px;border-radius:50%;border:0;background:rgba(255,255,255,.94);color:#8b98a5;display:flex;align-items:center;justify-content:center;cursor:pointer;box-shadow:0 2px 8px rgba(0,0,0,.22);padding:0;transition:.12s}
.sbtn svg{width:16px;height:16px}
.sbtn:active{transform:scale(.88)}
.sbtn.v.on{background:#2e9e5b;color:#fff}
.sbtn.w.on{background:#d6457f;color:#fff}
.prio{height:24px;padding:0 9px;border-radius:999px;border:0;font-size:11px;font-weight:800;color:#fff;cursor:pointer;box-shadow:0 2px 8px rgba(0,0,0,.22)}
.prio:active{transform:scale(.92)}
.pop .pacts a.sv{flex:none;width:30px;font-size:13px;font-weight:800;cursor:pointer}
.pop .pacts a.sv.v.on{background:#2e9e5b;border-color:#2e9e5b;color:#fff}
.pop .pacts a.sv.w.on{background:#d6457f;border-color:#d6457f;color:#fff}
.mlbtn{display:flex;align-items:center;gap:5px;border:0;background:rgba(255,255,255,.16);color:#fff;border-radius:999px;padding:7px 11px;cursor:pointer;font-weight:800;font-size:12px}
.mlbtn b{background:#fff;color:var(--sea);border-radius:999px;padding:1px 7px;font-size:11px;font-variant-numeric:tabular-nums}
.mlay{position:fixed;inset:0;background:rgba(10,20,32,.48);z-index:2500;display:none;align-items:flex-end;justify-content:center}
.mlay.show{display:flex}
.mpanel{background:#fff;width:100%;max-width:480px;max-height:82vh;border-radius:22px 22px 0 0;display:flex;flex-direction:column;overflow:hidden;box-shadow:0 -10px 40px rgba(0,0,0,.25)}
@media(min-width:560px){.mlay{align-items:center;padding:20px}.mpanel{border-radius:22px}}
.mhead{display:flex;align-items:center;justify-content:space-between;padding:16px 18px 10px}
.mhead b{font-size:17px;letter-spacing:-.02em}
.mclose{border:0;background:var(--bg);color:var(--sub);width:34px;height:34px;border-radius:50%;display:flex;align-items:center;justify-content:center;cursor:pointer}
.mtabs{display:flex;gap:8px;padding:0 16px 12px}
.mtab{flex:1;border:1.5px solid var(--line);background:#fff;color:var(--sub);border-radius:12px;padding:9px 6px;font-size:13px;font-weight:700;cursor:pointer}
.mtab.on{background:var(--ink);border-color:var(--ink);color:#fff}
.mlist{overflow:auto;padding:2px 12px calc(18px + var(--safe-b))}
.mitem{display:flex;align-items:center;gap:10px;padding:11px 6px;border-bottom:1px solid var(--line);cursor:pointer}
.mitem:last-child{border-bottom:0}
.mitem .mi{font-size:20px;flex:none}
.mitem .mtx{flex:1;min-width:0}
.mitem .mn{font-weight:800;font-size:14.5px;letter-spacing:-.01em;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.mitem .ms{font-size:12px;color:var(--sub);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.mitem .prio{flex:none}
.mitem .sbtn{flex:none;box-shadow:none;border:1.5px solid var(--line);width:30px;height:30px}
.mitem .sbtn svg{width:14px;height:14px}
.mitem.gone{opacity:.5;cursor:default}
.mempty{text-align:center;color:var(--sub);padding:44px 20px;font-weight:600;font-size:13.5px;line-height:1.7}
.mlbtn img{width:20px;height:20px;border-radius:50%;display:block}
.llbody{padding:0 18px calc(22px + var(--safe-b));display:flex;flex-direction:column;gap:9px}
.lldesc{font-size:13.5px;color:var(--sub);line-height:1.7;padding:0 2px 10px;text-align:center}
.lbtn{display:flex;align-items:center;justify-content:center;gap:9px;border:1.5px solid var(--line);background:#fff;border-radius:13px;padding:12px;font-size:14.5px;font-weight:700;cursor:pointer;color:var(--ink)}
.lbtn:active{filter:brightness(.96)}
.lbtn.a{background:#000;color:#fff;border-color:#000}
.lbtn.out{color:#d2453b;border-color:#f0cdc9}
.lbtn svg,.lbtn img{width:18px;height:18px}
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
.visits{display:flex;align-items:center;justify-content:center;gap:11px;width:fit-content;max-width:90%;margin:20px auto 2px;padding:10px 18px;background:linear-gradient(135deg,#fff,#f4f8fc);border:1px solid var(--line);border-radius:999px;box-shadow:var(--shadow);font-size:12.5px;color:var(--sub);font-weight:600}
.visits[hidden]{display:none}
.visits .vi{display:inline-flex;align-items:center;gap:5px}
.visits svg{width:15px;height:15px;color:var(--sea);flex:none}
.visits b{color:var(--sea);font-weight:800;font-variant-numeric:tabular-nums;font-size:13.5px}
.visits .vdot{width:3px;height:3px;border-radius:50%;background:#c4ccd6}
</style>
</head>
<body>
<header class="hero"><div class="wrap">
  <div class="topline">
    <div><h1>📍 <span id="brand">부산에 가면</span></h1><p id="subtitle"></p></div>
    <div style="display:flex;gap:7px;align-items:flex-start;flex:none">
      <button class="mlbtn" id="mlBtn" aria-label="내 목록"><svg viewBox="0 0 24 24" fill="currentColor" width="15" height="15"><path d="M12 21s-7.5-4.9-9.8-9.2C.7 8.9 2.2 5.4 5.4 4.6c1.9-.5 3.9.2 5.1 1.7L12 8l1.5-1.7c1.2-1.5 3.2-2.2 5.1-1.7 3.2.8 4.7 4.3 3.2 7.2C19.5 16.1 12 21 12 21z"/></svg><b id="mlCount" hidden></b></button>
      <button class="mlbtn" id="authBtn"><img id="authAv" alt="" hidden><span id="authLabel">로그인</span></button>
      <div class="langs" id="langs"><button data-l="ko" class="on">한</button><button data-l="en">EN</button><button data-l="ja">日</button><button data-l="zh">中</button></div>
    </div>
  </div>
  <div class="regs" id="regs" hidden></div>
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
<div class="visits" id="visits" hidden>
  <span class="vi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75"/></svg><span id="vLabelTotal">누적 방문</span> <b id="vTotal">–</b></span>
  <span class="vdot"></span>
  <span class="vi"><span id="vLabelToday">오늘</span> <b id="vToday">–</b></span>
</div>
<footer id="footer"></footer>
<div class="mlay" id="mlay">
  <div class="mpanel">
    <div class="mhead"><b id="mlTitle">💾 내 저장</b><button class="mclose" id="mlClose" aria-label="닫기"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" width="18" height="18"><path d="M6 6l12 12M18 6L6 18"/></svg></button></div>
    <div class="mtabs"><button class="mtab on" id="mlTabW" data-t="w"></button><button class="mtab" id="mlTabV" data-t="v"></button></div>
    <div class="mlist" id="mlist"></div>
  </div>
</div>
<div class="mlay" id="llay">
  <div class="mpanel">
    <div class="mhead"><b id="llTitle"></b><button class="mclose" id="llClose" aria-label="닫기"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" width="18" height="18"><path d="M6 6l12 12M18 6L6 18"/></svg></button></div>
    <div class="llbody" id="llBody"></div>
  </div>
</div>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script>
<script src="https://www.gstatic.com/firebasejs/10.14.1/firebase-app-compat.js"></script>
<script src="https://www.gstatic.com/firebasejs/10.14.1/firebase-auth-compat.js"></script>
<script src="https://www.gstatic.com/firebasejs/10.14.1/firebase-firestore-compat.js"></script>
<script>
const REGMETA=__REGMETA__;
const DB={};
const TODAY="__TODAY__";
const SEC=[{k:"sights",i:"🏞️"},{k:"food",i:"🍜"},{k:"usulleng",i:"📮"},{k:"festival",i:"🎉"},{k:"stay",i:"🏨"},{k:"shopping",i:"🛍️"}];
const REGIONS=[
 {k:"busan",i:"🌊",n:{ko:"부산",en:"Busan",ja:"釜山",zh:"釜山"},c:[35.16,129.07],z:11},
 {k:"seoul",i:"🏙️",n:{ko:"서울",en:"Seoul",ja:"ソウル",zh:"首尔"},c:[37.55,126.99],z:11},
 {k:"incheon",i:"🛳️",n:{ko:"인천",en:"Incheon",ja:"仁川",zh:"仁川"},c:[37.45,126.7],z:11},
 {k:"gyeonggi",i:"🌇",n:{ko:"경기",en:"Gyeonggi",ja:"京畿",zh:"京畿"},c:[37.4,127.2],z:9},
 {k:"suwon",i:"🏯",n:{ko:"수원",en:"Suwon",ja:"水原",zh:"水原"},c:[37.28,127.01],z:12},
 {k:"ansan",i:"🌷",n:{ko:"안산",en:"Ansan",ja:"安山",zh:"安山"},c:[37.32,126.83],z:12},
 {k:"pangyo",i:"🚄",n:{ko:"판교역",en:"Pangyo Stn",ja:"板橋駅",zh:"板桥站"},c:[37.394761,127.111217],z:14},
 {k:"jeongja",i:"🚇",n:{ko:"정자역",en:"Jeongja Stn",ja:"亭子駅",zh:"亭子站"},c:[37.365994,127.108727],z:14},
 {k:"seohyeon",i:"🚉",n:{ko:"서현역",en:"Seohyeon Stn",ja:"書峴駅",zh:"书岘站"},c:[37.385166,127.123674],z:14},
 {k:"gangwon",i:"🏔️",n:{ko:"강원",en:"Gangwon",ja:"江原",zh:"江原"},c:[37.8,128.2],z:9},
 {k:"daejeon",i:"🔬",n:{ko:"대전",en:"Daejeon",ja:"大田",zh:"大田"},c:[36.35,127.38],z:12},
 {k:"sejong",i:"🏛️",n:{ko:"세종",en:"Sejong",ja:"世宗",zh:"世宗"},c:[36.48,127.29],z:12},
 {k:"chungbuk",i:"🌿",n:{ko:"충북",en:"Chungbuk",ja:"忠北",zh:"忠北"},c:[36.8,127.7],z:9},
 {k:"chungnam",i:"🌾",n:{ko:"충남",en:"Chungnam",ja:"忠南",zh:"忠南"},c:[36.5,126.8],z:9},
 {k:"daegu",i:"🌞",n:{ko:"대구",en:"Daegu",ja:"大邱",zh:"大邱"},c:[35.87,128.6],z:11},
 {k:"gyeongbuk",i:"🏯",n:{ko:"경북",en:"Gyeongbuk",ja:"慶北",zh:"庆北"},c:[36.3,128.7],z:9},
 {k:"ulsan",i:"🐋",n:{ko:"울산",en:"Ulsan",ja:"蔚山",zh:"蔚山"},c:[35.54,129.31],z:11},
 {k:"gyeongnam",i:"🦀",n:{ko:"경남",en:"Gyeongnam",ja:"慶南",zh:"庆南"},c:[35.3,128.3],z:9},
 {k:"gwangju",i:"🎨",n:{ko:"광주",en:"Gwangju",ja:"光州",zh:"光州"},c:[35.16,126.85],z:12},
 {k:"jeonbuk",i:"🍲",n:{ko:"전북",en:"Jeonbuk",ja:"全北",zh:"全北"},c:[35.7,127.1],z:9},
 {k:"jeonnam",i:"🌊",n:{ko:"전남",en:"Jeonnam",ja:"全南",zh:"全南"},c:[34.8,126.9],z:9},
 {k:"jeju",i:"🍊",n:{ko:"제주",en:"Jeju",ja:"済州",zh:"济州"},c:[33.38,126.55],z:10},
].filter(r=>REGMETA[r.k]);
// ── 지역 데이터 lazy-load: 선택한 지역의 pack만 내려받음 ──
const _loading={};
function ensureRegion(k){
  if(DB[k])return Promise.resolve();
  if(_loading[k])return _loading[k];
  return _loading[k]=fetch("pack/"+k+".json").then(r=>{if(!r.ok)throw new Error(r.status);return r.json()})
    .then(d=>{DB[k]=d;ALLIDX=null})
    .catch(e=>{delete _loading[k];throw e});
}
function showLoading(){document.getElementById("count").innerHTML="";
  document.getElementById("grid").innerHTML=`<div class="empty"><div class="em">⏳</div><p>${U().loading}</p></div>`}
function showLoadErr(){document.getElementById("grid").innerHTML=`<div class="empty"><div class="em">⚠️</div><p>${U().loadErr}</p></div>`}
function REG(){return REGIONS.find(r=>r.k===state.region)||REGIONS[0]}
function regName(r){return r.n[state.lang]||r.n.ko}
function brandText(){const r=REG();return {ko:`${r.n.ko}에 가면`,en:`When in ${r.n.en}`,ja:`${r.n.ja}に行ったら`,zh:`来${r.n.zh}`}[state.lang]}
const PALETTE=["#0e7c86","#d2453b","#e8632c","#3f51b5","#7e57c2","#2e9e5b","#b5762e","#d6457f","#7a8b27","#0a6ebd","#7a8896"];

const SECNAME={
 sights:{ko:"명소",en:"Sights",ja:"名所",zh:"景点"},food:{ko:"음식",en:"Food",ja:"グルメ",zh:"美食"},
 usulleng:{ko:"우슐랭",en:"Usulleng",ja:"郵便局グルメ",zh:"邮局美食"},
 festival:{ko:"축제",en:"Festivals",ja:"祭り",zh:"庆典"},stay:{ko:"숙박",en:"Stay",ja:"宿泊",zh:"住宿"},
 shopping:{ko:"쇼핑",en:"Shopping",ja:"買物",zh:"购物"}};
const GU_I18N={"중구":{en:"Jung-gu",ja:"中区",zh:"中区"},"서구":{en:"Seo-gu",ja:"西区",zh:"西区"},"동구":{en:"Dong-gu",ja:"東区",zh:"东区"},"영도구":{en:"Yeongdo-gu",ja:"影島区",zh:"影岛区"},"부산진구":{en:"Busanjin-gu",ja:"釜山鎮区",zh:"釜山镇区"},"동래구":{en:"Dongnae-gu",ja:"東莱区",zh:"东莱区"},"남구":{en:"Nam-gu",ja:"南区",zh:"南区"},"북구":{en:"Buk-gu",ja:"北区",zh:"北区"},"해운대구":{en:"Haeundae-gu",ja:"海雲台区",zh:"海云台区"},"사하구":{en:"Saha-gu",ja:"沙下区",zh:"沙下区"},"금정구":{en:"Geumjeong-gu",ja:"金井区",zh:"金井区"},"강서구":{en:"Gangseo-gu",ja:"江西区",zh:"江西区"},"연제구":{en:"Yeonje-gu",ja:"蓮堤区",zh:"莲堤区"},"수영구":{en:"Suyeong-gu",ja:"水営区",zh:"水营区"},"사상구":{en:"Sasang-gu",ja:"沙上区",zh:"沙上区"},"기장군":{en:"Gijang-gun",ja:"機張郡",zh:"机张郡"}};
const CAT_I18N={
 "카페·베이커리":{en:"Cafe & Bakery",ja:"カフェ",zh:"咖啡"},"일식":{en:"Japanese",ja:"和食",zh:"日料"},"해산물·회":{en:"Seafood",ja:"海鮮",zh:"海鲜"},"고기·구이":{en:"BBQ & Grill",ja:"焼肉",zh:"烤肉"},"중식":{en:"Chinese",ja:"中華",zh:"中餐"},"양식·세계요리":{en:"Western & World",ja:"洋食",zh:"西餐"},"분식·주점":{en:"Snacks & Pub",ja:"軽食・居酒屋",zh:"小吃"},"면·국물":{en:"Noodles & Soup",ja:"麺類",zh:"面食"},"한식·백반":{en:"Korean",ja:"韓定食",zh:"韩餐"},
 "바다·해변":{en:"Sea & Beach",ja:"海・ビーチ",zh:"海滨"},"전망·야경":{en:"Views & Night",ja:"展望・夜景",zh:"观景"},"역사·문화재":{en:"History",ja:"歴史",zh:"历史"},"박물관·전시":{en:"Museums",ja:"博物館",zh:"博物馆"},"테마·체험":{en:"Themes",ja:"テーマ",zh:"主题"},"공원·자연":{en:"Parks & Nature",ja:"公園・自然",zh:"公园"},"거리·시장":{en:"Streets",ja:"街・市場",zh:"街市"},
 "백화점·몰":{en:"Malls",ja:"百貨店・モール",zh:"商场"},"전통시장":{en:"Markets",ja:"伝統市場",zh:"传统市场"},"면세점":{en:"Duty Free",ja:"免税店",zh:"免税店"},"거리·테마":{en:"Shopping Streets",ja:"商店街",zh:"商业街"},
 "호텔":{en:"Hotel",ja:"ホテル",zh:"酒店"},"리조트·콘도":{en:"Resort & Condo",ja:"リゾート",zh:"度假村"},"게스트하우스":{en:"Guesthouse",ja:"ゲストハウス",zh:"青年旅舍"},"모텔":{en:"Motel",ja:"モーテル",zh:"汽车旅馆"},"펜션·민박":{en:"Pension",ja:"ペンション",zh:"民宿"},
 "축제·행사":{en:"Festival & Event",ja:"祭り・イベント",zh:"庆典活动"},"기타":{en:"Others",ja:"その他",zh:"其他"},
 "국밥·탕":{en:"Gukbap & Soup",ja:"クッパ・スープ",zh:"汤饭"},"면류":{en:"Noodles",ja:"麺類",zh:"面食"},"카페·디저트":{en:"Cafe & Dessert",ja:"カフェ・デザート",zh:"咖啡甜点"},"회·해산물":{en:"Seafood & Hoe",ja:"刺身・海鮮",zh:"生鱼海鲜"},"일식·돈카츠":{en:"Japanese",ja:"和食・トンカツ",zh:"日料"},"양식·파스타":{en:"Western & Pasta",ja:"洋食・パスタ",zh:"西餐"},"분식":{en:"Snacks",ja:"粉食",zh:"小吃"},"치킨·호프":{en:"Chicken & Pub",ja:"チキン・ビール",zh:"炸鸡啤酒"}};
const UI={
 ko:{brand:"부산에 가면",sub:(s,n)=>`${SECNAME[s].ko} ${n}곳 · 구·군과 종류로 찾아보세요`,src:`데이터 출처: <a href="https://www.visitbusan.net/index.do?menuCd=DOM_000000201001000000" target="_blank" rel="noopener">부산관광포털 비짓부산</a> · '부산에가면'`,search:"이름·지역·키워드 검색",list:"목록",map:"지도",catLabel:"종류",guLabel:"지역",all:"전체",count:n=>`<b>${n}</b>곳`,call:"전화",mapBtn:"길찾기",detail:"상세",home:"홈페이지",sorts:{def:"기본순",rate:"평점순",view:"인기순",like:"좋아요순",name:"가나다순"},empty:"조건에 맞는 곳이 없어요.<br>검색어·필터·섹션을 바꿔보세요.",loading:"불러오는 중…",loadErr:"데이터를 불러오지 못했어요. 네트워크 확인 후 새로고침해 주세요.",hint:"핀을 누르면 정보가 나와요",ongoing:"진행중",upcoming:"예정",ended:"종료",foot:`비짓부산 공개 정보를 정리한 것으로 실제와 다를 수 있습니다. 방문 전 운영시간·휴무·행사기간을 확인하세요.<br>종류는 자동 분류 · 숙박·中文은 일부 정보가 한/영으로 표기 · 지도 © OpenStreetMap·CARTO · 갱신 __UPDATED__`},
 en:{brand:"When in Busan",sub:(s,n)=>`${n} ${SECNAME[s].en.toLowerCase()} spots · Filter by district & type`,src:`Data: <a href="https://www.visitbusan.net/index.do?menuCd=DOM_000000201001000000" target="_blank" rel="noopener">VisitBusan portal</a>`,search:"Search name · area · keyword",list:"List",map:"Map",catLabel:"Type",guLabel:"Area",all:"All",count:n=>`<b>${n}</b> places`,call:"Call",mapBtn:"Directions",detail:"Details",home:"Website",sorts:{def:"Default",rate:"Top rated",view:"Popular",like:"Most liked",name:"Name A–Z"},empty:"Nothing matches.<br>Try another keyword, filter or section.",loading:"Loading…",loadErr:"Failed to load data. Check your network and refresh.",hint:"Tap a pin for details",ongoing:"Ongoing",upcoming:"Upcoming",ended:"Ended",foot:`Compiled from VisitBusan public data; details may differ. Check hours/closing/festival dates before visiting.<br>Type is auto-classified · Some stay info shown in Korean · Map © OpenStreetMap, CARTO · Updated __UPDATED__`},
 ja:{brand:"釜山に行ったら",sub:(s,n)=>`${SECNAME[s].ja} ${n}件 · 区・郡と種類で検索`,src:`データ出典: <a href="https://www.visitbusan.net/index.do?menuCd=DOM_000000201001000000" target="_blank" rel="noopener">VisitBusan 公式観光ポータル</a>`,search:"名前・エリア・キーワード",list:"リスト",map:"地図",catLabel:"種類",guLabel:"エリア",all:"すべて",count:n=>`<b>${n}</b>件`,call:"電話",mapBtn:"道案内",detail:"詳細",home:"ホームページ",sorts:{def:"標準",rate:"評価順",view:"人気順",like:"いいね順",name:"名前順"},empty:"該当なし。<br>キーワード・フィルター・セクションを変更してください。",loading:"読み込み中…",loadErr:"データを読み込めませんでした。再読み込みしてください。",hint:"ピンをタップで情報表示",ongoing:"開催中",upcoming:"予定",ended:"終了",foot:`VisitBusanの公開データを整理。実際と異なる場合があります。訪問前に営業時間・定休日・開催期間をご確認ください。<br>種類は自動分類 · 宿泊・中文は一部が韓/英表記 · 地図 © OpenStreetMap・CARTO · 更新 __UPDATED__`},
 zh:{brand:"来釜山",sub:(s,n)=>`${SECNAME[s].zh} ${n}处 · 按区·郡和类型筛选`,src:`数据来源: <a href="https://www.visitbusan.net/index.do?menuCd=DOM_000000201001000000" target="_blank" rel="noopener">VisitBusan 官方旅游门户</a>`,search:"搜索名称·地区·关键词",list:"列表",map:"地图",catLabel:"类型",guLabel:"地区",all:"全部",count:n=>`<b>${n}</b>处`,call:"电话",mapBtn:"导航",detail:"详情",home:"官网",sorts:{def:"默认",rate:"评分",view:"人气",like:"点赞",name:"名称"},empty:"没有符合条件的结果。<br>请更换关键词·筛选或栏目。",loading:"加载中…",loadErr:"数据加载失败，请刷新。",hint:"点击图钉查看信息",ongoing:"进行中",upcoming:"即将",ended:"已结束",foot:`整理自VisitBusan公开数据，可能与实际不符，到访前请确认营业·休息·活动期间。<br>类型为自动分类 · 部分详情以韩/英显示 · 地图 © OpenStreetMap·CARTO · 更新 __UPDATED__`}};

const LOCT={
 ko:{me:"내 위치",nearest:"거리순",within:"이내",all:"전체",nearme:"내 위치 기준",sortLabel:"정렬",err:"위치 정보를 가져올 수 없어요. 브라우저 위치 권한을 확인해 주세요.",locating:"현재 위치 확인 중…",here:"현재 위치"},
 en:{me:"My location",nearest:"Nearest",within:"away",all:"All",nearme:"Near me",sortLabel:"Sort",err:"Couldn't get your location. Please allow location access.",locating:"Locating…",here:"You are here"},
 ja:{me:"現在地",nearest:"近い順",within:"以内",all:"すべて",nearme:"現在地から",sortLabel:"並び替え",err:"位置情報を取得できません。位置情報の許可をご確認ください。",locating:"現在地を取得中…",here:"現在地"},
 zh:{me:"我的位置",nearest:"距离最近",within:"以内",all:"全部",nearme:"我的位置",sortLabel:"排序",err:"无法获取位置，请允许定位权限。",locating:"定位中…",here:"我的位置"}};
function LT(){return LOCT[state.lang]}
const VIS={ko:{total:"누적 방문",today:"오늘"},en:{total:"Total visits",today:"Today"},ja:{total:"累計訪問",today:"本日"},zh:{total:"累计访问",today:"今日"}};
const MYT={
 ko:{mine:"내 저장",all:"전체",vList:"가본 곳",wList:"찜한 곳",visited:"가봤어요",wish:"찜",prioSort:"우선순위순",p:["","높음","보통","낮음"],pick:"추천",empty:"아직 없어요 — 카드의 ♥ / ✓ 버튼으로 저장해 보세요"},
 en:{mine:"My places",all:"All",vList:"Visited",wList:"Saved",visited:"Visited",wish:"Save",prioSort:"By priority",p:["","High","Mid","Low"],pick:"pick",empty:"Nothing yet — save places with the ♥ / ✓ buttons on cards"},
 ja:{mine:"マイリスト",all:"すべて",vList:"行った所",wList:"キープ",visited:"行った",wish:"キープ",prioSort:"優先度順",p:["","高","中","低"],pick:"おすすめ",empty:"まだありません — カードの ♥ / ✓ ボタンで保存できます"},
 zh:{mine:"我的收藏",all:"全部",vList:"去过",wList:"收藏",visited:"去过",wish:"收藏",prioSort:"按优先级",p:["","高","中","低"],pick:"推荐",empty:"还没有 — 用卡片上的 ♥ / ✓ 按钮保存"}};
function MT(){return MYT[state.lang]}
const USRC={
 ko:` · 우슐랭: <a href="https://jk-ayaan.github.io/usulleng/" target="_blank" rel="noopener">우체국 추천 맛집가이드(부산지방우정청 2024·2025)</a> — 부산·울산·경남 포함`,
 en:` · Usulleng: <a href="https://jk-ayaan.github.io/usulleng/" target="_blank" rel="noopener">Post Office restaurant guide (Busan Regional Postal Agency, 2024·2025)</a> — incl. Ulsan & Gyeongnam`,
 ja:` · 郵便局グルメ: <a href="https://jk-ayaan.github.io/usulleng/" target="_blank" rel="noopener">郵便局おすすめグルメガイド(釜山地方郵政庁 2024·2025)</a> — 蔚山・慶南を含む`,
 zh:` · 邮局美食: <a href="https://jk-ayaan.github.io/usulleng/" target="_blank" rel="noopener">邮局推荐美食指南(釜山地方邮政厅 2024·2025)</a> — 含蔚山·庆南`};
const TSRC={
 ko:` · 전국 시·도 및 수도권 상세: <a href="https://knto.or.kr" target="_blank" rel="noopener">한국관광공사 TourAPI</a>`,
 en:` · Nationwide & metro areas: <a href="https://knto.or.kr" target="_blank" rel="noopener">KTO TourAPI</a>`,
 ja:` · 全国市・道: <a href="https://knto.or.kr" target="_blank" rel="noopener">韓国観光公社 TourAPI</a>`,
 zh:` · 全国市·道: <a href="https://knto.or.kr" target="_blank" rel="noopener">韩国观光公社 TourAPI</a>`};
// ── Firebase: 계정 로그인(Google/Apple) + Firestore 저장 ──
firebase.initializeApp({apiKey:"AIzaSyCes21kZAZGrTlL0rOSLjGivsXVwU4xaHs",authDomain:"food-trip-5c302.firebaseapp.com",projectId:"food-trip-5c302",storageBucket:"food-trip-5c302.firebasestorage.app",messagingSenderId:"392054177863",appId:"1:392054177863:web:b957c32238aa0f4e15b162"});
const fbAuth=firebase.auth(),fdb=firebase.firestore();
let fbUser=null;
const AUTH={
 ko:{login:"로그인",title:"로그인",desc:"로그인하면 찜 ♥ · 가본 곳 ✓ 이 계정에 저장되어 어느 기기에서든 이어볼 수 있어요.",google:"Google로 계속하기",apple:"Apple로 계속하기",logout:"로그아웃",err:"로그인에 실패했어요. 잠시 후 다시 시도해 주세요.",appleNotReady:"Apple 로그인은 준비 중이에요. Google로 로그인해 주세요."},
 en:{login:"Sign in",title:"Sign in",desc:"Sign in to save ♥ wishlist and ✓ visited places to your account and sync across devices.",google:"Continue with Google",apple:"Continue with Apple",logout:"Sign out",err:"Sign-in failed. Please try again.",appleNotReady:"Apple sign-in is coming soon. Please use Google."},
 ja:{login:"ログイン",title:"ログイン",desc:"ログインすると ♥ キープ・✓ 行った所がアカウントに保存され、端末間で同期されます。",google:"Googleで続行",apple:"Appleで続行",logout:"ログアウト",err:"ログインに失敗しました。もう一度お試しください。",appleNotReady:"Appleログインは準備中です。Googleをご利用ください。"},
 zh:{login:"登录",title:"登录",desc:"登录后，收藏 ♥ 和去过 ✓ 将保存到您的账户并跨设备同步。",google:"通过 Google 继续",apple:"通过 Apple 继续",logout:"退出登录",err:"登录失败，请稍后再试。",appleNotReady:"Apple 登录即将推出，请先使用 Google。"}};
function AT(){return AUTH[state.lang]}
// ── 내 저장 (가본 곳 / 찜 + 우선순위 1~3) — 로그인 계정(Firestore)에 저장 ──
const store={v:{},w:{},_t:null,
 save(){if(!fbUser)return;clearTimeout(this._t);
  this._t=setTimeout(()=>{fdb.collection("users").doc(fbUser.uid).set({v:store.v,w:store.w,up:firebase.firestore.FieldValue.serverTimestamp()}).catch(()=>{})},400)}};
function ridOf(reg,sec,r){const base=sec+"|"+((r.n&&r.n.ko)||"")+"|"+(((r.a&&r.a.ko)||"").slice(0,24));return reg==="busan"?base:reg+"@"+base}
function rid(r){return ridOf(state.region,state.sec,r)}
function myCounts(){let v=0,w=0;rows().forEach(r=>{const id=rid(r);if(store.v[id])v++;if(store.w[id])w++});return {v,w}}
let ALLIDX=null;
function allIdx(){if(!ALLIDX){ALLIDX={};Object.keys(DB).forEach(reg=>Object.keys(DB[reg]).forEach(sec=>DB[reg][sec].forEach(r=>{ALLIDX[ridOf(reg,sec,r)]={reg,sec,r}})))}return ALLIDX}
const PRIO_COL=["","#d2453b","#e8632c","#7a8896"];
const state={region:(()=>{const s=localStorage.getItem("bf_region");return (s&&REGMETA[s])?s:"busan"})(),sec:"food",q:"",cat:"전체",gu:"전체",sort:"def",view:"list",radius:0,loc:null,mine:"all",lang:(()=>{const s=localStorage.getItem("bf_lang");if(s)return s;const n=(navigator.language||"ko").slice(0,2);return ["en","ja","zh"].includes(n)?n:"ko"})()};
function tr(o){if(!o)return "";const L=state.lang;if(L==="zh")return o.en||o.ko||"";return o[L]||o.en||o.ko||""}
function catName(k){const m=CAT_I18N[k];if(!m)return k;return state.lang==="ko"?k:(m[state.lang]||k)}
function guName(k){const m=GU_I18N[k];if(!m)return k;return state.lang==="ko"?k:(m[state.lang]||k)}
function secName(k){return SECNAME[k][state.lang]||SECNAME[k].ko}
function U(){return UI[state.lang]}
const rows=()=>((DB[state.region]||{})[state.sec])||[];
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
function sortName(k){return k==="dist"?LT().nearest:k==="prio"?MT().prioSort:U().sorts[k]}
function ddLabelText(){const m=state.mine==="v"?" · ✓":state.mine==="w"?" · ♥":"";return sortName(state.sort)+(state.radius>0?` · ${state.radius}km`:"")+m}
function renderDD(){const lt=LT(),mt=MT(),mc=myCounts();
  let h=`<div class="dd-h">${lt.sortLabel}</div>`;
  ["def","rate","view","like","name","prio","dist"].forEach(k=>h+=`<div class="dd-opt${state.sort===k?" on":""}" data-g="s" data-v="${k}"><span>${sortName(k)}</span>${CK}</div>`);
  h+=`<div class="dd-div"></div><div class="dd-h">💾 ${mt.mine}</div>`;
  [["all",mt.all,""],["v","✓ "+mt.vList,mc.v],["w","♥ "+mt.wList,mc.w]].forEach(([v,lab,n])=>h+=`<div class="dd-opt${state.mine===v?" on":""}" data-g="m" data-v="${v}"><span>${lab}${n!==""?` <i class="ct">${n}</i>`:""}</span>${CK}</div>`);
  h+=`<div class="dd-div"></div><div class="dd-h">📍 ${lt.nearme}</div>`;
  [[0,lt.all]].concat([1,3,5,10].map(n=>[n,`${n}km ${lt.within}`])).forEach(([v,lab])=>h+=`<div class="dd-opt${state.radius===v?" on":""}" data-g="r" data-v="${v}"><span>${lab}</span>${CK}</div>`);
  document.getElementById("ddPanel").innerHTML=h;
  document.getElementById("ddLabel").textContent=ddLabelText();
  updateMlBadge();
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
// 평점 정렬 점수: 평가 수가 적으면 3.0 쪽으로 평활 — 리뷰 2개짜리 5.0이 상위 독식하지 않게
function rateScore(r){return r.rt?(r.rt*r.rc+3.0*15)/(r.rc+15):-1}
function starHtml(r){return r.rt?`<span class="rate">★ ${r.rt.toFixed(1)}<i>(${r.rc>=1000?(r.rc/1000).toFixed(1)+"k":r.rc})</i></span>`:""}
function filtered(){
  const q=norm(state.q);
  let list=rows().filter(r=>{
    if(state.cat!=="전체"&&r.c!==state.cat)return false;
    if(state.gu!=="전체"&&r.g!==state.gu)return false;
    if(state.radius>0&&state.loc){const dk=distKm(r);if(dk==null||dk>state.radius)return false}
    if(state.mine==="v"&&!store.v[rid(r)])return false;
    if(state.mine==="w"&&!store.w[rid(r)])return false;
    if(q){const hay=norm(tr(r.n)+tr(r.a)+r.g+r.c+(r.n&&r.n.ko||"")+tr(r.d)+(r.of||""));if(!hay.includes(q))return false}
    return true;
  });
  const s=state.sort;
  if(s==="dist"&&state.loc)list=[...list].sort((a,b)=>(distKm(a)??1e9)-(distKm(b)??1e9));
  else if(s==="rate")list=[...list].sort((a,b)=>rateScore(b)-rateScore(a));
  else if(s==="prio")list=[...list].sort((a,b)=>(store.w[rid(a)]||9)-(store.w[rid(b)]||9));
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
const PH_EMOJI={"카페·베이커리":"☕","카페·디저트":"☕","해산물·회":"🐟","회·해산물":"🐟","고기·구이":"🥩","면·국물":"🍜","면류":"🍜","국밥·탕":"🍲","한식·백반":"🍚","중식":"🥟","일식":"🍣","일식·돈카츠":"🍣","양식·세계요리":"🍝","양식·파스타":"🍝","분식·주점":"🍢","분식":"🍢","치킨·호프":"🍗","백화점·몰":"🏬","전통시장":"🧺","호텔":"🏨","축제·행사":"🎉"};
const SEC_PH={sights:"🏞️",food:"🍽️",usulleng:"🍽️",festival:"🎉",stay:"🏨",shopping:"🛍️"};
function phDiv(r,hidden){const col=catColor(r.c);const e=PH_EMOJI[r.c]||SEC_PH[state.sec]||"📍";
  return `<div class="ph" style="${hidden?"display:none;":""}background:linear-gradient(135deg,${col}1f,${col}52)">${e}</div>`}
const HEART='<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 21s-7.5-4.9-9.8-9.2C.7 8.9 2.2 5.4 5.4 4.6c1.9-.5 3.9.2 5.1 1.7L12 8l1.5-1.7c1.2-1.5 3.2-2.2 5.1-1.7 3.2.8 4.7 4.3 3.2 7.2C19.5 16.1 12 21 12 21z"/></svg>';
const CHKI='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><path d="M4 12.5l5 5L20 6.5"/></svg>';
function saveBar(r){const id=esc(rid(r)),iv=!!store.v[rid(r)],iw=store.w[rid(r)]||0,mt=MT();
  return `<div class="savebar">${iw?`<button class="prio" data-act="p" data-id="${id}" style="background:${PRIO_COL[iw]}" title="${mt.prioSort}">⚑ ${mt.p[iw]}</button>`:""}<button class="sbtn w${iw?" on":""}" data-act="w" data-id="${id}" aria-label="${mt.wish}" title="${mt.wish}">${HEART}</button><button class="sbtn v${iv?" on":""}" data-act="v" data-id="${id}" aria-label="${mt.visited}" title="${mt.visited}">${CHKI}</button></div>`}
function card(r){
  const col=catColor(r.c);
  const hl=highlight(r);
  const hrs=esc(tr(r.h)),cls=(tr(r.x)||"").trim();
  const closedTxt=cls&&!/^(연중무휴|연중 무휴|Open (365|every)|無休)/i.test(cls)?" · "+esc(cls):"";
  const tel=(r.p||"").replace(/[^0-9+]/g,"");
  const mapq=encodeURIComponent(tr(r.n)+" "+r.g);
  const st=state.sec==="festival"?fstatus(r):null;
  const stColor={ongoing:"#2e9e5b",upcoming:"#0a6ebd",ended:"#9aa6b2"}[st];
  const img=r.t?`<img loading="lazy" src="${esc(r.t)}" alt="${esc(tr(r.n))}" onerror="this.style.display='none';this.nextElementSibling.style.display='flex'">${phDiv(r,true)}`:phDiv(r,false);
  const nameHref=r.u||("https://map.kakao.com/?q="+mapq);
  return `<article class="card"><div class="thumb">${img}<span class="badge" style="background:${col}">${esc(catName(r.c))}</span>${r.g?`<span class="gbadge">${esc(guName(r.g))}</span>`:""}${st?`<span class="statusb" style="background:${stColor}">${U()[st]}</span>`:""}${saveBar(r)}</div>
  <div class="body"><a class="name" href="${esc(nameHref)}" target="_blank" rel="noopener">${esc(tr(r.n))}</a>
  ${hl&&hl.t?`<div class="hl">${hl.ic}<span>${esc(hl.t)}</span></div>`:""}
  ${r.of?`<div class="row"><span class="ic">📮</span><span>${esc(r.of)} ${MT().pick}${r.ed?` · <b>${esc(r.ed)}</b>`:""}</span></div>`:""}
  ${(tr(r.a)||state.loc)?`<div class="row">${PIN}<span>${state.loc&&distKm(r)!=null?`<span class="dist">${fmtDist(distKm(r))}</span> · `:""}${esc(tr(r.a))}</span></div>`:""}
  ${hrs&&state.sec!=="festival"?`<div class="row">${CLK}<span>${hrs}${closedTxt}</span></div>`:""}
  ${tr(r.d)?`<div class="desc">${esc(tr(r.d))}</div>`:""}
  ${(r.rt||r.v||r.l)?`<div class="stat">${starHtml(r)}${r.v?"👁 "+r.v.toLocaleString():""} ${r.l?"&nbsp; ♥ "+r.l:""}</div>`:""}
  <div class="acts">${tel?`<a class="act call" href="tel:${tel}"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 16.9v3a2 2 0 01-2.2 2 19.8 19.8 0 01-8.6-3 19.5 19.5 0 01-6-6 19.8 19.8 0 01-3-8.6A2 2 0 014.1 2h3a2 2 0 012 1.7c.1.9.3 1.8.6 2.6a2 2 0 01-.5 2.1L8 9.6a16 16 0 006 6l1.2-1.2a2 2 0 012.1-.5c.8.3 1.7.5 2.6.6a2 2 0 011.7 2z"/></svg>${U().call}</a>`:""}
  <a class="act" href="https://map.kakao.com/?q=${mapq}" target="_blank" rel="noopener">${PIN.replace('class="ic" ','')}${U().mapBtn}</a>
  ${r.u?`<a class="act" href="${esc(r.u)}" target="_blank" rel="noopener">${U().detail}</a>`:""}</div></div></article>`;
}

let map,cluster,mapReady=false;
function initMap(){if(mapReady)return;map=L.map("map",{zoomControl:true}).setView(REG().c,REG().z);
  L.tileLayer("https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",{attribution:'© <a href="https://openstreetmap.org/copyright">OpenStreetMap</a> · © <a href="https://carto.com/">CARTO</a>',subdomains:"abcd",maxZoom:19}).addTo(map);
  cluster=L.markerClusterGroup({maxClusterRadius:48,showCoverageOnHover:false});map.addLayer(cluster);mapReady=true}
function popHtml(r){const tel=(r.p||"").replace(/[^0-9+]/g,"");const hl=highlight(r);const mapq=encodeURIComponent(tr(r.n)+" "+r.g);
  const id=esc(rid(r)),iv=!!store.v[rid(r)],iw=store.w[rid(r)]||0;
  return `<div class="pop">${r.t?`<img class="pimg" src="${esc(r.t)}" alt="" onerror="this.style.display='none'">`:""}<div class="pbody"><div class="pn">${esc(tr(r.n))}</div>${hl&&hl.t?`<div class="pm">${esc(hl.t)}</div>`:""}<div class="pa">${r.rt?starHtml(r)+" · ":""}${state.loc&&distKm(r)!=null?`<span class="dist">${fmtDist(distKm(r))}</span> · `:""}${esc(catName(r.c))}${r.g?" · "+esc(guName(r.g)):""}${r.of?`<br>📮 ${esc(r.of)} ${MT().pick}`:""}<br>${esc(tr(r.a))}</div><div class="pacts">${tel?`<a class="call" href="tel:${tel}">${U().call}</a>`:""}<a href="https://map.kakao.com/?q=${mapq}" target="_blank" rel="noopener">${U().mapBtn}</a>${r.u?`<a href="${esc(r.u)}" target="_blank" rel="noopener">${U().detail}</a>`:""}<a class="sv v${iv?" on":""}" data-act="v" data-id="${id}" title="${MT().visited}">✓</a><a class="sv w${iw?" on":""}" data-act="w" data-id="${id}" title="${MT().wish}">♥</a></div></div></div>`}
function renderMap(list){initMap();cluster.clearLayers();const ms=[];
  list.forEach(r=>{if(r.lat==null||r.lng==null)return;const col=catColor(r.c);
    const m=L.marker([r.lat,r.lng],{icon:L.divIcon({className:"",html:`<div class="mk" style="background:${col}"></div>`,iconSize:[16,16],iconAnchor:[8,15],popupAnchor:[0,-14]})});
    m.bindPopup(()=>popHtml(r));ms.push(m)});
  cluster.addLayers(ms);setTimeout(()=>map.invalidateSize(),60);
  if(ms.length){try{const b=cluster.getBounds();b.isValid()&&map.fitBounds(b.pad(.12),{maxZoom:14})}catch(e){}}
  else map.setView(REG().c,REG().z)}

function render(){const list=filtered();document.getElementById("count").innerHTML=U().count(list.length);
  if(state.view==="map")renderMap(list);
  else document.getElementById("grid").innerHTML=list.length?list.map(card).join(""):`<div class="empty"><div class="em">🔍</div><p>${U().empty}</p></div>`}

function setToolsH(){document.documentElement.style.setProperty("--toolsH",(document.querySelector(".tools").offsetHeight+document.querySelector(".hero").offsetHeight)+"px")}
function buildTabs(){const rm=REGMETA[state.region]||{};document.getElementById("tabs").innerHTML=SEC.filter(s=>rm[s.k]).map(s=>`<button class="tab${s.k===state.sec?" on":""}" data-s="${s.k}">${s.i} ${secName(s.k)}<span class="tn">${rm[s.k]}</span></button>`).join("")}
function buildRegs(){const el=document.getElementById("regs");el.hidden=REGIONS.length<2;
  el.innerHTML=REGIONS.map(r=>{const tot=Object.values(REGMETA[r.k]).reduce((a,n)=>a+n,0);
    return `<button class="reg${r.k===state.region?" on":""}" data-r="${r.k}">${r.i} ${regName(r)}<span class="rn">${tot>=1000?(tot/1000).toFixed(1)+"k":tot}</span></button>`}).join("")}
function regionUI(){
  document.getElementById("subtitle").textContent=U().sub(state.sec,rows().length);
  buildChips("cats","c","cat",catName);buildChips("gus","g","gu",guName);
  if(mapReady)try{map.closePopup()}catch(e){}
  renderDD();render();setToolsH()}
function switchRegion(k){state.region=k;localStorage.setItem("bf_region",k);
  const rm=REGMETA[k]||{};
  if(!rm[state.sec]){const f=SEC.find(s=>rm[s.k]);state.sec=f?f.k:"food"}
  state.cat="전체";state.gu="전체";state.q="";document.getElementById("q").value="";
  buildRegs();
  document.getElementById("brand").textContent=brandText();
  buildTabs();showLoading();
  ensureRegion(k).then(()=>{if(state.region!==k)return;regionUI();window.scrollTo({top:0,behavior:"instant"})})
    .catch(showLoadErr)}
function applyLang(){const u=U();document.documentElement.lang=state.lang;
  document.getElementById("brand").textContent=brandText();
  buildRegs();
  document.getElementById("subtitle").textContent=u.sub(state.sec,rows().length);
  document.getElementById("q").placeholder=u.search;
  document.querySelector(".vlist").textContent=u.list;document.querySelector(".vmap").textContent=u.map;
  document.getElementById("footer").innerHTML=u.foot+" · "+u.src+USRC[state.lang]+(REGIONS.length>1?TSRC[state.lang]:"");
  document.getElementById("maphint").innerHTML=u.hint;
  document.getElementById("vLabelTotal").textContent=VIS[state.lang].total;
  document.getElementById("vLabelToday").textContent=VIS[state.lang].today;
  renderAuthUI();
  if(document.getElementById("llay").classList.contains("show"))renderLL();
  renderDD();
  document.getElementById("locate").setAttribute("aria-label",LT().me);
  document.querySelectorAll("#langs button").forEach(b=>b.classList.toggle("on",b.dataset.l===state.lang));
  buildTabs();
  if(DB[state.region]){buildChips("cats","c","cat",catName);buildChips("gus","g","gu",guName);render()}
  setToolsH()}

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
  else if(g==="m"){state.mine=v}
  else{state.radius=+v;if(+v>0&&!state.loc)need=true}
  renderDD();if(need)locate();else render()});
document.addEventListener("click",e=>{if(!e.target.closest("#dd"))ddOpen(false)});
// ── 가본 곳 ✓ / 찜 ♥ 토글 (카드·지도 팝업 공용) ──
document.addEventListener("click",e=>{
  const b=e.target.closest("[data-act]");if(!b)return;
  e.preventDefault();
  if(!fbUser){llOpen(true);return}
  const act=b.dataset.act,id=b.dataset.id;
  if(act==="v"){if(store.v[id])delete store.v[id];else store.v[id]=1}
  else if(act==="w"){if(store.w[id])delete store.w[id];else store.w[id]=2}
  else if(act==="p"){store.w[id]=(store.w[id]%3)+1}
  store.save();renderDD();
  if(e.target.closest("#mlay")){renderML();if(state.view==="list")render();return}
  const pop=e.target.closest(".pop");
  if(pop){pop.querySelectorAll("[data-act]").forEach(x=>{const a=x.dataset.act;
    if(a==="v")x.classList.toggle("on",!!store.v[id]);
    if(a==="w")x.classList.toggle("on",!!store.w[id])})}
  else render();
});
// ── 내 저장 목록 패널 ──
const SECICON=Object.fromEntries(SEC.map(s=>[s.k,s.i]));
let mlTab="w";
function updateMlBadge(){const n=new Set(Object.keys(store.w).concat(Object.keys(store.v))).size;const el=document.getElementById("mlCount");el.hidden=!n;el.textContent=n}
function renderML(){
  const mt=MT(),idx=allIdx();
  const wIds=Object.keys(store.w).sort((a,b)=>store.w[a]-store.w[b]),vIds=Object.keys(store.v);
  document.getElementById("mlTitle").textContent="💾 "+mt.mine;
  const tw=document.getElementById("mlTabW"),tv=document.getElementById("mlTabV");
  tw.textContent=`♥ ${mt.wList} ${wIds.length}`;tv.textContent=`✓ ${mt.vList} ${vIds.length}`;
  tw.classList.toggle("on",mlTab==="w");tv.classList.toggle("on",mlTab==="v");
  const ids=mlTab==="w"?wIds:vIds;
  const h=ids.map(id=>{
    const e=idx[id];
    let reg=e?e.reg:"busan",rest=id;const at=id.indexOf("@");
    if(!e&&at>0){reg=id.slice(0,at);rest=id.slice(at+1)}
    const parts=rest.split("|");
    const name=e?tr(e.r.n):parts[1],sec=e?e.sec:parts[0];
    const rm=REGIONS.find(x=>x.k===reg);
    const sub=[(REGIONS.length>1&&rm)?regName(rm):"",e?catName(e.r.c):"",e&&e.r.g?guName(e.r.g):(e?"":parts[2]||"")].filter(Boolean).join(" · ");
    const p=store.w[id]||0;
    const gone=!e&&!REGMETA[reg];  // 지역 pack 미로딩이면 클릭 시 로드 (완전 삭제된 항목만 gone)
    return `<div class="mitem${gone?" gone":""}" data-mid="${esc(id)}"><span class="mi">${SECICON[sec]||"📍"}</span><div class="mtx"><div class="mn">${esc(name)}</div><div class="ms">${esc(sub)}</div></div>${mlTab==="w"&&p?`<button class="prio" data-act="p" data-id="${esc(id)}" style="background:${PRIO_COL[p]}">⚑ ${mt.p[p]}</button>`:""}<button class="sbtn ${mlTab==="w"?"w":"v"} on" data-act="${mlTab}" data-id="${esc(id)}">${mlTab==="w"?HEART:CHKI}</button></div>`}).join("");
  document.getElementById("mlist").innerHTML=h||`<div class="mempty">${mt.empty}</div>`;
}
function mlOpen(o){document.getElementById("mlay").classList.toggle("show",o);if(o)renderML()}
document.getElementById("mlBtn").addEventListener("click",()=>{fbUser?mlOpen(true):llOpen(true)});
// ── 로그인 모달 + 계정 상태 ──
const GLOGO='<svg viewBox="0 0 24 24"><path fill="#4285F4" d="M23.5 12.3c0-.9-.1-1.5-.3-2.2H12v4.1h6.5c-.1 1.1-.8 2.7-2.4 3.8l3.7 2.9c2.3-2.1 3.7-5.1 3.7-8.6z"/><path fill="#34A853" d="M12 24c3.2 0 6-1.1 7.9-2.9l-3.7-2.9c-1 .7-2.4 1.2-4.2 1.2-3.2 0-6-2.1-7-5.1l-3.9 3C3.1 21.3 7.2 24 12 24z"/><path fill="#FBBC05" d="M5 14.3c-.2-.7-.4-1.5-.4-2.3s.2-1.6.4-2.3l-3.9-3C.4 8.3 0 10.1 0 12s.4 3.7 1.1 5.3l3.9-3z"/><path fill="#EA4335" d="M12 4.6c1.8 0 3 .8 3.7 1.4l3.3-3.2C17.9 1 15.2 0 12 0 7.2 0 3.1 2.7 1.1 6.7l3.9 3c1-3 3.8-5.1 7-5.1z"/></svg>';
const ALOGO='<svg viewBox="0 0 24 24" fill="currentColor"><path d="M16.7 12.9c0-2.4 2-3.6 2.1-3.7-1.1-1.7-2.9-1.9-3.5-1.9-1.5-.2-2.9.9-3.7.9-.8 0-1.9-.9-3.2-.8-1.6 0-3.1 1-4 2.4-1.7 3-.4 7.4 1.2 9.8.8 1.2 1.8 2.5 3.1 2.4 1.2-.1 1.7-.8 3.2-.8 1.5 0 1.9.8 3.2.8 1.3 0 2.2-1.2 3-2.4.9-1.4 1.3-2.7 1.3-2.8-.1 0-2.6-1-2.7-3.9zM14.4 5.6c.7-.8 1.1-1.9 1-3.1-1 0-2.2.7-2.9 1.5-.6.7-1.2 1.9-1 3 1.1.1 2.2-.6 2.9-1.4z"/></svg>';
function renderAuthUI(){const av=document.getElementById("authAv"),lb=document.getElementById("authLabel");
  if(fbUser){if(fbUser.photoURL){av.src=fbUser.photoURL;av.hidden=false;lb.textContent=""}
    else{av.hidden=true;lb.textContent=(fbUser.displayName||fbUser.email||"👤").split(" ")[0]}}
  else{av.hidden=true;av.removeAttribute("src");lb.textContent=AT().login}}
function renderLL(){const a=AT();
  document.getElementById("llTitle").textContent=fbUser?(fbUser.displayName||a.title):a.title;
  document.getElementById("llBody").innerHTML=fbUser
    ?`<p class="lldesc">${esc(fbUser.email||"")}</p><button class="lbtn out" id="btnLogout">${a.logout}</button>`
    :`<p class="lldesc">${a.desc}</p><button class="lbtn g" data-prov="google">${GLOGO}<span>${a.google}</span></button><button class="lbtn a" data-prov="apple">${ALOGO}<span>${a.apple}</span></button>`}
function llOpen(o){document.getElementById("llay").classList.toggle("show",o);if(o)renderLL()}
function fbLogin(prov){
  const p=prov==="apple"?new firebase.auth.OAuthProvider("apple.com"):new firebase.auth.GoogleAuthProvider();
  fbAuth.signInWithPopup(p).catch(e=>{
    if(e&&e.code==="auth/popup-blocked")fbAuth.signInWithRedirect(p);
    else if(e&&e.code==="auth/operation-not-allowed")toast(AT().appleNotReady);
    else if(e&&e.code!=="auth/popup-closed-by-user"&&e.code!=="auth/cancelled-popup-request")toast(AT().err)})}
document.getElementById("authBtn").addEventListener("click",()=>llOpen(true));
document.getElementById("llClose").addEventListener("click",()=>llOpen(false));
document.getElementById("llay").addEventListener("click",e=>{if(e.target.id==="llay")llOpen(false)});
document.getElementById("llBody").addEventListener("click",e=>{
  const p=e.target.closest("[data-prov]");
  if(p){fbLogin(p.dataset.prov);return}
  if(e.target.closest("#btnLogout"))fbAuth.signOut().then(()=>llOpen(false))});
fbAuth.onAuthStateChanged(async u=>{
  fbUser=u;
  if(u){
    llOpen(false);
    let cv={},cw={};
    try{const s=await fdb.collection("users").doc(u.uid).get();if(s.exists){cv=s.data().v||{};cw=s.data().w||{}}}catch(e){}
    // 예전 기기(localStorage) 저장분은 첫 로그인 때 계정으로 병합 (계정 데이터 우선)
    const lv=JSON.parse(localStorage.getItem("bf_visited")||"{}"),lw=JSON.parse(localStorage.getItem("bf_wish")||"{}");
    store.v=Object.assign({},lv,cv);store.w=Object.assign({},lw,cw);
    if(Object.keys(lv).length||Object.keys(lw).length){
      try{await fdb.collection("users").doc(u.uid).set({v:store.v,w:store.w},{merge:true});
        localStorage.removeItem("bf_visited");localStorage.removeItem("bf_wish")}catch(e){}}
  }else{store.v={};store.w={}}
  renderAuthUI();renderDD();render();
  if(document.getElementById("mlay").classList.contains("show"))renderML();
});
document.getElementById("mlClose").addEventListener("click",()=>mlOpen(false));
document.getElementById("mlay").addEventListener("click",e=>{if(e.target.id==="mlay")mlOpen(false)});
document.querySelectorAll(".mtab").forEach(b=>b.addEventListener("click",()=>{mlTab=b.dataset.t;renderML()}));
document.getElementById("mlist").addEventListener("click",e=>{
  if(e.target.closest("[data-act]"))return;
  const it=e.target.closest(".mitem");if(!it||it.classList.contains("gone"))return;
  const id=it.dataset.mid,ent=allIdx()[id];
  if(!ent){ // 미로딩 지역: pack 로드 후 이동
    let reg="busan",rest=id;const at=id.indexOf("@");
    if(at>0){reg=id.slice(0,at);rest=id.slice(at+1)}
    if(!REGMETA[reg])return;
    const parts=rest.split("|");
    mlOpen(false);switchRegion(reg);
    ensureRegion(reg).then(()=>{
      if(REGMETA[reg][parts[0]]){state.sec=parts[0];buildTabs()}
      state.mine="all";state.q=parts[1]||"";document.getElementById("q").value=state.q;
      regionUI()}).catch(()=>{});
    return;
  }
  mlOpen(false);
  if(state.region!==ent.reg){state.region=ent.reg;localStorage.setItem("bf_region",ent.reg);buildRegs();document.getElementById("brand").textContent=brandText()}
  if(state.sec!==ent.sec)switchSection(ent.sec);
  else{state.cat="전체";state.gu="전체";buildChips("cats","c","cat",catName);buildChips("gus","g","gu",guName)}
  state.mine="all";state.q=tr(ent.r.n);document.getElementById("q").value=state.q;
  renderDD();render();window.scrollTo({top:0,behavior:"instant"});
});
document.getElementById("locate").addEventListener("click",()=>{if(state.sort==="def")state.sort="dist";renderDD();locate()});
document.getElementById("viewtog").addEventListener("click",e=>{const b=e.target.closest("button");if(b)setView(b.dataset.v)});
document.getElementById("tabs").addEventListener("click",e=>{const b=e.target.closest(".tab");if(b&&b.dataset.s!==state.sec)switchSection(b.dataset.s)});
document.getElementById("regs").addEventListener("click",e=>{const b=e.target.closest(".reg");if(b&&b.dataset.r!==state.region)switchRegion(b.dataset.r)});
document.getElementById("langs").addEventListener("click",e=>{const b=e.target.closest("button");if(!b)return;state.lang=b.dataset.l;localStorage.setItem("bf_lang",state.lang);applyLang()});
const topBtn=document.getElementById("top");addEventListener("scroll",()=>topBtn.classList.toggle("show",state.view==="list"&&scrollY>600),{passive:true});
topBtn.addEventListener("click",()=>scrollTo({top:0,behavior:"smooth"}));addEventListener("resize",setToolsH);

// ── 방문자수 (Abacus 무료 카운터) ──
function countUp(el,to){to=+to||0;const from=+(el.dataset.v||0);el.dataset.v=to;const dur=750,t0=performance.now();
  (function step(t){const p=Math.min(1,(t-t0)/dur),e=1-Math.pow(1-p,3);el.textContent=Math.round(from+(to-from)*e).toLocaleString();if(p<1)requestAnimationFrame(step)})(t0)}
function visitorCounter(){
  const NS="busan-when-in-2026",base="https://abacus.jasoncameron.dev";
  const today="d"+new Date().toLocaleDateString("en-CA").replace(/-/g,"");
  const counted=sessionStorage.getItem("bf_counted"),verb=counted?"get":"hit";
  const j=r=>r.ok?r.json():null;
  Promise.all([
    fetch(`${base}/${verb}/${NS}/total`).then(j),
    fetch(`${base}/${verb}/${NS}/${today}`).then(j)
  ]).then(([t,d])=>{
    sessionStorage.setItem("bf_counted","1");
    if(t&&typeof t.value==="number"){
      document.getElementById("visits").hidden=false;
      countUp(document.getElementById("vTotal"),t.value);
      countUp(document.getElementById("vToday"),(d&&d.value)||0);
    }
  }).catch(()=>{});
}
applyLang();
showLoading();
ensureRegion(state.region).then(()=>regionUI()).catch(showLoadErr);
visitorCounter();
</script>
</body>
</html>"""

out = (HTML.replace("__REGMETA__", meta_js).replace("__TOTAL__", str(total))
           .replace("__TODAY__", updated).replace("__UPDATED__", updated))
with open("index.html", "w", encoding="utf-8") as f:
    f.write(out)
print(f"index.html 생성 ({len(out):,} bytes)")
