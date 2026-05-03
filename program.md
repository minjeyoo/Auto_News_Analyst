# Auto-News-Analyst Program

## Objective

Improve `composite_score` on rolling stock-news backcasts.

## Editable Arena

You may modify only:
- `candidate_pipeline.py`
- `prompts/candidate_prompt.md`
- `news_keywords.json`
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
