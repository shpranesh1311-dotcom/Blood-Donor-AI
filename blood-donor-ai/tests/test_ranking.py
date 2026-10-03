"""Tests for app/services/ranking.py"""

from app.services.ranking import RankingInput, compute_rank_score, rank_donors, expected_response_label


def test_closer_and_more_reliable_donor_ranks_higher():
    strong = RankingInput(
        donor_id="D1", ml_response_probability=0.9, distance_km=1.0,
        previous_response_rate=0.9, current_availability=True,
        average_response_time_minutes=15, urgency_level="Critical",
    )
    weak = RankingInput(
        donor_id="D2", ml_response_probability=0.3, distance_km=25.0,
        previous_response_rate=0.2, current_availability=False,
        average_response_time_minutes=150, urgency_level="Critical",
    )
    ranked = rank_donors([weak, strong])
    assert ranked[0].donor_id == "D1"
    assert ranked[0].overall_score > ranked[1].overall_score


def test_overall_score_is_within_0_100():
    result = compute_rank_score(RankingInput(
        donor_id="D1", ml_response_probability=0.5, distance_km=10,
        previous_response_rate=0.5, current_availability=True,
        average_response_time_minutes=45, urgency_level="Medium",
    ))
    assert 0 <= result.overall_score <= 100


def test_expected_response_label_thresholds():
    assert expected_response_label(10) == "High"
    assert expected_response_label(50) == "Medium"
    assert expected_response_label(200) == "Low"


def test_sub_scores_contain_all_factors():
    result = compute_rank_score(RankingInput(
        donor_id="D1", ml_response_probability=0.7, distance_km=5,
        previous_response_rate=0.6, current_availability=True,
        average_response_time_minutes=30, urgency_level="High",
    ))
    expected_keys = {
        "ml_response_probability", "distance", "previous_response_rate",
        "current_availability", "expected_response_time", "urgency_alignment",
    }
    assert expected_keys == set(result.sub_scores.keys())


def test_rank_donors_sorted_descending():
    items = [
        RankingInput(donor_id=f"D{i}", ml_response_probability=i / 10, distance_km=10,
                     previous_response_rate=0.5, current_availability=True,
                     average_response_time_minutes=40, urgency_level="Medium")
        for i in range(1, 6)
    ]
    ranked = rank_donors(items)
    scores = [r.overall_score for r in ranked]
    assert scores == sorted(scores, reverse=True)
