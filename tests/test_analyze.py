"""Checks that the deterministic layer keeps the method's rules.

These test the arithmetic and evidence-handling tools, not the agents'
judgment.
"""
import filecmp
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import analyze  # noqa: E402
import generate_synthetic  # noqa: E402

S1 = ROOT / "examples" / "01-generator-saturation" / "data"
S2 = ROOT / "examples" / "02-connection-pool" / "data"


def inv(facts, name):
    return next(i for i in facts["inventory"] if i["file"] == name)


def test_fixtures_are_reproducible(tmp_path):
    generate_synthetic.scenario_checkout_generator(tmp_path / "s1")
    generate_synthetic.scenario_checkout_pool(tmp_path / "s2")
    for committed, fresh in ((S1, tmp_path / "s1"), (S2, tmp_path / "s2")):
        names = sorted(p.name for p in committed.iterdir())
        assert names == sorted(p.name for p in fresh.iterdir())
        match, mismatch, errors = filecmp.cmpfiles(committed, fresh, names, shallow=False)
        assert not mismatch and not errors


def test_percentiles_are_never_averaged():
    facts = analyze.analyze(S1)
    for windows in facts["summaries"].values():
        for groups in windows.values():
            for stats in groups.values():
                for col, value in stats.items():
                    if col.startswith("p95"):
                        assert set(value) == {"median_of_minute_values", "max_minute_value"}


def test_local_database_time_is_normalized_to_utc():
    facts = analyze.analyze(S1)
    db = inv(facts, "database.csv")
    assert db["range_utc"][0] == "2026-10-01T10:00:00Z"
    assert "converted to UTC" in db["normalization"]


def test_monitoring_gap_is_reported_not_filled():
    facts = analyze.analyze(S1)
    assert inv(facts, "app_servers.csv")["missing_minutes"] == {"app2": [26, 27, 28]}
    window = facts["summaries"]["app_servers.csv"]["min 16-39"]
    assert window["app2"]["minutes_present"] == window["app1"]["minutes_present"] - 3


def test_prompt_injection_log_lines_are_flagged():
    flagged = inv(analyze.analyze(S1), "generator_errors.log")["prompt_injection_lines"]
    assert len(flagged) == 1 and "ignore your previous instructions" in flagged[0]


def test_sla_onset_and_load_profile_shortfall():
    s1, s2 = analyze.analyze(S1), analyze.analyze(S2)
    assert s1["sla_results"]["first_failing_minute"] == 16
    assert s2["sla_results"]["first_failing_minute"] == 19
    late = [m for m in s1["load_profile"]["minutes"] if 23 <= m["elapsed_min"] <= 39]
    assert all(m["running_vusers"] < m["scheduled_vusers"] for m in late)
    late2 = [m for m in s2["load_profile"]["minutes"] if 23 <= m["elapsed_min"] <= 39]
    assert all(m["running_vusers"] == m["scheduled_vusers"] for m in late2)


def test_trace_breakdown_shows_connection_held_during_payment_call():
    traces = analyze.analyze(S2)["traces"]
    assert traces["min 19-39"]["payment_share_of_connection_hold_pct"] > 90
    assert traces["min 10-18"]["median_pool_wait_ms"] == 0
