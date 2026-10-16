from eval.providers import parse_reading
from eval.schema import Label, Reading
from eval.score import level_recall, score


def test_level_recall_tolerance():
    assert level_recall([100.0, 200.0], [100.5, 250.0]) == 0.5
    assert level_recall([], [1.0]) is None


def test_gate_needs_enough_charts_and_accuracy():
    labels = [Label(f"{i}.png", "UP") for i in range(50)]
    ok = [Reading("UP")] * 40 + [Reading("DOWN")] * 10
    assert score(labels, ok)["gate"]["passed"]
    bad = [Reading("UP")] * 39 + [Reading(None, error="x")] * 11
    r = score(labels, bad)
    assert not r["gate"]["passed"] and r["failed_calls"] == 11
    assert not score(labels[:10], ok[:10])["gate"]["passed"]  # accuracy fine, too few charts


def test_parse_reading():
    assert parse_reading('```json\n{"trend":"up","levels":[1,2.5]}\n```').levels == [1.0, 2.5]
    assert parse_reading("nope").trend is None
    assert parse_reading('{"trend":"MOON"}').trend is None
