from __future__ import annotations

import math

import pytest

from player_price_generator.data import PricingConfig
from player_price_generator.pricing import _compute_price_for_round, _weights_for_previous_games, generate_round_prices


def test_weights_for_previous_games_one() -> None:
    alpha, weights = _weights_for_previous_games(1)
    assert alpha == 55
    assert weights == [5]


def test_weights_for_previous_games_two() -> None:
    alpha, weights = _weights_for_previous_games(2)
    assert alpha == 51
    assert weights == [5, 4]


def test_weights_for_previous_games_five_or_more_caps_at_five() -> None:
    alpha5, weights5 = _weights_for_previous_games(5)
    alpha6, weights6 = _weights_for_previous_games(6)
    assert alpha5 == 45
    assert weights5 == [5, 4, 3, 2, 1]
    assert alpha6 == 45
    assert weights6 == [5, 4, 3, 2, 1]


def test_compute_price_for_round_matches_formula_example_round2() -> None:
    price1 = 100.0
    score1 = 60.0
    magic = 1000.0

    # round2 = 55/60 * price1 + magic * (5/60 * score1)
    expected = (55 / 60.0) * price1 + magic * ((5 / 60.0) * score1)
    actual = _compute_price_for_round(
        price_prev=price1,
        previous_game_scores_most_recent_first=[score1],
        magic_number=magic,
    )
    assert math.isclose(actual, expected, rel_tol=0, abs_tol=1e-9)


def test_generate_round_prices_skips_non_playing_rounds_in_score_window() -> None:
    # Player plays r1 and r3; does not play r2.
    starting_prices = {"P": 100.0}
    simulated_scores = {"P": {1: 10.0, 3: 30.0}}
    config = PricingConfig(salary_cap=0.0, magic_number=1.0)

    prices = generate_round_prices(
        starting_prices_round_1=starting_prices,
        simulated_scores=simulated_scores,
        max_round=4,
        config=config,
    )

    # r2 uses only score(1)
    expected_r2 = (55 / 60.0) * 100.0 + (5 / 60.0) * 10.0
    assert math.isclose(prices["P"][2], expected_r2, rel_tol=0, abs_tol=1e-9)

    # r3 also uses only score(1) because score(2) doesn't exist (player didn't play).
    expected_r3 = (55 / 60.0) * prices["P"][2] + (5 / 60.0) * 10.0
    assert math.isclose(prices["P"][3], expected_r3, rel_tol=0, abs_tol=1e-9)

    # After r3 price computed, r3 score is added. r4 should now use scores [30, 10]
    expected_r4 = (51 / 60.0) * prices["P"][3] + ((5 / 60.0) * 30.0 + (4 / 60.0) * 10.0)
    assert math.isclose(prices["P"][4], expected_r4, rel_tol=0, abs_tol=1e-9)


def test_generate_round_prices_raises_if_missing_starting_price() -> None:
    config = PricingConfig(salary_cap=0.0, magic_number=1.0)
    with pytest.raises(KeyError, match="Missing starting round-1 price"):
        generate_round_prices(starting_prices_round_1={}, simulated_scores={"P": {1: 1.0}}, max_round=2, config=config)


def test_generate_round_prices_round2_includes_round0_when_present() -> None:
    # Player played opening round (0) and round 1.
    starting_prices = {"P": 100.0}
    simulated_scores = {"P": {0: 20.0, 1: 10.0}}
    config = PricingConfig(salary_cap=0.0, magic_number=1.0)

    prices = generate_round_prices(
        starting_prices_round_1=starting_prices,
        simulated_scores=simulated_scores,
        max_round=2,
        config=config,
    )

    # With a round-0 score present, there is a hidden round-1 update that becomes the
    # base for round-2 pricing.
    hidden_r1 = (55 / 60.0) * 100.0 + ((5 / 60.0) * 20.0)

    # Round 2 uses scores (r1 and r0) with weights [5,4] and alpha=51.
    expected_r2 = (51 / 60.0) * hidden_r1 + ((5 / 60.0) * 10.0 + (4 / 60.0) * 20.0)
    assert math.isclose(prices["P"][2], expected_r2, rel_tol=0, abs_tol=1e-9)


def test_generate_round_prices_round3_uses_three_previous_games_when_round0_present() -> None:
    # Player played opening round (0), round 1, and round 2.
    starting_prices = {"P": 100.0}
    simulated_scores = {"P": {0: 20.0, 1: 10.0, 2: 30.0}}
    config = PricingConfig(salary_cap=0.0, magic_number=1.0)

    prices = generate_round_prices(
        starting_prices_round_1=starting_prices,
        simulated_scores=simulated_scores,
        max_round=3,
        config=config,
    )

    hidden_r1 = (55 / 60.0) * 100.0 + ((5 / 60.0) * 20.0)

    # Round 2 includes r1 and r0, with alpha=51 and weights [5,4], but uses hidden_r1.
    expected_r2 = (51 / 60.0) * hidden_r1 + ((5 / 60.0) * 10.0 + (4 / 60.0) * 20.0)
    assert math.isclose(prices["P"][2], expected_r2, rel_tol=0, abs_tol=1e-9)

    # Round 3 should use three previous games: r2, r1, r0 with weights [5,4,3] and alpha=48.
    expected_r3 = (48 / 60.0) * expected_r2 + ((5 / 60.0) * 30.0 + (4 / 60.0) * 10.0 + (3 / 60.0) * 20.0)
    assert math.isclose(prices["P"][3], expected_r3, rel_tol=0, abs_tol=1e-9)


def test_generate_round_prices_round3_uses_two_previous_games_when_no_round0() -> None:
    # No opening round score; player played r1 and r2.
    starting_prices = {"P": 100.0}
    simulated_scores = {"P": {1: 10.0, 2: 30.0}}
    config = PricingConfig(salary_cap=0.0, magic_number=1.0)

    prices = generate_round_prices(
        starting_prices_round_1=starting_prices,
        simulated_scores=simulated_scores,
        max_round=3,
        config=config,
    )

    # Round 2 uses only r1 (alpha=55, weights [5])
    expected_r2 = (55 / 60.0) * 100.0 + ((5 / 60.0) * 10.0)
    assert math.isclose(prices["P"][2], expected_r2, rel_tol=0, abs_tol=1e-9)

    # Round 3 uses r2 and r1 (alpha=51, weights [5,4])
    expected_r3 = (51 / 60.0) * expected_r2 + ((5 / 60.0) * 30.0 + (4 / 60.0) * 10.0)
    assert math.isclose(prices["P"][3], expected_r3, rel_tol=0, abs_tol=1e-9)


def test_generate_round_prices_manual_check_round2_exact() -> None:
    starting_prices = {"P": 535_602.0}
    simulated_scores = {"P": {1: 118.0}}
    config = PricingConfig(salary_cap=0.0, magic_number=10_502.0)

    prices = generate_round_prices(
        starting_prices_round_1=starting_prices,
        simulated_scores=simulated_scores,
        max_round=2,
        config=config,
    )

    expected_r2 = (55 / 60.0) * 535_602.0 + 10_502.0 * ((5 / 60.0) * 118.0)
    assert math.isclose(prices["P"][2], expected_r2, rel_tol=0, abs_tol=1e-9)
    assert prices["P"][2] == pytest.approx(594_238.0, abs=1.0)


def test_generate_round_prices_opening_round_score_in_round0_round2_price() -> None:
    # Edge case:
    # - rd0 price is same as rd1 starting price (there is no "official" price update)
    # - BUT there is a hidden price update that would have occurred for rd1 due to rd0 score
    # - rd2 pricing uses that hidden rd1 price as the base
    # - player scored 118 in rd0 and 47 in rd1
    # Expected rd2 price: 628851

    starting_prices = {"P": 535_602.0}
    simulated_scores = {"P": {0: 118.0, 1: 47.0}}
    config = PricingConfig(salary_cap=0.0, magic_number=10_502.0)

    prices = generate_round_prices(
        starting_prices_round_1=starting_prices,
        simulated_scores=simulated_scores,
        max_round=2,
        config=config,
    )

    hidden_r1 = (55 / 60.0) * 535_602.0 + 10_502.0 * ((5 / 60.0) * 118.0)

    # Round 2 includes both scores (rd1 and rd0) with weights [5,4] and alpha=51,
    # but uses the hidden updated rd1 price as price_prev.
    expected_r2 = (51 / 60.0) * hidden_r1 + 10_502.0 * ((5 / 60.0) * 47.0 + (4 / 60.0) * 118.0)
    assert math.isclose(prices["P"][2], expected_r2, rel_tol=0, abs_tol=1e-9)
    assert prices["P"][2] == pytest.approx(628_851.0, abs=1.0)


def test_generate_round_prices_round1_price_is_starting_price_even_when_round0_score_exists() -> None:
    starting_prices = {"P": 535_602.0}
    simulated_scores = {"P": {0: 118.0, 1: 47.0}}
    config = PricingConfig(salary_cap=0.0, magic_number=10_502.0)

    prices = generate_round_prices(
        starting_prices_round_1=starting_prices,
        simulated_scores=simulated_scores,
        max_round=2,
        config=config,
    )

    # The published rd1 price must always be the starting price.
    assert prices["P"][1] == 535_602.0

    # And it must not equal the hidden updated rd1 price implied by the rd0 score.
    hidden_r1 = (55 / 60.0) * 535_602.0 + 10_502.0 * ((5 / 60.0) * 118.0)
    assert prices["P"][1] != pytest.approx(hidden_r1)
