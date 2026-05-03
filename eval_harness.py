"""
Immutable evaluation harness for Auto-News-Analyst.

Agents must not modify this file during autoresearch runs. It owns leakage checks,
price alignment, hit-rate calculation, and the single scalar score used by the
keep/discard gate.
"""

from __future__ import annotations

from datetime import date
from typing import Iterable

from types import SimpleNamespace

try:
    from .domain_types import (
        Direction,
        EvaluationResult,
        InsightPrediction,
        NewsRecord,
        PredictionEvaluation,
        PricePoint,
    )
except ImportError:  # Allows running tests from this directory without package install.
    from domain_types import (
        Direction,
        EvaluationResult,
        InsightPrediction,
        NewsRecord,
        PredictionEvaluation,
        PricePoint,
    )


DEFAULT_METRIC_WEIGHTS = SimpleNamespace(
    hit_rate=0.35,
    alpha_return=0.30,
    virtual_return=0.20,
    coverage=0.10,
    imbalance_penalty=0.05,
)


def assert_no_news_leakage(news: Iterable[NewsRecord], forecast_start: date) -> None:
    leaked = [item for item in news if item.published_at.date() > forecast_start]
    if leaked:
        examples = ", ".join(f"{item.ticker}:{item.published_at.date()}" for item in leaked[:5])
        raise ValueError(f"news leakage detected after forecast date: {examples}")


def evaluate_predictions(
    *,
    predictions: list[InsightPrediction],
    prices_by_ticker: dict[str, list[PricePoint]],
    run_id: str,
    forecast_start: date,
    forecast_end: date,
    min_score_to_trade: float = 0.15,
    flat_return_threshold: float = 0.005,
    transaction_cost: float = 0.001,
    min_evaluated_count: int = 20,
) -> EvaluationResult:
    """
    Score backcast predictions against later realized prices.

    The single gate metric is `composite_score`. It intentionally combines
    direction accuracy, benchmark-relative return, absolute strategy return,
    prediction coverage, and long/short balance so the loop cannot improve by
    simply making fewer trades or becoming one-sided.
    """
    details: list[PredictionEvaluation] = []
    errors: list[str] = []

    for prediction in predictions:
        if prediction.as_of_date > forecast_start:
            errors.append(f"{prediction.ticker}: prediction uses future as_of_date {prediction.as_of_date}")
            continue

        price_points = sorted(
            prices_by_ticker.get(prediction.ticker, []),
            key=lambda point: point.trading_date,
        )
        start_point = _first_point_on_or_after(price_points, forecast_start)
        end_point = _last_point_on_or_before(price_points, forecast_end)
        predicted_direction = _score_to_direction(prediction.score, min_score_to_trade)

        if start_point is None or end_point is None:
            details.append(
                PredictionEvaluation(
                    ticker=prediction.ticker,
                    predicted_direction=predicted_direction,
                    actual_direction=Direction.NEUTRAL,
                    score=prediction.score,
                    confidence=prediction.confidence,
                    start_price=0.0,
                    end_price=0.0,
                    realized_return=0.0,
                    strategy_return=0.0,
                    hit=False,
                    skipped_reason="missing price data",
                )
            )
            continue

        if start_point.close <= 0 or end_point.close <= 0:
            details.append(
                PredictionEvaluation(
                    ticker=prediction.ticker,
                    predicted_direction=predicted_direction,
                    actual_direction=Direction.NEUTRAL,
                    score=prediction.score,
                    confidence=prediction.confidence,
                    start_price=start_point.close,
                    end_price=end_point.close,
                    realized_return=0.0,
                    strategy_return=0.0,
                    hit=False,
                    skipped_reason="invalid non-positive price",
                )
            )
            continue

        realized_return = (end_point.close - start_point.close) / start_point.close
        actual_direction = _return_to_direction(realized_return, flat_return_threshold)
        strategy_return = _strategy_return(predicted_direction, realized_return, transaction_cost)
        hit = (
            predicted_direction != Direction.NEUTRAL
            and actual_direction != Direction.NEUTRAL
            and predicted_direction == actual_direction
        )

        details.append(
            PredictionEvaluation(
                ticker=prediction.ticker,
                predicted_direction=predicted_direction,
                actual_direction=actual_direction,
                score=prediction.score,
                confidence=prediction.confidence,
                start_price=start_point.close,
                end_price=end_point.close,
                realized_return=realized_return,
                strategy_return=strategy_return,
                hit=hit,
            )
        )

    active = [
        item
        for item in details
        if item.skipped_reason is None
        and item.predicted_direction != Direction.NEUTRAL
        and item.actual_direction != Direction.NEUTRAL
    ]
    valid_price_rows = [item for item in details if item.skipped_reason is None]

    evaluated_count = len(active)
    skipped_count = len([item for item in details if item.skipped_reason is not None])
    hit_rate = sum(1 for item in active if item.hit) / evaluated_count if evaluated_count else 0.0
    virtual_return = _mean(item.strategy_return for item in active)
    benchmark_return = _mean(item.realized_return for item in valid_price_rows)
    alpha_return = virtual_return - benchmark_return
    coverage_score = evaluated_count / len(predictions) if predictions else 0.0
    long_count = sum(1 for item in details if item.predicted_direction == Direction.BULLISH)
    short_count = sum(1 for item in details if item.predicted_direction == Direction.BEARISH)
    neutral_count = sum(1 for item in details if item.predicted_direction == Direction.NEUTRAL)
    direction_imbalance = _direction_imbalance(long_count, short_count)
    composite_score = _composite_score(
        hit_rate=hit_rate,
        alpha_return=alpha_return,
        virtual_return=virtual_return,
        coverage_score=coverage_score,
        direction_imbalance=direction_imbalance,
    )

    return EvaluationResult(
        run_id=run_id,
        evaluated_count=evaluated_count,
        skipped_count=skipped_count,
        hit_rate=hit_rate,
        virtual_return=virtual_return,
        benchmark_return=benchmark_return,
        alpha_return=alpha_return,
        coverage_score=coverage_score,
        direction_imbalance=direction_imbalance,
        composite_score=composite_score,
        long_count=long_count,
        short_count=short_count,
        neutral_count=neutral_count,
        min_evaluated_count=min_evaluated_count,
        details=details,
        errors=errors,
    )


def _composite_score(
    *,
    hit_rate: float,
    alpha_return: float,
    virtual_return: float,
    coverage_score: float,
    direction_imbalance: float,
) -> float:
    weights = DEFAULT_METRIC_WEIGHTS
    return (
        weights.hit_rate * hit_rate
        + weights.alpha_return * alpha_return
        + weights.virtual_return * virtual_return
        + weights.coverage * coverage_score
        - weights.imbalance_penalty * direction_imbalance
    )


def _direction_imbalance(long_count: int, short_count: int) -> float:
    active = long_count + short_count
    if active == 0:
        return 0.0
    return abs(long_count - short_count) / active


def _score_to_direction(score: float, threshold: float) -> Direction:
    if score >= threshold:
        return Direction.BULLISH
    if score <= -threshold:
        return Direction.BEARISH
    return Direction.NEUTRAL


def _return_to_direction(value: float, threshold: float) -> Direction:
    if value >= threshold:
        return Direction.BULLISH
    if value <= -threshold:
        return Direction.BEARISH
    return Direction.NEUTRAL


def _strategy_return(direction: Direction, realized_return: float, transaction_cost: float) -> float:
    if direction == Direction.BULLISH:
        return realized_return - transaction_cost
    if direction == Direction.BEARISH:
        return -realized_return - transaction_cost
    return 0.0


def _first_point_on_or_after(points: list[PricePoint], target: date) -> PricePoint | None:
    return next((point for point in points if point.trading_date >= target), None)


def _last_point_on_or_before(points: list[PricePoint], target: date) -> PricePoint | None:
    eligible = [point for point in points if point.trading_date <= target]
    return eligible[-1] if eligible else None


def _mean(values: Iterable[float]) -> float:
    items = list(values)
    return sum(items) / len(items) if items else 0.0
