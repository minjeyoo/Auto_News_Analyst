# Auto-News-Analyst Program

## Objective

Improve `composite_score` on rolling stock-news backcasts.

## Editable Arena

You may modify only:
- `candidate_pipeline.py`
- `prompts/candidate_prompt.md`
- `news_keywords.json`
- `industry_themes.json`
- `company_aliases.json`
- `COMBAT_LOG.md`
- `RESEARCH_LOG.md`

Do not modify:
- `eval_harness.py`
- `controller.py`
- `news_cache.py`
- `news_fetchers/`
- `prepare_data.py`
- `price_provider.py`
- `tests/`
- cached news or price data

## Loop Rules

1. Read `COMBAT_LOG.md` before proposing a change.
2. Test exactly one hypothesis per iteration.
3. Do not change the metric, price data, labels, or evaluation window.
4. If the change fails, record why in `COMBAT_LOG.md` before reverting code.
5. Prefer robust signal extraction over narrow ticker-specific rules.

## Current Research Directions

- Separate earnings, guidance, analyst, legal, and macro catalysts.
- Add source reliability weighting.
- Penalize stale repeated syndicated articles.
- Calibrate confidence by evidence count and source diversity.
- Avoid one-sided bullish or bearish output.
- Use `docs/data_source_setup.md` when adding or configuring global data sources.
- Derive next-run keywords from cached reports/news with `derive_keywords.py` before widening collection.
- `build_industry_report.py`로 출처 기반 산업 증거 리포트를 생성해 GDELT, SEC EDGAR, DART, 유료 API 증거가 캐시에 있을 때 최종 리포트에 반영되게 한다.
- 기본 뉴스 수집 소스는 `naver + google`이며, 영어권 글로벌 수집은 `google_global`과 `industry_themes.json`의 `global_queries`로 별도 생성한다.
- 리포트 출력은 국내 뉴스 플로우(`daily_local_news_report`)와 글로벌 산업/주식 맵(`global_equity_theme_map`)으로 분리한다.
