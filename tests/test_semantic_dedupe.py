from semantic_dedupe import choose_duplicate


def test_highest_scoring_order_update_is_duplicate():
    decision = choose_duplicate([
        {"score": 0.95, "metadata": {"order_id": "ord-7"}},
        {"score": 0.61, "metadata": {"order_id": "ord-3"}},
    ])
    assert decision.duplicate is True
    assert decision.matched_order_id == "ord-7"


def test_low_score_update_is_new():
    decision = choose_duplicate([{"score": 0.71, "metadata": {"order_id": "ord-7"}}])
    assert decision.duplicate is False
    assert decision.matched_order_id is None
