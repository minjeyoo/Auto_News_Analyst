# 데이터 소스 설정

이 프로젝트의 목표는 국내 뉴스가 아니라 글로벌 산업 흐름, 공시, 매크로, 종목 뉴스를 함께 보는 것입니다.

## 바로 사용 가능

### GDELT

- 목적: 전세계 뉴스 흐름 탐지
- API 키: 필요 없음
- 프로젝트 소스명: `gdelt`
- 예시:

```bash
python3 collect_news.py --tickers NVDA TSM MU --sources gdelt --keywords "AI infrastructure" HBM datacenter --days 3
```

### SEC EDGAR

- 목적: 미국 상장사 공시 추적
- API 키: 필요 없음
- 프로젝트 소스명: `sec`
- 해야 할 일: `.env`에 `SEC_USER_AGENT`를 본인 이메일이 들어간 값으로 설정
- 예시:

```env
SEC_USER_AGENT=Auto-News-Analyst/0.1 your-email@example.com
```

```bash
python3 collect_news.py --tickers NVDA AAPL MSFT --sources sec --keywords --days 30
```

`--keywords`만 쓰고 뒤에 값을 넣지 않으면 공시명 필터 없이 수집합니다. `10-Q`, `8-K`만 보고 싶으면 아래처럼 명시합니다.

```bash
python3 collect_news.py --tickers NVDA AAPL MSFT --sources sec --keywords 10-Q 8-K 10-K --days 30
```

### Investing.com RSS

- 목적: 글로벌 주식시장 뉴스, 경제 뉴스, 분석 RSS 보강
- API 키: 필요 없음
- 프로젝트 소스명: `investing`
- 방식: Investing.com이 공개한 RSS 피드만 사용합니다. 웹페이지 스크래핑은 사용하지 않습니다.
- 예시:

```bash
python3 collect_news.py --tickers NVDA TSLA AAPL MSFT --sources investing --keywords AI earnings capex --days 7
```

### Bloomberg

- 목적: 기관급 뉴스와 데이터
- 무료 자동수집: 권장하지 않음
- 이유: Bloomberg 웹사이트 약관은 사전 서면 동의 없는 scraper, robot, bot, data mining 방식 접근을 금지합니다. Bloomberg News/API는 Bloomberg Professional, Terminal, Data License, B-PIPE 같은 유료/계약형 접근이 기본입니다.
- 현실적 대안: Bloomberg 원문을 직접 긁지 말고, Google News RSS, GDELT, Investing.com RSS, SEC/DART, Alpha Vantage, Finnhub, NewsAPI에서 Bloomberg가 인용되거나 같은 이벤트를 보도한 자료를 포착합니다.

## API 키 발급 필요

### Alpha Vantage

- 목적: 글로벌 시장 뉴스, 감성, 토픽 기반 뉴스
- 프로젝트 소스명: `alpha_vantage`
- `.env` 항목:

```env
ALPHA_VANTAGE_API_KEY=...
```

### Finnhub

- 목적: 종목별 글로벌 회사 뉴스
- 프로젝트 소스명: `finnhub`
- `.env` 항목:

```env
FINNHUB_API_KEY=...
```

### NewsAPI

- 목적: 범용 글로벌 영문 뉴스 백업 소스
- 프로젝트 소스명: `newsapi`
- `.env` 항목:

```env
NEWSAPI_API_KEY=...
```

### OpenDART

- 목적: 한국 상장사 공시
- 프로젝트 소스명: `dart`
- `.env` 항목:

```env
DART_API_KEY=...
```

### FRED

- 목적: 미국 금리, 인플레이션, 고용, 경기지표
- 현재 상태: `.env.example`에 키 슬롯만 준비됨. 다음 단계에서 매크로 수집기로 연결 예정.
- `.env` 항목:

```env
FRED_API_KEY=...
```

### BOK ECOS

- 목적: 한국 금리, 환율, 물가, 경기지표
- 현재 상태: `.env.example`에 키 슬롯만 준비됨. 다음 단계에서 매크로 수집기로 연결 예정.
- `.env` 항목:

```env
BOK_ECOS_API_KEY=...
```

## 추천 실행 조합

리포트/기사에서 다음 검색어를 먼저 추출:

```bash
python3 derive_keywords.py \
  --start 2026-05-03 \
  --end 2026-05-03 \
  --output derived_keywords.json
```

추출된 키워드로 다시 수집:

```bash
python3 collect_news.py \
  --tickers NVDA TSM MU ASML VRT ETN TSLA TM 삼성전자 SK하이닉스 현대차 기아 NAVER LG에너지솔루션 \
  --sources naver google google_global investing gdelt sec alpha_vantage finnhub newsapi dart \
  --keyword-file derived_keywords.json \
  --keyword-group global \
  --include-global-queries \
  --include-company-aliases \
  --days 7
```

국내 뉴스 플로우 리포트 생성:

```bash
python3 build_industry_report.py \
  --report-type daily_local_news_report \
  --start 2026-05-03 \
  --end 2026-05-03 \
  --output reports/2026-05-03_daily_local_news_report.md
```

글로벌 산업 흐름과 전세계 관련 주식 리포트 생성:

```bash
python3 build_industry_report.py \
  --report-type global_equity_theme_map \
  --start 2026-05-03 \
  --end 2026-05-03 \
  --output reports/2026-05-03_global_equity_theme_map.md
```

글로벌 산업 흐름:

```bash
python3 collect_news.py \
  --tickers NVDA TSM MU ASML VRT ETN TSLA TM \
  --sources google_global investing gdelt alpha_vantage finnhub newsapi sec \
  --keywords "AI infrastructure" HBM datacenter capex earnings guidance \
  --include-global-queries \
  --include-company-aliases \
  --days 7
```

한국 산업 흐름:

```bash
python3 collect_news.py \
  --tickers 삼성전자 SK하이닉스 현대차 기아 NAVER LG에너지솔루션 \
  --sources naver google gdelt dart \
  --keywords 실적 가이던스 수주 투자 공시 \
  --days 7
```

## 주의

- `.env`는 Git에 올리면 안 됩니다.
- API 키가 없는 소스는 빈 결과를 반환하도록 되어 있습니다.
- 뉴스는 중복과 노이즈가 많으므로 `데이터 품질 메모`에 출처 편향을 반드시 남겨야 합니다.
