import pytest

from app.services.debt_engine import Thresholds, build_learning_path, calculate_mastery, classify_mastery, detect_learning_debt
from app.services.graph_utils import compute_depths, would_create_cycle

T = Thresholds()
NAMES = {1: "Variables", 2: "Data Types", 3: "Operators", 4: "Conditionals", 5: "Loops", 6: "Functions"}
CHAIN = [(1, 2), (2, 3), (3, 4), (4, 5), (5, 6)]


def test_mastery_percentage_matches_spec_example():
    # Q1 wrong, Q2 wrong, Q3 correct, Q4 wrong -> 25%
    m = calculate_mastery(1, 4, T)
    assert m["mastery_percentage"] == 25.0
    assert m["status"] == "HIGH_DEBT"
    assert m["confidence"] == 1.0


def test_confidence_grows_with_number_of_questions():
    assert calculate_mastery(1, 1, T)["confidence"] == 0.33
    assert calculate_mastery(2, 3, T)["confidence"] == 1.0


@pytest.mark.parametrize("pct,expected", [(0, "HIGH_DEBT"), (39.9, "HIGH_DEBT"), (40, "MODERATE_DEBT"),
                                          (59, "MODERATE_DEBT"), (60, "DEVELOPING"), (79, "DEVELOPING"),
                                          (80, "MASTERED"), (100, "MASTERED")])
def test_thresholds(pct, expected):
    assert classify_mastery(pct, T) == expected


def test_mastery_rejects_bad_input():
    with pytest.raises(ValueError):
        calculate_mastery(0, 0, T)
    with pytest.raises(ValueError):
        calculate_mastery(5, 4, T)


def test_foundational_weakness_is_root_cause_with_affected_concepts():
    mastery = {1: 30, 2: 40, 3: 90, 6: 35}
    debt = detect_learning_debt(NAMES, CHAIN, mastery, T)
    by_name = {d["concept"]: d for d in debt}
    assert set(by_name) == {"Variables", "Data Types", "Functions"}
    v = by_name["Variables"]
    assert v["is_root_cause"] and v["severity"] == "high" and v["mastery"] == 30
    assert v["affected_concepts"] == ["Data Types", "Operators", "Conditionals", "Loops", "Functions"]
    assert by_name["Data Types"]["caused_by"] == ["Variables"]
    assert not by_name["Data Types"]["is_root_cause"]
    assert debt[0]["concept"] == "Variables"  # most urgent first


def test_unassessed_concepts_are_not_treated_as_weak():
    debt = detect_learning_debt(NAMES, CHAIN, {3: 90}, T)
    assert debt == []


def test_moderate_weakness_blocking_many_concepts_is_escalated():
    debt = detect_learning_debt(NAMES, CHAIN, {1: 55}, T)
    assert debt[0]["severity"] == "high"  # blocks 5 concepts >= escalation_dependents
    leaf = detect_learning_debt(NAMES, CHAIN, {6: 55}, T)
    assert leaf[0]["severity"] == "moderate"


def test_learning_path_orders_prerequisites_first():
    names = {1: "Variables", 2: "Loops", 3: "Functions"}
    edges = [(1, 2), (2, 3)]
    path = build_learning_path(names, edges, {3: 30, 2: 40, 1: 35}, T)
    assert [s["concept"] for s in path] == ["Variables", "Loops", "Functions"]
    assert path[0]["reason"].startswith("Foundational")


def test_learning_path_includes_developing_prerequisites_but_not_mastered_ones():
    path = build_learning_path(NAMES, CHAIN, {1: 95, 2: 70, 3: 90, 4: 90, 5: 90, 6: 20}, T)
    assert [s["concept"] for s in path] == ["Data Types", "Functions"]


def test_cycle_detection():
    assert would_create_cycle(6, 1, CHAIN)      # Functions -> Variables closes the loop
    assert would_create_cycle(1, 1, CHAIN)      # self loop
    assert not would_create_cycle(1, 3, CHAIN)  # shortcut edge is fine (no cycle)
    assert not would_create_cycle(1, 6, CHAIN)


def test_depths():
    assert compute_depths(NAMES.keys(), CHAIN) == {1: 0, 2: 1, 3: 2, 4: 3, 5: 4, 6: 5}
