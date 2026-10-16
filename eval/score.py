"""Scoring and the go/no-go gate. Pure functions, no network."""
from collections import Counter
from eval.schema import Label, Reading, TRENDS

GATE_TREND_ACC = 0.80
GATE_MIN_CHARTS = 50
LEVEL_TOL = 0.01  # a predicted level matches if within 1% of the labeled price


def level_recall(true: list[float], pred: list[float], tol: float = LEVEL_TOL) -> float | None:
    """Fraction of labeled levels that have a prediction within tol (relative)."""
    if not true:
        return None
    hit = sum(any(abs(p - t) <= tol * abs(t) for p in pred) for t in true)
    return hit / len(true)


def score(labels: list[Label], readings: list[Reading]) -> dict:
    assert len(labels) == len(readings)
    n = len(labels)
    correct = sum(r.trend == l.trend for l, r in zip(labels, readings))
    failed = sum(r.trend is None for r in readings)
    confusion = Counter((l.trend, r.trend or "ERROR") for l, r in zip(labels, readings))
    recalls = [x for l, r in zip(labels, readings)
               if (x := level_recall(l.levels, r.levels)) is not None]
    trend_acc = correct / n if n else 0.0
    return {
        "n": n,
        "failed_calls": failed,
        "trend_accuracy": round(trend_acc, 4),
        "level_recall": round(sum(recalls) / len(recalls), 4) if recalls else None,
        "confusion": {f"{t}->{p}": c for (t, p), c in sorted(confusion.items())},
        "gate": {
            "passed": n >= GATE_MIN_CHARTS and trend_acc >= GATE_TREND_ACC,
            "needs": f">= {GATE_MIN_CHARTS} charts and trend accuracy >= {GATE_TREND_ACC:.0%}",
            "enough_charts": n >= GATE_MIN_CHARTS,
        },
    }
