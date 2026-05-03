# Data Source Setup

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

글로벌 산업 흐름:

```bash
python3 collect_news.py \
  --tickers NVDA TSM MU ASML VRT ETN TSLA TM \
  --sources google gdelt alpha_vantage finnhub newsapi sec \
  --keywords "AI infrastructure" HBM datacenter capex earnings guidance \
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
- 뉴스는 중복과 노이즈가 많으므로 `Data Quality Notes`에 출처 편향을 반드시 남겨야 합니다.
