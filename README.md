# 🧳 Food Trip · 부산 & 수도권 맛집·관광 가이드

지역을 골라 떠나는 맛집·관광 웹 가이드. **부산**(비짓부산 + 우슐랭) · **수원 · 안산 · 판교역 · 정자역 · 서현역**(한국관광공사 TourAPI), 총 **1,896곳**을 지도·다국어(한·영·일·중)로 둘러보는 모바일 반응형 웹앱.

> 데이터 출처: [부산관광포털 비짓부산](https://www.visitbusan.net/index.do?menuCd=DOM_000000201001000000) (부산광역시) · [우체국 추천 맛집가이드](https://github.com/jk-ayaan/usulleng) (부산지방우정청, 2024·2025) · [한국관광공사 TourAPI 4.0](https://api.visitkorea.or.kr)

## 지역 × 섹션

| 지역 | 곳수 | 데이터 |
|---|---|---|
| 🌊 부산 | 1,324 | 명소 212 · 음식 337 · 📮우슐랭 318 · 축제 40 · 숙박 362 · 쇼핑 55 |
| 🏯 수원 | 298 | 명소 64 · 음식 195 · 축제 8 · 숙박 20 · 쇼핑 11 |
| 🌷 안산 | 145 | 명소 53 · 음식 79 · 축제 1 · 숙박 8 · 쇼핑 4 |
| 🚄 판교역 | 40 | 역 반경 2km — 음식 24 · 명소 12 외 |
| 🚇 정자역 | 40 | 역 반경 2km — 음식 28 · 명소 10 외 |
| 🚉 서현역 | 49 | 역 반경 2km — 음식 29 · 명소 15 외 |

## 기능

- 🗺 **지역 선택** — 헤더 지역 pill로 즉시 전환, 지역별 브랜드("수원에 가면"/"When in Suwon")·지도 중심·섹션 탭 자동 구성
- 📱 **모바일 반응형** — 1열(모바일) → 4열(데스크톱)
- 🗺 **지도 보기** — Leaflet + OpenStreetMap(CARTO), 핀·클러스터, 팝업
- 🌐 **다국어** — 한국어·English·日本語·中文 (부산: 비짓부산 공식 번역 / 우슐랭·경기: 한국어 기준)
- 🔎 **검색·필터** — 이름/지역/키워드, 구·군 + 종류 칩, 정렬(거리순 포함)
- ✓ **가본 곳 체크** / ♥ **찜 + 우선순위**(높음/보통/낮음) — localStorage 저장
- 💾 **내 저장 패널** — 전 지역·섹션 통합 찜/가본 곳 목록, 우선순위 관리, 탭하면 해당 카드로 이동
- 📞 전화 · 카카오맵 길찾기 · 상세 링크(부산)

데이터가 내장된 **단일 `index.html`** 로 서버 없이 열어도 동작합니다.

## 데이터 파이프라인

```bash
python3 grab.py all                          # 부산 5개 섹션 (비짓부산) → data/busan/
python3 grab_usulleng.py                     # 우슐랭 → data/busan/usulleng.json
TOURAPI_KEY='...' python3 grab_gyeonggi.py   # 경기 5개 지역 (TourAPI) → data/<region>/
python3 build_app.py                         # data/<region>/*.json → index.html
```

| 파일 | 설명 |
|---|---|
| `grab.py` | 비짓부산 수집기 — 목록·상세 파싱, 구·군 매핑, 종류 자동 분류, 영·일 번역 |
| `grab_usulleng.py` | [usulleng](https://github.com/jk-ayaan/usulleng) → 앱 스키마 변환 |
| `grab_gyeonggi.py` | TourAPI KorService2 — 수원·안산(시 전체) + 판교·정자·서현역(반경 2km), 카테고리 매핑·overview·축제기간. `TOURAPI_KEY` 환경변수 필요 ([data.go.kr](https://www.data.go.kr) 발급) |
| `build_app.py` | 지역×섹션 단일 HTML 생성기 |
| `data/<region>/*.json` | 지역·섹션별 데이터셋 |

## 주의

공개 정보를 정리한 것으로 실제와 다를 수 있습니다. 방문 전 운영시간·휴무·행사기간을 확인하세요. 종류는 자동 분류입니다. 사진은 비짓부산·한국관광공사 서버 이미지를 사용합니다. 가본 곳·찜 데이터는 브라우저 localStorage에만 저장됩니다.
