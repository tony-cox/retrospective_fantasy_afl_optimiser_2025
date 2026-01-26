from __future__ import annotations

from retro_fantasy.data import ModelInputData, Player, PlayerRoundInfo, Position, Round, TeamStructureRules


def test_model_input_data_player_ids_sorted() -> None:
    rules = TeamStructureRules(
        on_field_required={p: 0 for p in Position.__members__.values()},
        bench_required={p: 0 for p in Position.__members__.values()},
        salary_cap=10.0,
        utility_bench_count=1,
    )
    rounds = {2: Round(number=2, max_trades=2, counted_onfield_players=22), 1: Round(number=1, max_trades=0, counted_onfield_players=22)}

    p2 = Player(player_id=2, first_name="B", last_name="Y")
    p2.by_round[1] = PlayerRoundInfo(round_number=1, score=1.0, price=2.0, eligible_positions=frozenset({Position.DEF}))

    p1 = Player(player_id=1, first_name="A", last_name="X")
    p1.by_round[1] = PlayerRoundInfo(round_number=1, score=3.0, price=4.0, eligible_positions=frozenset({Position.MID}))

    data = ModelInputData(players={2: p2, 1: p1}, rounds=rounds, team_rules=rules)
    assert list(data.player_ids) == [1, 2]


def test_model_input_data_round_numbers_sorted_and_excluding_1() -> None:
    rules = TeamStructureRules(
        on_field_required={p: 0 for p in Position.__members__.values()},
        bench_required={p: 0 for p in Position.__members__.values()},
        salary_cap=10.0,
        utility_bench_count=1,
    )
    rounds = {
        3: Round(number=3, max_trades=2, counted_onfield_players=22),
        1: Round(number=1, max_trades=0, counted_onfield_players=22),
        2: Round(number=2, max_trades=2, counted_onfield_players=22),
    }

    p = Player(player_id=1, first_name="A", last_name="X")
    p.by_round[1] = PlayerRoundInfo(round_number=1, score=0.0, price=0.0, eligible_positions=frozenset({Position.DEF}))

    data = ModelInputData(players={1: p}, rounds=rounds, team_rules=rules)

    assert list(data.round_numbers) == [1, 2, 3]
    assert list(data.rounds_excluding_1) == [2, 3]


def test_model_input_data_score_price_and_eligibility_accessors() -> None:
    rules = TeamStructureRules(
        on_field_required={p: 0 for p in Position.__members__.values()},
        bench_required={p: 0 for p in Position.__members__.values()},
        salary_cap=100.0,
        utility_bench_count=1,
    )
    rounds = {1: Round(number=1, max_trades=0, counted_onfield_players=22)}

    player = Player(player_id=1, first_name="A", last_name="B")
    player.by_round[1] = PlayerRoundInfo(
        round_number=1,
        score=55.0,
        price=123.0,
        eligible_positions=frozenset({Position.DEF, Position.MID}),
    )

    data = ModelInputData(players={1: player}, rounds=rounds, team_rules=rules)

    assert data.score(1, 1) == 55.0
    assert data.price(1, 1) == 123.0
    assert data.eligible_positions(1, 1) == frozenset({Position.DEF, Position.MID})
    assert data.is_eligible(1, Position.DEF, 1) is True
    assert data.is_eligible(1, Position.RUC, 1) is False


def test_model_input_data_team_rule_accessors() -> None:
    rules = TeamStructureRules(
        on_field_required={Position.DEF: 6, Position.MID: 8, Position.RUC: 2, Position.FWD: 6},
        bench_required={Position.DEF: 2, Position.MID: 2, Position.RUC: 1, Position.FWD: 2},
        salary_cap=17.5,
        utility_bench_count=1,
    )
    rounds = {1: Round(number=1, max_trades=0, counted_onfield_players=22), 2: Round(number=2, max_trades=2, counted_onfield_players=18)}

    player = Player(player_id=1, first_name="A", last_name="B")
    player.by_round[1] = PlayerRoundInfo(round_number=1, score=0.0, price=0.0, eligible_positions=frozenset({Position.DEF}))
    player.by_round[2] = PlayerRoundInfo(round_number=2, score=0.0, price=0.0, eligible_positions=frozenset({Position.DEF}))

    data = ModelInputData(players={1: player}, rounds=rounds, team_rules=rules)

    assert data.salary_cap == 17.5
    assert data.utility_bench_count == 1
    assert data.on_field_required(Position.DEF) == 6
    assert data.bench_required(Position.RUC) == 1
    assert data.max_trades(2) == 2
    assert data.counted_onfield_players(2) == 18


def test_model_input_data_idx_player_round_generation() -> None:
    rules = TeamStructureRules(
        on_field_required={p: 0 for p in Position.__members__.values()},
        bench_required={p: 0 for p in Position.__members__.values()},
        salary_cap=0.0,
        utility_bench_count=0,
    )
    rounds = {1: Round(number=1, max_trades=0, counted_onfield_players=22), 2: Round(number=2, max_trades=2, counted_onfield_players=22)}

    p1 = Player(player_id=1, first_name="A", last_name="B")
    p1.by_round[1] = PlayerRoundInfo(round_number=1, score=0.0, price=0.0, eligible_positions=frozenset({Position.DEF}))
    p1.by_round[2] = PlayerRoundInfo(round_number=2, score=0.0, price=0.0, eligible_positions=frozenset({Position.DEF}))

    p2 = Player(player_id=2, first_name="C", last_name="D")
    p2.by_round[1] = PlayerRoundInfo(round_number=1, score=0.0, price=0.0, eligible_positions=frozenset({Position.DEF}))
    p2.by_round[2] = PlayerRoundInfo(round_number=2, score=0.0, price=0.0, eligible_positions=frozenset({Position.DEF}))

    data = ModelInputData(players={1: p1, 2: p2}, rounds=rounds, team_rules=rules)

    assert data.idx_player_round == ((1, 1), (1, 2), (2, 1), (2, 2))
    assert data.idx_player_round_excluding_1 == ((1, 2), (2, 2))


def test_model_input_data_idx_player_position_round_includes_all_positions() -> None:
    rules = TeamStructureRules(
        on_field_required={p: 0 for p in Position.__members__.values()},
        bench_required={p: 0 for p in Position.__members__.values()},
        salary_cap=0.0,
        utility_bench_count=0,
    )
    rounds = {1: Round(number=1, max_trades=0, counted_onfield_players=22)}

    p = Player(player_id=1, first_name="A", last_name="B")
    p.by_round[1] = PlayerRoundInfo(round_number=1, score=0.0, price=0.0, eligible_positions=frozenset({Position.DEF}))

    data = ModelInputData(players={1: p}, rounds=rounds, team_rules=rules)

    expected = tuple((1, pos, 1) for pos in Position.__members__.values())
    assert data.idx_player_position_round == expected


def test_model_input_data_idx_round_and_excluding_1() -> None:
    rules = TeamStructureRules(
        on_field_required={p: 0 for p in Position.__members__.values()},
        bench_required={p: 0 for p in Position.__members__.values()},
        salary_cap=0.0,
        utility_bench_count=0,
    )
    rounds = {2: Round(number=2, max_trades=2, counted_onfield_players=22), 1: Round(number=1, max_trades=0, counted_onfield_players=22)}

    p = Player(player_id=1, first_name="A", last_name="B")
    p.by_round[1] = PlayerRoundInfo(round_number=1, score=0.0, price=0.0, eligible_positions=frozenset({Position.DEF}))
    p.by_round[2] = PlayerRoundInfo(round_number=2, score=0.0, price=0.0, eligible_positions=frozenset({Position.DEF}))

    data = ModelInputData(players={1: p}, rounds=rounds, team_rules=rules)

    assert list(data.idx_round) == [1, 2]
    assert list(data.idx_round_excluding_1) == [2]


def test_model_input_data_eligibility_map_contains_expected_keys() -> None:
    rules = TeamStructureRules(
        on_field_required={p: 0 for p in Position.__members__.values()},
        bench_required={p: 0 for p in Position.__members__.values()},
        salary_cap=0.0,
        utility_bench_count=0,
    )
    rounds = {1: Round(number=1, max_trades=0, counted_onfield_players=22)}

    p = Player(player_id=1, first_name="A", last_name="B")
    p.by_round[1] = PlayerRoundInfo(
        round_number=1,
        score=0.0,
        price=0.0,
        eligible_positions=frozenset({Position.DEF}),
    )

    data = ModelInputData(players={1: p}, rounds=rounds, team_rules=rules)

    emap = data.eligibility_map

    assert emap[(1, Position.DEF, 1)] is True
    assert emap[(1, Position.MID, 1)] is False


def test_model_input_data_squad_size_helpers() -> None:
    rules = TeamStructureRules(
        on_field_required={Position.DEF: 6, Position.MID: 8, Position.RUC: 2, Position.FWD: 6},
        bench_required={Position.DEF: 2, Position.MID: 2, Position.RUC: 1, Position.FWD: 2},
        salary_cap=0.0,
        utility_bench_count=1,
    )
    rounds = {1: Round(number=1, max_trades=0, counted_onfield_players=22)}

    p = Player(player_id=1, first_name="A", last_name="B")
    p.by_round[1] = PlayerRoundInfo(round_number=1, score=0.0, price=0.0, eligible_positions=frozenset({Position.DEF}))

    data = ModelInputData(players={1: p}, rounds=rounds, team_rules=rules)

    assert data.on_field_size == 22
    assert data.bench_size == 8
    assert data.squad_size == 30


def test_model_input_data_score_and_price_missing_round_returns_defaults() -> None:
    rules = TeamStructureRules(
        on_field_required={p: 0 for p in Position.__members__.values()},
        bench_required={p: 0 for p in Position.__members__.values()},
        salary_cap=999.0,
        utility_bench_count=0,
    )
    rounds = {1: Round(number=1, max_trades=0, counted_onfield_players=22), 2: Round(number=2, max_trades=0, counted_onfield_players=22)}

    player = Player(player_id=1, first_name="A", last_name="B", original_positions=frozenset({Position.DEF}))
    player.by_round[1] = PlayerRoundInfo(
        round_number=1,
        score=10.0,
        price=123.0,
        eligible_positions=frozenset({Position.DEF}),
    )

    data = ModelInputData(players={1: player}, rounds=rounds, team_rules=rules)

    # Round 2 is missing from player.by_round -> defaults
    assert data.score(1, 2) == 0.0
    assert data.price(1, 2) == 999.0
    assert data.eligible_positions(1, 2) == frozenset({Position.DEF})
