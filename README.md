# 📍 그곳에 가면 · Food Trip Korea

지역을 골라 떠나는 전국 맛집·관광 웹 가이드. **전국 17개 시·도 + 수도권 상세(수원·안산·판교역·정자역·서현역)**, 총 **22,000여 곳**을 카카오 별점·지도·다국어(한·영·일·중)로 둘러보는 모바일 반응형 웹앱.

> 데이터 출처: [한국관광공사 TourAPI 4.0](https://api.visitkorea.or.kr) · [부산관광포털 비짓부산](https://www.visitbusan.net) (부산광역시) · [우체국 추천 맛집가이드](https://github.com/jk-ayaan/usulleng) (부산지방우정청, 2024·2025) · 별점: 카카오맵

## 지역

| 구분 | 지역 |
|---|---|
| 큐레이션 | 🌊 부산 1,324 (비짓부산 + 📮우슐랭 318) |
| 전국 시·도 | 서울 2,314 · 경기 4,049 · 강원 2,600 · 경북 1,655 · 경남 1,696 · 전남 1,447 · 전북 1,338 · 충남 1,294 · 제주 1,028 · 충북 1,005 · 인천 664 · 대구 560 · 대전 347 · 울산 278 · 광주 208 · 세종 102 |
| 수도권 상세 | 수원 298 · 안산 145 · 판교역 40 · 정자역 40 · 서현역 49 (역은 반경 2km) |

## 기능

- 🗺 **지역 선택 + lazy-load** — 선택한 지역 데이터만 내려받음(index 66KB, 지역팩 57KB~1.7MB), 지역별 브랜드("서울에 가면"/"When in Seoul")
- ⭐ **카카오맵 별점** — 실제 별점·평가 수 표시, **평점순** 정렬(평가 수 보정)
- 🔎 검색·필터(구·군/종류 칩) · 거리순·반경 필터(내 위치)
- ✓/♥ **가본 곳·찜(우선순위)** — Google/Apple 로그인 계정(Firestore)에 저장, 기기 간 동기화
- 💾 **내 저장 패널** — 전 지역 통합 목록, 탭하면 해당 지역 로드 후 이동
- 🌐 다국어 한·영·일·중 (부산: 공식 번역 / 그 외: 한국어 기준) · 📱 모바일 반응형 · 🗺 Leaflet 지도·클러스터

> ⚠️ lazy-load 구조라 로컬에서는 `python3 -m http.server`로 띄워야 동작합니다 (file:// 불가).

## 데이터 파이프라인

```bash
python3 grab.py all                          # 부산 (비짓부산) → data/busan/
python3 grab_usulleng.py                     # 우슐랭 → data/busan/usulleng.json
TOURAPI_KEY='...' python3 grab_gyeonggi.py   # 수도권 상세 5곳 (TourAPI)
TOURAPI_KEY='...' python3 grab_korea.py      # 전국 16개 시·도 (TourAPI, 설명 생략)
python3 grab_ratings.py [region ...]         # 카카오맵 별점 (+썸네일 보충)
python3 grab_thumb_fix.py                    # 썸네일 정비 (깨진 URL 정리 + 카카오 대표사진)
python3 build_app.py                         # → index.html + pack/<region>.json
```

| 파일 | 설명 |
|---|---|
| `grab_korea.py` | TourAPI areaBasedList2/searchFestival2 — 전국 시·도, 시·군·구 추출, 카테고리 매핑 |
| `grab_gyeonggi.py` | 수도권 상세 5곳 — 시 전체/역 반경 2km, overview·축제기간 포함 |
| `grab_ratings.py` | 카카오맵 별점 — 전화 일치 또는 300m 이내+이름 유사만 채택 |
| `grab_kakao_thumbs.py` / `grab_thumb_fix.py` | 카카오맵 플레이스 대표사진 매칭·정비 |
| `build_app.py` | UI 단일 HTML + 지역별 pack JSON 생성기 |

## 주의

공개 정보를 정리한 것으로 실제와 다를 수 있습니다. 방문 전 운영시간·휴무·행사기간을 확인하세요. 전국 시·도 데이터는 상세설명 없이 목록 정보만 제공됩니다(API 쿼터). 사진은 한국관광공사·비짓부산·카카오 CDN을 사용합니다. 찜·가본 곳은 로그인 계정(Firebase)에 저장됩니다.
