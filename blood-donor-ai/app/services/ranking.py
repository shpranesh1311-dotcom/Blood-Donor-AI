"""
ranking.py
==========
Intelligent donor ranking module.

WHY A WEIGHTED, CONFIGURABLE SCORE (AND NOT JUST THE RAW ML PROBABILITY)?
--------------------------------------------------------------------------
The ML model only predicts P(donor responds). That is one useful signal,
but a hospital coordinator also cares about:
  - how far away the donor is (closer donors can help faster),
  - how the donor has behaved historically (consistency matters, not
    just a single probability estimate which can be noisy for donors
    with very little history),
  - whether the donor is currently marked available right now,
  - how quickly the donor tends to respond once they say yes,
  - and how urgent the request is (for critical requests we may want to
    weight "speed" factors more heavily than for routine requests).

Rather than hard-coding arbitrary numbers deep in the code, all weights
live in ranking_config.json so a project supervisor / demo user can
retune the system without touching Python code. Weights are documented
below and are expected to sum to 1.0 (they are re-normalised defensively
if they do not, so the system never silently breaks).

The final "overall_score" is scaled to 0-100 for easy display.
"""

import json
import os
from dataclasses import dataclass, field
from typing import Optional

_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ranking_config.json")

URGENCY_ORDER = {"Critical": 3, "High": 2, "Medium": 1, "Low": 0}


def load_ranking_config() -> dict:
    with open(_CONFIG_PATH, "r") as f:
        return json.load(f)


@dataclass
class RankingInput:
    donor_id: str
    ml_response_probability: float          # 0.0 - 1.0, from the trained model
    distance_km: float
    previous_response_rate: float           # 0.0 - 1.0 (responded / received)
    current_availability: bool
    average_response_time_minutes: float
    urgency_level: str = "Medium"
    extra: dict = field(default_factory=dict)


@dataclass
class RankingResult:
    donor_id: str
    overall_score: float          # 0-100
    sub_scores: dict              # each factor's normalised 0-1 contribution
    expected_response_label: str  # "High" / "Medium" / "Low" speed expectation


def _normalise_weights(weights: dict) -> dict:
    total = sum(weights.values())
    if total <= 0:
        n = len(weights)
        return {k: 1.0 / n for k in weights}
    return {k: v / total for k, v in weights.items()}


def _distance_score(distance_km: float, max_distance_km: float) -> float:
    """Closer donors score higher. Linear falloff, clipped to [0, 1]."""
    if distance_km <= 0:
        return 1.0
    score = 1.0 - (distance_km / max_distance_km)
    return max(0.0, min(1.0, score))


def _response_time_score(avg_minutes: float) -> float:
    """Faster historical response time scores higher. 10 min -> ~1.0, 180+ min -> ~0."""
    score = 1.0 - (avg_minutes / 180.0)
    return max(0.0, min(1.0, score))


def _urgency_alignment_score(urgency_level: str, avg_minutes: float) -> float:
    """
    For Critical/High urgency requests, reward donors with historically fast
    response times more strongly. For Low urgency, this factor matters less.
    """
    speed_score = _response_time_score(avg_minutes)
    urgency_weight = URGENCY_ORDER.get(urgency_level, 1) / 3.0
    # blend: at Low urgency this factor is nearly neutral (0.5), at Critical
    # it fully reflects the donor's speed score.
    return (0.5 * (1 - urgency_weight)) + (speed_score * urgency_weight)


def expected_response_label(avg_minutes: float) -> str:
    if avg_minutes <= 30:
        return "High"
    if avg_minutes <= 75:
        return "Medium"
    return "Low"


def compute_rank_score(item: RankingInput, config: Optional[dict] = None) -> RankingResult:
    cfg = config or load_ranking_config()
    weights = _normalise_weights(cfg["weights"])
    max_distance = cfg.get("max_distance_km_for_scoring", 30)

    sub_scores = {
        "ml_response_probability": max(0.0, min(1.0, item.ml_response_probability)),
        "distance": _distance_score(item.distance_km, max_distance),
        "previous_response_rate": max(0.0, min(1.0, item.previous_response_rate)),
        "current_availability": 1.0 if item.current_availability else 0.0,
        "expected_response_time": _response_time_score(item.average_response_time_minutes),
        "urgency_alignment": _urgency_alignment_score(item.urgency_level, item.average_response_time_minutes),
    }

    overall = sum(sub_scores[k] * weights[k] for k in weights) * 100.0

    return RankingResult(
        donor_id=item.donor_id,
        overall_score=round(overall, 1),
        sub_scores={k: round(v, 3) for k, v in sub_scores.items()},
        expected_response_label=expected_response_label(item.average_response_time_minutes),
    )


def rank_donors(items: list, config: Optional[dict] = None) -> list:
    """
    Rank a list of RankingInput objects, returning RankingResult objects
    sorted by overall_score (descending).
    """
    cfg = config or load_ranking_config()
    results = [compute_rank_score(item, cfg) for item in items]
    results.sort(key=lambda r: r.overall_score, reverse=True)
    return results
