"""
Editable candidate pipeline.

During autoresearch runs, the agent may modify this file. Keep the public
`CandidateNewsPipeline.analyze()` contract stable so the immutable evaluation
harness can compare experiments fairly.
"""

from __future__ import annotations

from datetime import date

try:
    from .domain_types import InsightPrediction, NewsRecord
except ImportError:  # Allows running from this directory without package install.
    from domain_types import InsightPrediction, NewsRecord


class CandidateNewsPipeline:
    def analyze(self, news: list[NewsRecord], as_of_date: date, prompt: str) -> list[InsightPrediction]:
        """
        Baseline heuristic.

        This is intentionally simple: future iterations should improve evidence
        extraction, scoring, and confidence calibration without changing the
        evaluation harness.
        """
        grouped: dict[str, list[NewsRecord]] = {}
        for item in news:
            grouped.setdefault(item.ticker, []).append(item)

        predictions: list[InsightPrediction] = []
        for ticker, records in grouped.items():
            score = _baseline_score(records)
            predictions.append(
                InsightPrediction(
                    ticker=ticker,
                    as_of_date=as_of_date,
                    score=score,
                    confidence=min(1.0, 0.35 + 0.05 * len(records)),
                    thesis=f"Baseline news polarity score from {len(records)} articles.",
                    evidence=[record.title for record in records[:3]],
                )
            )
        return predictions


def _baseline_score(records: list[NewsRecord]) -> float:
    positive = ("beat", "raise", "growth", "upgrade", "profit", "surge", "record")
    negative = ("miss", "cut", "risk", "downgrade", "loss", "probe", "delay")
    score = 0
    for record in records:
        text = f"{record.title} {record.body}".lower()
        score += sum(1 for word in positive if word in text)
        score -= sum(1 for word in negative if word in text)
    return max(-1.0, min(1.0, score / max(3, len(records))))
