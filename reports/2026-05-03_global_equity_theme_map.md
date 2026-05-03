# Global Equity Theme Map - 2026-05-03

목적: 글로벌 뉴스와 산업 자료를 기준으로 **산업 흐름 → 전세계 관련 주식 후보 → 국내 연결 후보**를 함께 정리한다.  
주의: 이 문서는 매수/매도 추천이 아니라 Auto-News-Analyst의 글로벌 산업 매핑 리포트다.

## Why The Previous Report Was Biased

이전 리포트가 국내주식 중심으로 보인 이유는 명확하다.

1. 실제 뉴스 캐시 수집을 `Naver News API` 중심으로 실행했다.
2. 대상 종목도 `삼성전자`, `SK하이닉스`, `NAVER`, `현대차`, `LG에너지솔루션`으로 국내 종목만 넣었다.
3. 글로벌 문서는 참고했지만, 결과 테이블에서 글로벌 주식을 충분히 펼치지 않았다.

따라서 앞으로 리포트는 `국내 종목 리포트`와 `글로벌 산업/주식 맵`을 분리해야 한다. 이 파일은 두 번째 용도다.

## 1. AI Infrastructure: Compute, Memory, Networking, Power

### Global Industry Flow

AI 인프라 투자 사이클은 여전히 강하다. Gartner는 2026년 전세계 반도체 매출이 1.3조 달러를 넘을 것으로 전망했고, AI processing, 데이터센터 네트워킹/전력, 메모리 가격 상승을 주요 동인으로 제시했다. Gartner의 IT spending 전망에서도 2026년 데이터센터 시스템 지출이 7,880억 달러를 넘을 것으로 제시됐다. Tom's Hardware는 Google, Amazon, Microsoft, Meta의 2026년 CAPEX가 7,250억 달러 수준으로 늘 수 있다고 보도했다. ([Gartner Semiconductor](https://www.gartner.com/en/newsroom/press-releases/2026-04-08-gartner-forecasts-worldwide-semiconductor-revenue-to-exceed-us-dollars-one-point-3-trillion-in-2026), [Gartner IT Spending](https://www.gartner.com/en/newsroom/press-releases/2026-04-22-gartner-forecasts-worldwide-it-spending-to-grow-13-point-5-percent-in-2026-totaling-6-point-31-trillion-dollars), [Tom's Hardware CAPEX](https://www.tomshardware.com/tech-industry/big-tech/big-techs-ai-spending-plans-reach-725-billion))

### Global Equity Watchlist

| Layer | Global stocks to track | Why they matter |
|---|---|---|
| AI accelerators | Nvidia (`NVDA`), AMD (`AMD`) | GPU/accelerator demand captures the first-order AI compute spend. |
| Custom AI silicon / networking | Broadcom (`AVGO`), Marvell (`MRVL`) | Hyperscalers are shifting part of the stack toward custom ASICs and high-speed networking. |
| Foundry | TSMC (`TSM`), Samsung Electronics (`005930.KS`) | Advanced-node capacity and packaging determine accelerator supply. |
| Semiconductor equipment | ASML (`ASML`), Applied Materials (`AMAT`), Lam Research (`LRCX`) | AI/HBM/advanced DRAM capacity expansion needs equipment. |
| Memory/HBM | SK hynix (`000660.KS`), Samsung Electronics (`005930.KS`), Micron (`MU`) | HBM/DRAM scarcity is the clearest direct bottleneck. |
| Cloud buyers | Microsoft (`MSFT`), Alphabet (`GOOGL`), Amazon (`AMZN`), Meta (`META`), Oracle (`ORCL`) | They are both demand drivers and margin-risk carriers because CAPEX is rising. |

### Korea Link

국내 직접 수혜는 `SK하이닉스`, `삼성전자`다. 그러나 글로벌 관점에서는 `MU`, `NVDA`, `TSM`, `ASML`, `AVGO`, `MRVL`도 같은 테마의 핵심 비교군으로 같이 봐야 한다.

## 2. HBM/DRAM Shortage: Memory Is The Constraint

### Global Industry Flow

S&P Global/Visible Alpha는 Samsung, SK hynix, Micron이 HBM 쪽으로 생산능력을 돌리면서 전통 DRAM 공급이 타이트해지고 가격이 오른다고 분석했다. 이 자료는 2026년 전통 DRAM ASP가 Samsung +116%, SK hynix +78%, Micron +54% 상승할 것으로 보는 컨센서스를 소개했다. WSTS도 2026년 메모리 시장이 2,948억 달러, 전년 대비 39.4% 성장할 것으로 전망했다. ([S&P Global](https://www.spglobal.com/market-intelligence/en/news-insights/research/2026/01/ai-memory-boom-squeezes-legacy-dram-supply-pushing-prices-higher), [WSTS](https://www.wsts.org/esraCMS/extension/media/f/WST/7310/WSTS_FC-Release-2025_11.pdf))

### Global Equity Watchlist

| Exposure | Stocks |
|---|---|
| Pure memory cycle | Micron (`MU`), SK hynix (`000660.KS`) |
| Diversified memory + devices/foundry | Samsung Electronics (`005930.KS`) |
| HBM demand driver | Nvidia (`NVDA`), AMD (`AMD`), Broadcom (`AVGO`) |
| Capacity enablers | ASML (`ASML`), Lam Research (`LRCX`), Applied Materials (`AMAT`) |

### Strategic Interpretation

이 테마는 한국 주식만의 문제가 아니다. `SK하이닉스 vs Micron vs Samsung`의 상대 강도를 봐야 한다. 특히 Micron은 미국 상장 메모리 pure play에 가까워 글로벌 투자자들이 HBM/DRAM shortage를 표현하는 대표 수단이 될 수 있다.

## 3. Data Center Power, Cooling, And Grid

### Global Industry Flow

AI 데이터센터는 GPU뿐 아니라 전력, 냉각, UPS, 변압기, 전력망 연결을 병목으로 만든다. Gartner는 데이터센터 시스템 지출을 강하게 상향했고, Vertiv의 2026년 전망 자료도 AI 인프라에 맞춘 전력 체인, 전기 장비, 액체 냉각, ESS/UPS 수요를 주요 테마로 다룬다. ([Gartner IT Spending](https://www.gartner.com/en/newsroom/press-releases/2026-04-22-gartner-forecasts-worldwide-it-spending-to-grow-13-point-5-percent-in-2026-totaling-6-point-31-trillion-dollars), [Vertiv Frontiers 2026](https://www.vertiv.com/48d902/globalassets/content---assets-2025/documents/vertiv-frontiers-2026-report-en-gl-web.pdf))

### Global Equity Watchlist

| Layer | Global stocks to track | Notes |
|---|---|---|
| Data center power/cooling pure play | Vertiv (`VRT`) | Direct exposure to critical power and thermal infrastructure. |
| Electrical equipment | Eaton (`ETN`), Schneider Electric (`SU.PA` / `SBGSY`), ABB (`ABB`) | Power distribution, electrical systems, automation. |
| Cooling/HVAC components | Modine (`MOD`), nVent (`NVT`), Comfort Systems (`FIX`) | More specific but higher idiosyncratic risk. |
| Data center landlords/operators | Equinix (`EQIX`), Digital Realty (`DLR`) | Benefit from demand, but power availability and capex intensity matter. |
| Energy supply | Brookfield Renewable (`BEP`/`BEPC`), Constellation Energy (`CEG`) | Power availability becomes a strategic input for AI data centers. |

### Korea Link

국내에서는 `HD현대일렉트릭`, `LS ELECTRIC`, `효성중공업`, `LS`, `대한전선` 같은 전력기기/전선 후보군을 추적해야 한다. 하지만 이들은 아직 본 파이프라인에서 충분히 수집하지 않았다. 다음 수집에서는 `data center transformer`, `AI power grid`, `liquid cooling`, `UPS`, `substation` 글로벌 쿼리와 국내 전력기기 쿼리를 함께 돌려야 한다.

## 4. EV, Hybrid, Battery, And ESS

### Global Industry Flow

자동차 전동화는 EV 단일 성장보다 하이브리드와 ESS를 같이 보는 국면이다. 현대차·기아는 2026년 1분기 미국에서 역대 최고 판매를 기록했지만, EV 판매는 전년 대비 21.6% 감소했고 하이브리드 판매는 53.2% 증가했다. 반면 CnEVPost/SNE Research에 따르면 2026년 1-2월 글로벌 EV 배터리 점유율은 CATL 42.1%, BYD 13.4%, LG Energy Solution 8.7%였고, 한국 3사 점유율은 압박을 받았다. S&P Global은 ESS가 리튬 수요에서 가장 빠르게 성장하는 축이 될 수 있다고 봤다. ([Korea JoongAng Daily](https://koreajoongangdaily.joins.com/news/2026-04-02/business/industry/Hyundai-Motor-Kia-log-record-Q1-sales-in-US-on-surging-hybrid-demand/2560006), [CnEVPost/SNE](https://cnevpost.com/2026/04/07/global-ev-battery-market-share-jan-feb-2026/), [S&P Global Lithium](https://www.spglobal.com/energy/en/news-research/latest-news/metals/010826-battery-storage-to-drive-lithium-demand-growth-globally))

### Global Equity Watchlist

| Theme | Global stocks to track | Why |
|---|---|---|
| Hybrid winner | Toyota (`TM`), Hyundai Motor (`005380.KS` / `HYMTF`), Kia (`000270.KS`) | Hybrid demand is stronger than pure EV in the current data. |
| EV scale leaders | BYD (`1211.HK` / `BYDDY`), Tesla (`TSLA`) | Useful for EV demand and pricing pressure read-through. |
| Battery leaders | CATL (`300750.SZ`), LG Energy Solution (`373220.KS`), Samsung SDI (`006400.KS`), Panasonic (`6752.T`) | Global battery share and customer exposure matter. |
| Lithium/materials | Albemarle (`ALB`), SQM (`SQM`), POSCO Holdings (`005490.KS`), Umicore (`UMI.BR`) | Sensitive to lithium price and material cycle. |
| ESS/inverters | Tesla (`TSLA`), Fluence (`FLNC`), Sungrow (`300274.SZ`) | ESS can offset weaker EV battery demand. |

### Strategic Interpretation

하이브리드 강세는 완성차에는 긍정이지만, 배터리 셀/소재에는 반드시 긍정은 아니다. 글로벌 주식으로 보면 `Toyota`, `Hyundai/Kia`는 방어적 전동화 믹스, `CATL/BYD`는 중국 EV/배터리 지배력, `LGES/Samsung SDI`는 미국/레거시 OEM 둔화 리스크를 함께 봐야 한다.

## 5. Platform AI And Commerce

### Global Industry Flow

AI가 비용인지, 매출 성장 엔진인지 구분해야 한다. NAVER는 2026년 1분기 매출 3.2411조 원, 영업이익 5,418억 원을 기록했고, AI 통합이 광고와 커머스 성장에 기여한 것으로 보도됐다. 글로벌에서는 Alphabet, Meta, Amazon, MercadoLibre, Sea, Shopify 같은 플랫폼 기업을 광고/커머스/클라우드/결제 관점에서 비교해야 한다. ([Seoul Economic Daily - Naver](https://en.sedaily.com/news/2026/04/30/naver-q1-operating-profit-rises-72-percent-to-5418-billion))

### Global Equity Watchlist

| Business model | Global stocks |
|---|---|
| Search/AI ads/cloud | Alphabet (`GOOGL`) |
| Social ads/AI engagement | Meta (`META`) |
| Commerce/cloud | Amazon (`AMZN`) |
| Commerce payments ecosystem | MercadoLibre (`MELI`), Sea (`SE`), Shopify (`SHOP`) |
| Korea platform AI/commerce | NAVER (`035420.KS`), Kakao (`035720.KS`) |

### Strategic Interpretation

플랫폼 AI는 `AI capex`보다 `AI monetization`을 봐야 한다. NAVER의 경우 `AI 광고`, `Npay 거래액`, `커머스 서비스 매출`, `C2C`, `클라우드/엔터프라이즈 AI`를 따로 추적해야 한다.

## Global Theme Ranking

| Rank | Global theme | Confidence | Global stocks to track | Korea stocks to track |
|---:|---|---|---|---|
| 1 | AI memory/HBM shortage | High | `MU`, `NVDA`, `TSM`, `ASML`, `AVGO` | `000660.KS`, `005930.KS` |
| 2 | Data center power/cooling/grid | Medium-high | `VRT`, `ETN`, `SU.PA`, `ABB`, `EQIX`, `CEG` | HD현대일렉트릭, LS ELECTRIC, 효성중공업, LS |
| 3 | AI custom silicon/networking | Medium-high | `AVGO`, `MRVL`, `NVDA`, `AMD`, `TSM` | 삼성전자, 소부장/패키징 후보 |
| 4 | Hybrid over pure EV | Medium | `TM`, `TSLA`, `BYD`, `HYMTF` | 현대차, 기아 |
| 5 | Battery/ESS bifurcation | Medium-low | `CATL`, `BYD`, `ALB`, `SQM`, `FLNC` | LG에너지솔루션, 삼성SDI, POSCO홀딩스 |
| 6 | Platform AI monetization | Medium | `GOOGL`, `META`, `AMZN`, `MELI`, `SHOP` | NAVER, 카카오 |

## What The System Must Change

앞으로 Auto-News-Analyst는 국내 뉴스 수집기만으로는 목표를 달성할 수 없다. 필요한 변경:

1. `collect_news.py`에서 기본 소스를 `naver`가 아니라 `naver + google`로 두고, 영어 글로벌 쿼리를 별도로 생성한다.
2. `industry_themes.json`을 만들어 산업별 글로벌 키워드와 관련 주식 universe를 관리한다.
3. `company_aliases.json`은 국내명/영문명/ticker/사업부 키워드를 모두 포함해야 한다.
4. `reports` 출력은 두 개로 분리한다.
   - `daily_local_news_report`: 국내 뉴스 플로우
   - `global_equity_theme_map`: 글로벌 산업 흐름과 전세계 관련 주식
5. 평가도 종목별 hit rate뿐 아니라 theme basket 상대수익률을 봐야 한다.

## Source List

- Gartner, [Worldwide Semiconductor Revenue to Exceed $1.3 Trillion in 2026](https://www.gartner.com/en/newsroom/press-releases/2026-04-08-gartner-forecasts-worldwide-semiconductor-revenue-to-exceed-us-dollars-one-point-3-trillion-in-2026)
- Gartner, [Worldwide IT Spending to Grow 13.5% in 2026](https://www.gartner.com/en/newsroom/press-releases/2026-04-22-gartner-forecasts-worldwide-it-spending-to-grow-13-point-5-percent-in-2026-totaling-6-point-31-trillion-dollars)
- WSTS, [Autumn 2025 Semiconductor Forecast](https://www.wsts.org/esraCMS/extension/media/f/WST/7310/WSTS_FC-Release-2025_11.pdf)
- S&P Global, [AI Memory Boom Squeezes Legacy DRAM Supply](https://www.spglobal.com/market-intelligence/en/news-insights/research/2026/01/ai-memory-boom-squeezes-legacy-dram-supply-pushing-prices-higher)
- Tom's Hardware, [Hyperscaler CAPEX Plans Reach $725B](https://www.tomshardware.com/tech-industry/big-tech/big-techs-ai-spending-plans-reach-725-billion)
- Vertiv, [Frontiers 2026 Report](https://www.vertiv.com/48d902/globalassets/content---assets-2025/documents/vertiv-frontiers-2026-report-en-gl-web.pdf)
- Korea JoongAng Daily, [Hyundai Motor, Kia Record Q1 US Sales](https://koreajoongangdaily.joins.com/news/2026-04-02/business/industry/Hyundai-Motor-Kia-log-record-Q1-sales-in-US-on-surging-hybrid-demand/2560006)
- CnEVPost/SNE Research, [Global EV Battery Market Share Jan-Feb 2026](https://cnevpost.com/2026/04/07/global-ev-battery-market-share-jan-feb-2026/)
- S&P Global, [Battery Storage to Drive Lithium Demand Growth](https://www.spglobal.com/energy/en/news-research/latest-news/metals/010826-battery-storage-to-drive-lithium-demand-growth-globally)
- Seoul Economic Daily, [Naver Q1 Operating Profit Rises 7.2%](https://en.sedaily.com/news/2026/04/30/naver-q1-operating-profit-rises-72-percent-to-5418-billion)

