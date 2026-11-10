"""Tests for the deterministic tooling: the calculations and data handling
the agents rely on. These do not test the agents' analysis.
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
S0 = ROOT / "examples" / "00-baseline" / "data"


def inv(facts, name):
    return next(i for i in facts["inventory"] if i["file"] == name)


def test_fixtures_are_reproducible(tmp_path):
    generate_synthetic.generate_all(tmp_path)
    for name in ("00-baseline", "01-generator-saturation", "02-connection-pool"):
        committed, fresh = ROOT / "examples" / name / "data", tmp_path / name / "data"
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


def test_failure_types_add_up_to_failed():
    for row in analyze.load_csv(S1 / "transactions.csv") + analyze.load_csv(S2 / "transactions.csv"):
        parts = int(row["failed_timeout"]) + int(row["failed_http_5xx"]) + int(row["failed_content_check"])
        assert parts == int(row["failed"])


def test_transaction_summary_matches_per_minute_counts():
    rows = analyze.load_csv(S2 / "transactions.csv")
    for r in analyze.load_csv(S2 / "transaction_summary.csv"):
        per_min = [x for x in rows if 10 <= int(x["elapsed_min"]) <= 39 and x["transaction"] == r["transaction"]
                   and (r["generator"] == "ALL" or x["generator"] == r["generator"])]
        assert sum(int(x["count"]) for x in per_min) == int(r["count"])
        assert sum(int(x["failed"]) for x in per_min) == int(r["failed"])


def test_baseline_comparison_flags_regression_only_when_slower():
    s0, s2 = analyze.analyze(S0), analyze.analyze(S2)
    assert s0["baseline"] is None
    assert all(t["regression"] for t in s2["baseline"]["transactions"])
    assert s2["baseline"]["steady_tps"]["change_pct"] < 0


def test_capacity_uses_utilization_law():
    cap = analyze.analyze(S0)["capacity"]["windows"]["min 10-39"]
    app1 = cap["app1"]
    assert abs(app1["cpu_pct_per_tps"] * app1["tps_handled"] - app1["mean_cpu_pct"]) < 0.2
    assert abs(app1["cpu_bound_ceiling_tps"] - 80 / app1["cpu_pct_per_tps"]) < 0.2
    assert app1["other_monitored_limit_detected"] is False and app1["other_limits_seen"] == []


def test_graphs_are_written(tmp_path):
    facts = analyze.analyze(S1)
    made = analyze.write_charts(facts, tmp_path)
    assert {name for _, name in made} == {"running-vusers.svg", "throughput.svg", "checkout-p95.svg", "errors.svg"}
    assert all((tmp_path / name).read_text().startswith("<svg") for _, name in made)


def test_draft_handoff_example_validates_against_draft_schema():
    import json
    jsonschema = __import__("pytest").importorskip("jsonschema")
    schema = json.loads((ROOT / "schemas" / "handoff.schema.json").read_text())
    jsonschema.Draft202012Validator.check_schema(schema)
    example = json.loads((ROOT / "schemas" / "examples" / "03-test-execution.example.json").read_text())
    jsonschema.validate(example, schema)


def test_sections_split_the_summary_without_losing_content(tmp_path):
    facts = analyze.analyze(S2)
    md = analyze.to_markdown(facts, [("Throughput", "charts/throughput.svg")])
    written = analyze.write_sections(md, tmp_path / "facts", tmp_path)
    assert {"overview.md", "load-profile.md", "capacity.md", "inventory.md", "metrics-app_servers.md"} <= set(written)
    overview = (tmp_path / "facts" / "overview.md").read_text()
    assert "## Transaction summary" in overview and "## SLA results" in overview
    assert "](../charts/throughput.svg)" in overview
    body_lines = {ln for ln in md.splitlines() if ln.startswith("| ")}
    split_lines = {ln for f in written for ln in (tmp_path / "facts" / f).read_text().splitlines() if ln.startswith("| ")}
    assert body_lines <= split_lines


# ---------------------------------------------------------------- SLA evaluation
import csv  # noqa: E402
import json  # noqa: E402
import shutil  # noqa: E402


def copy_run(tmp_path, src=S2):
    dst = tmp_path / "data"
    shutil.copytree(src, dst)
    return dst


def rewrite_csv(path, keep=lambda r: True, change=lambda r: r):
    rows = list(csv.DictReader(path.open()))
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(change(dict(r)) for r in rows if keep(r))


def edit_slas(data, fn):
    sc = json.loads((data / "scenario.json").read_text())
    fn(sc["slas"])
    (data / "scenario.json").write_text(json.dumps(sc))


def slas(data):
    return analyze.analyze(data)["sla_results"]["slas"]


def test_sla_thresholds_come_from_scenario(tmp_path):
    data = copy_run(tmp_path)
    assert slas(data)["SLA-1"]["result"] == "Fail"
    edit_slas(data, lambda s: s[0].update(value=10.0))
    assert slas(data)["SLA-1"]["result"] == "Pass"
    edit_slas(data, lambda s: s[0].update(value=0.5))
    assert slas(data)["SLA-1"]["counts"]["Fail"] == 30


def test_missing_p95_is_not_evaluated_not_pass(tmp_path):
    data = copy_run(tmp_path, S0)  # healthy baseline: every minute passes
    assert slas(data)["SLA-1"]["result"] == "Pass"
    rewrite_csv(data / "transactions.csv",
                change=lambda r: {**r, "p95_s": ""} if r["elapsed_min"] == "20" and r["generator"] == "LG2"
                and r["transaction"] == "checkout" else r)
    res = slas(data)["SLA-1"]
    assert res["per_minute"][20]["result"] == "Not evaluated"
    assert res["result"] == "Not evaluated"


def test_missing_load_generator_rows_are_not_evaluated(tmp_path):
    data = copy_run(tmp_path, S0)
    rewrite_csv(data / "transactions.csv", keep=lambda r: not (r["elapsed_min"] == "25" and r["generator"] == "LG1"))
    res = slas(data)
    assert res["SLA-1"]["per_minute"][25]["result"] == "Not evaluated"
    assert res["SLA-2"]["per_minute"][25]["result"] in ("Not evaluated", "Fail")
    assert res["SLA-1"]["result"] == "Not evaluated"


def test_no_transactions_is_not_evaluated(tmp_path):
    data = copy_run(tmp_path, S0)
    rewrite_csv(data / "transactions.csv", keep=lambda r: r["elapsed_min"] != "30")
    res = slas(data)
    assert res["SLA-2"]["per_minute"][30] == {"value": None, "result": "Not evaluated", "missing": ["LG1", "LG2"]}
    assert res["SLA-2"]["result"] == "Not evaluated"
    assert res["SLA-3"]["result"] == "Not evaluated"
    assert "30" in res["SLA-3"]["reason"]


def test_unsupported_or_incomplete_sla_is_not_evaluated(tmp_path):
    data = copy_run(tmp_path)
    edit_slas(data, lambda s: s.extend([{"id": "SLA-9", "metric": "CPU", "threshold": "<= 70%"},
                                        {"id": "SLA-8", "type": "apdex", "operator": ">=", "value": 0.9,
                                         "evaluation": "window"}]))
    res = slas(data)
    assert res["SLA-9"]["result"] == "Not evaluated" and "machine-readable" in res["SLA-9"]["reason"]
    assert res["SLA-8"]["result"] == "Not evaluated" and "not supported" in res["SLA-8"]["reason"]


def test_window_response_time_uses_run_summary_never_averages(tmp_path):
    data = copy_run(tmp_path)
    edit_slas(data, lambda s: s[0].update(evaluation="window"))
    res = slas(data)["SLA-1"]
    assert res["window_value"] == 6.28 and res["result"] == "Fail"
    (data / "transaction_summary.csv").unlink()
    res = slas(data)["SLA-1"]
    assert res["result"] == "Not evaluated" and "cannot be averaged" in res["reason"]


# ---------------------------------------------------------------- input validation and data boundaries
def test_missing_scenario_fields_block_analysis(tmp_path):
    import pytest
    data = copy_run(tmp_path)
    sc = json.loads((data / "scenario.json").read_text())
    del sc["workload_model"]["steady_state_min"]
    sc["run"]["start_utc"] = "not a time"
    (data / "scenario.json").write_text(json.dumps(sc))
    with pytest.raises(analyze.InputError) as e:
        analyze.analyze(data)
    assert "steady_state_min" in str(e.value) and "start_utc" in str(e.value)


def test_missing_required_column_blocks_analysis(tmp_path):
    import pytest
    data = copy_run(tmp_path)
    rows = list(csv.DictReader((data / "vusers.csv").open()))
    with (data / "vusers.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=[c for c in rows[0] if c != "running_vusers"])
        w.writeheader()
        w.writerows({k: v for k, v in r.items() if k != "running_vusers"} for r in rows)
    with pytest.raises(analyze.InputError, match="running_vusers"):
        analyze.analyze(data)


def test_malformed_values_are_missing_not_zero(tmp_path):
    data = copy_run(tmp_path, S0)
    rewrite_csv(data / "transactions.csv",
                change=lambda r: {**r, "count": "abc"} if r["elapsed_min"] == "20" and r["generator"] == "LG1"
                and r["transaction"] == "search" else
                ({**r, "p95_s": "n/a"} if r["elapsed_min"] == "21" and r["generator"] == "LG2"
                 and r["transaction"] == "checkout" else r))
    f = analyze.analyze(data)
    msgs = " ".join(c["message"] for c in f["input_checks"])
    assert "malformed" in msgs and "non-numeric p95_s" in msgs
    sla = f["sla_results"]["slas"]
    assert sla["SLA-1"]["per_minute"][21]["result"] == "Not evaluated"
    assert sla["SLA-1"]["result"] == "Not evaluated"


def test_elapsed_minutes_are_checked_against_timestamps(tmp_path):
    data = copy_run(tmp_path, S0)
    rewrite_csv(data / "vusers.csv", change=lambda r: {**r, "elapsed_min": "99"} if r["elapsed_min"] == "12" else r)
    f = analyze.analyze(data)
    assert any("disagrees with the timestamp" in c["message"] for c in f["input_checks"])
    assert {m["elapsed_min"] for m in f["load_profile"]["minutes"]} == set(range(45))


def test_baseline_comparison_is_qualified():
    s1, s2 = analyze.analyze(S1)["baseline"], analyze.analyze(S2)["baseline"]
    assert s1["comparable"] is False and "planned load not running" in s1["not_comparable_because"][0]
    assert all(t["regression"] is None and t["slower_than_threshold"] for t in s1["transactions"])
    assert s2["comparable"] is True and all(t["regression"] for t in s2["transactions"])


def test_baseline_not_comparable_when_design_differs(tmp_path):
    data = copy_run(tmp_path)
    shutil.copytree(S0, tmp_path / "base")
    sc = json.loads((data / "scenario.json").read_text())
    sc["baseline"]["data_dir"] = str(tmp_path / "base")
    sc["test_type"] = "soak"
    (data / "scenario.json").write_text(json.dumps(sc))
    bc = analyze.analyze(data)["baseline"]
    assert bc["comparable"] is False and any("test type differs" in r for r in bc["not_comparable_because"])


def test_cpu_ceiling_flags_other_limits():
    cap = analyze.analyze(S2)["capacity"]["windows"]["min 19-39"]["app1"]
    assert cap["other_monitored_limit_detected"] is True
    assert any("connection pool" in x for x in cap["other_limits_seen"])


# ---------------------------------------------------------------- data-quality boundaries (second external review)
def tx_rows(data):
    return list(csv.DictReader((data / "transactions.csv").open()))


def write_tx(data, rows):
    with (data / "transactions.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)


def test_exact_duplicate_rows_are_counted_once(tmp_path):
    data = copy_run(tmp_path, S0)
    before = analyze.analyze(data)["sla_results"]["slas"]["SLA-2"]["per_minute"][20]["value"]
    rows = tx_rows(data)
    dup = next(r for r in rows if r["elapsed_min"] == "20" and r["generator"] == "LG1" and r["transaction"] == "search")
    write_tx(data, rows + [dict(dup)])
    f = analyze.analyze(data)
    assert f["sla_results"]["slas"]["SLA-2"]["per_minute"][20]["value"] == before
    assert any("exact duplicate" in c["message"] for c in f["input_checks"])


def test_conflicting_duplicate_rows_become_missing_never_pass(tmp_path):
    data = copy_run(tmp_path, S0)
    rows = tx_rows(data)
    dup = dict(next(r for r in rows if r["elapsed_min"] == "20" and r["generator"] == "LG1" and r["transaction"] == "search"))
    dup["count"] = str(int(dup["count"]) + 500)
    dup["passed"] = str(int(dup["passed"]) + 500)
    write_tx(data, rows + [dup])
    f = analyze.analyze(data)
    slas = f["sla_results"]["slas"]
    assert any("conflicting rows" in c["message"] for c in f["input_checks"])
    assert slas["SLA-2"]["per_minute"][20]["result"] == "Not evaluated"
    assert slas["SLA-2"]["result"] == "Not evaluated"


def test_missing_transaction_type_is_not_evaluated(tmp_path):
    data = copy_run(tmp_path, S0)
    rewrite_csv(data / "transactions.csv",
                keep=lambda r: not (r["elapsed_min"] == "25" and r["generator"] == "LG1" and r["transaction"] == "checkout"))
    f = analyze.analyze(data)
    slas = f["sla_results"]["slas"]
    assert slas["SLA-2"]["per_minute"][25]["result"] == "Not evaluated"
    assert "LG1/checkout" in slas["SLA-2"]["per_minute"][25]["missing"]
    assert slas["SLA-2"]["result"] == "Not evaluated"
    assert slas["SLA-3"]["result"] == "Not evaluated"  # window: minute incomplete and summary no longer matches


def test_window_counts_reconciled_with_run_summary(tmp_path):
    data = copy_run(tmp_path, S0)
    rows = list(csv.DictReader((data / "transaction_summary.csv").open()))
    rows[0]["count"] = str(int(rows[0]["count"]) + 1)
    with (data / "transaction_summary.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    f = analyze.analyze(data)
    assert f["sla_results"]["summary_mismatches"]
    assert f["sla_results"]["slas"]["SLA-3"]["result"] == "Not evaluated"
    assert "does not match" in analyze.to_markdown(f)


def test_threshold_compared_at_full_precision(tmp_path):
    data = copy_run(tmp_path, S0)
    rows = tx_rows(data)
    minute = [r for r in rows if r["elapsed_min"] == "20"]
    total = sum(int(r["count"]) for r in minute)
    target = 5399  # 89.983 TPS: rounds to 90.0, but is below a >= 90 threshold
    biggest = max(minute, key=lambda r: int(r["count"]))
    delta = total - target
    biggest["count"] = str(int(biggest["count"]) - delta)
    biggest["passed"] = str(int(biggest["passed"]) - delta)
    write_tx(data, rows)
    e = analyze.analyze(data)["sla_results"]["slas"]["SLA-2"]["per_minute"][20]
    assert e["value"] == 89.98 and e["result"] == "Fail"


def test_error_rate_compared_at_full_precision(tmp_path):
    data = copy_run(tmp_path, S0)
    edit_slas(data, lambda s: s[2].update(evaluation="per_minute"))
    rows = tx_rows(data)
    minute = [r for r in rows if r["elapsed_min"] == "20"]
    total = sum(int(r["count"]) for r in minute)
    want_failed = int(total * 0.01004) + 1  # just above 1%, would round to 1.0
    r0 = minute[0]
    extra = want_failed - sum(int(r["failed"]) for r in minute)
    r0["failed"] = str(int(r0["failed"]) + extra)
    r0["passed"] = str(int(r0["passed"]) - extra)
    r0["failed_content_check"] = str(int(r0["failed_content_check"]) + extra)
    write_tx(data, rows)
    e = analyze.analyze(data)["sla_results"]["slas"]["SLA-3"]["per_minute"][20]
    assert 100 * want_failed / total > 1.0 and e["result"] == "Fail"


def test_malformed_trace_values_do_not_crash(tmp_path):
    data = copy_run(tmp_path)
    rewrite_csv(data / "checkout_traces.csv",
                change=lambda r: {**r, "payment_call_ms": "n/a"} if r["trace_id"] == "T200" else r)
    f = analyze.analyze(data)
    w = f["traces"]["min 19-39"]
    assert w["traces_with_missing_values"] == 1 and w["payment_share_of_connection_hold_pct"] > 90


def test_nan_and_infinite_values_are_missing(tmp_path):
    data = copy_run(tmp_path, S0)
    rewrite_csv(data / "transactions.csv",
                change=lambda r: {**r, "p95_s": "NaN"} if r["elapsed_min"] == "15" and r["generator"] == "LG1"
                and r["transaction"] == "checkout" else
                ({**r, "p95_s": "inf"} if r["elapsed_min"] == "16" and r["generator"] == "LG2"
                 and r["transaction"] == "checkout" else r))
    slas = analyze.analyze(data)["sla_results"]["slas"]
    assert analyze.num("NaN") is None and analyze.num("-inf") is None
    assert slas["SLA-1"]["per_minute"][15]["result"] == "Not evaluated"
    assert slas["SLA-1"]["per_minute"][16]["result"] == "Not evaluated"
    assert slas["SLA-1"]["result"] == "Not evaluated"


# ---------------------------------------------------------------- independent audit (PEL-01 to PEL-08)
import xml.etree.ElementTree as ET  # noqa: E402
import subprocess  # noqa: E402

import pytest  # noqa: E402


def copy_pair(tmp_path):
    """Run 02 and its baseline, laid out like examples/ so the relative baseline path works."""
    root = tmp_path / "examples"
    shutil.copytree(S2, root / "02-connection-pool" / "data")
    shutil.copytree(S0, root / "00-baseline" / "data")
    return root / "02-connection-pool" / "data", root / "00-baseline" / "data"


def summary_rows(data):
    return list(csv.DictReader((data / "transaction_summary.csv").open()))


def write_summary(data, rows):
    with (data / "transaction_summary.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)


def all_checkout(rows):
    return next(r for r in rows if r["generator"] == "ALL" and r["transaction"] == "checkout")


# PEL-01
def test_window_response_time_rejects_contradictory_summary(tmp_path):
    data = copy_run(tmp_path)
    edit_slas(data, lambda s: s[0].update(evaluation="window"))
    rewrite_csv(data / "transactions.csv", keep=lambda r: not (r["elapsed_min"] == "20" and r["generator"] == "LG1"
                                                               and r["transaction"] == "checkout"))
    rows = summary_rows(data)
    all_checkout(rows).update(p95_s="0.1", count="1", passed="1", failed="0")
    write_summary(data, rows)
    res = slas(data)["SLA-1"]
    assert res["result"] == "Not evaluated"


def test_window_response_time_rejects_conflicting_summary_rows(tmp_path):
    data = copy_run(tmp_path)
    edit_slas(data, lambda s: s[0].update(evaluation="window"))
    rows = summary_rows(data)
    fake = dict(all_checkout(rows), min_s="0.01", avg_s="0.05", p90_s="0.09", p95_s="0.1")  # self-consistent
    write_summary(data, [fake] + rows)
    f = analyze.analyze(data)
    assert f["sla_results"]["slas"]["SLA-1"]["result"] == "Not evaluated"
    assert any("conflicting rows for ALL/checkout" in c["message"] for c in f["input_checks"])


def test_window_response_time_rejects_summary_for_wrong_window(tmp_path):
    data = copy_run(tmp_path)
    edit_slas(data, lambda s: s[0].update(evaluation="window"))
    rows = summary_rows(data)
    for r in rows:
        r["steady_state_min"] = "0-44"
    write_summary(data, rows)
    assert slas(data)["SLA-1"]["result"] == "Not evaluated"


def test_window_response_time_uses_reconciled_summary_without_minute_percentiles(tmp_path):
    data = copy_run(tmp_path)
    edit_slas(data, lambda s: s[0].update(evaluation="window"))
    rewrite_csv(data / "transactions.csv", change=lambda r: {**r, "p95_s": ""})
    res = slas(data)["SLA-1"]
    assert res["result"] == "Fail" and res["window_value"] == 6.28 and "reconciled" in res["reason"]


# PEL-02
def test_baseline_missing_a_generator_is_not_comparable(tmp_path):
    data, base = copy_pair(tmp_path)
    assert analyze.analyze(data)["baseline"]["comparable"] is True
    for name in ("vusers.csv", "transactions.csv"):
        rewrite_csv(base / name, keep=lambda r: r["generator"] != "LG2")
    bc = analyze.analyze(data)["baseline"]
    assert bc["comparable"] is False and all(t["regression"] is None for t in bc["transactions"])
    assert any("LG2 missing" in r for r in bc["not_comparable_because"])


def test_current_run_missing_a_generator_is_not_comparable(tmp_path):
    data, _ = copy_pair(tmp_path)
    rewrite_csv(data / "vusers.csv", keep=lambda r: r["generator"] != "LG2")
    bc = analyze.analyze(data)["baseline"]
    assert bc["comparable"] is False and all(t["regression"] is None for t in bc["transactions"])
    assert any("this run" in r and "250 running, 250 scheduled, 500 planned" in r for r in bc["not_comparable_because"])


# PEL-03
def test_impossible_transaction_statistics_never_pass(tmp_path):
    data = copy_run(tmp_path, S0)
    rewrite_csv(data / "transactions.csv",
                change=lambda r: {**r, "passed": "0", "failed": "0", "p95_s": "-1"}
                if r["elapsed_min"] == "20" and r["generator"] == "LG1" and r["transaction"] == "checkout" else r)
    f = analyze.analyze(data)
    s = f["sla_results"]["slas"]
    assert s["SLA-1"]["per_minute"][20]["result"] == "Not evaluated" and s["SLA-1"]["result"] == "Not evaluated"
    assert any("does not equal count" in c["message"] for c in f["input_checks"])


@pytest.mark.parametrize("change, message", [
    (lambda r: {**r, "p95_s": "-0.5"}, "negative response time"),
    (lambda r: {**r, "p95_s": str(float(r["p99_s"]) + 1)}, "out of order"),
    (lambda r: {**r, "passed": "0", "failed": r["count"], "failed_content_check": r["count"],
                "failed_timeout": "0", "failed_http_5xx": "0"}, "zero passed"),
    (lambda r: {**r, "failed_timeout": str(int(r["failed_timeout"]) + 1)}, "failure types do not add up"),
])
def test_invalid_rows_are_reported_and_never_pass(tmp_path, change, message):
    data = copy_run(tmp_path, S0)
    target = lambda r: r["elapsed_min"] == "20" and r["generator"] == "LG1" and r["transaction"] == "checkout"
    rewrite_csv(data / "transactions.csv", change=lambda r: change(r) if target(r) else r)
    f = analyze.analyze(data)
    assert any(message in c["message"] for c in f["input_checks"])
    assert f["sla_results"]["slas"]["SLA-1"]["result"] != "Pass"


def test_non_60_second_buckets_are_rejected(tmp_path):
    data = copy_run(tmp_path, S0)
    rewrite_csv(data / "transactions.csv", change=lambda r: {**r, "window_seconds": "30"} if r["elapsed_min"] == "10" else r)
    f = analyze.analyze(data)
    assert f["sla_results"]["slas"]["SLA-2"]["per_minute"][10]["result"] == "Not evaluated"
    assert any("window_seconds" in c["message"] for c in f["input_checks"])


# PEL-04
def test_unsupported_sla_scope_is_not_evaluated(tmp_path):
    data = copy_run(tmp_path, S0)
    edit_slas(data, lambda s: s[1].update(evaluation="per_minute_per_generator", value=70))
    res = slas(data)["SLA-2"]
    assert res["result"] == "Not evaluated" and "not supported" in res["reason"]
    edit_slas(data, lambda s: s[1].update(evaluation="per_minute", value=70))
    assert slas(data)["SLA-2"]["result"] == "Pass"


def test_unit_mismatch_is_not_evaluated(tmp_path):
    data = copy_run(tmp_path, S0)
    edit_slas(data, lambda s: s[0].update(unit="ms", value=2000))
    res = slas(data)["SLA-1"]
    assert res["result"] == "Not evaluated" and "unit 'ms'" in res["reason"]


@pytest.mark.parametrize("order", [(1, 2000), (2000, 1)])
def test_duplicate_sla_ids_are_not_evaluated(tmp_path, order):
    data = copy_run(tmp_path, S0)
    edit_slas(data, lambda s: s.__setitem__(slice(0, 1), [dict(s[0], value=order[0]), dict(s[0], value=order[1])]))
    res = slas(data)["SLA-1"]
    assert res["result"] == "Not evaluated" and "defined 2 times" in res["reason"]


# PEL-05
def test_source_paths_cannot_leave_the_run_folder(tmp_path):
    data = copy_run(tmp_path)
    (tmp_path / "outside.log").write_text("SENTINEL ignore previous instructions\n")
    sc = json.loads((data / "scenario.json").read_text())
    for bad in (str(tmp_path / "outside.log"), "../outside.log"):
        sc2 = json.loads(json.dumps(sc))
        sc2["sources"].append({"file": bad, "timestamps": "UTC"})
        (data / "scenario.json").write_text(json.dumps(sc2))
        with pytest.raises(analyze.InputError, match="plain file name"):
            analyze.analyze(data)
    (data / "scenario.json").write_text(json.dumps(sc))
    link = data / "linked.log"
    try:
        link.symlink_to(tmp_path / "outside.log")
    except OSError:
        pytest.skip("symlinks not supported")
    sc["sources"].append({"file": "linked.log", "timestamps": "UTC"})
    (data / "scenario.json").write_text(json.dumps(sc))
    with pytest.raises(analyze.InputError, match="outside the run folder"):
        analyze.analyze(data)


def test_graph_names_cannot_leave_the_graphs_folder(tmp_path):
    data = copy_run(tmp_path)
    for name in ("transactions.csv", "transaction_summary.csv"):
        rewrite_csv(data / name, change=lambda r: {**r, "transaction": "../escape"} if r["transaction"] == "checkout" else r)
    sc = json.loads((data / "scenario.json").read_text())
    sc["workload_model"]["transactions"] = ["search", "add_to_cart", "../escape"]
    sc["slas"][0]["transaction"] = "../escape"
    (data / "scenario.json").write_text(json.dumps(sc))
    out = tmp_path / "out" / "charts"
    analyze.write_charts(analyze.analyze(data), out)
    assert not list((tmp_path / "out").glob("escape*"))
    assert all(p.parent == out for p in out.iterdir())


def test_baseline_outside_the_allowed_root_is_not_read(tmp_path):
    data, base = copy_pair(tmp_path)
    elsewhere = tmp_path / "elsewhere"
    shutil.copytree(base, elsewhere)
    sc = json.loads((data / "scenario.json").read_text())
    sc["baseline"]["data_dir"] = str(elsewhere)
    (data / "scenario.json").write_text(json.dumps(sc))
    bc = analyze.analyze(data)["baseline"]
    assert bc["available"] is False and "outside the allowed root" in bc["reason"]
    assert analyze.analyze(data, baseline_root=tmp_path)["baseline"]["available"] is True


# PEL-06
@pytest.mark.parametrize("current, expected", [("1.1004", True), ("1.1000", False), ("1.0996", False)])
def test_regression_threshold_uses_unrounded_change(tmp_path, current, expected):
    data, base = copy_pair(tmp_path)
    for d, v in ((base, "1.0000"), (data, current)):
        rows = summary_rows(d)
        for r in rows:
            r.update(min_s="0.1", avg_s="0.9", p90_s=v, p95_s=v, p99_s="5", max_s="9")
        write_summary(d, rows)
    bc = analyze.analyze(data)["baseline"]
    assert bc["comparable"] is True
    assert all(t["regression"] is expected for t in bc["transactions"])


# PEL-07
@pytest.mark.parametrize("damage", ["zero_db_cpu", "empty_app_servers", "extra_field", "no_baseline_transactions"])
def test_data_problems_are_reported_not_crashes(tmp_path, damage):
    data, base = copy_pair(tmp_path)
    if damage == "zero_db_cpu":
        rewrite_csv(data / "database.csv", change=lambda r: {**r, "cpu_pct": "0"})
    elif damage == "empty_app_servers":
        header = (data / "app_servers.csv").read_text().splitlines()[0]
        (data / "app_servers.csv").write_text(header + "\n")
    elif damage == "extra_field":
        lines = (data / "transactions.csv").read_text().splitlines()
        lines[100] += ",EXTRA"
        (data / "transactions.csv").write_text("\n".join(lines) + "\n")
    else:
        (base / "transactions.csv").unlink()
    f = analyze.analyze(data)
    md = analyze.to_markdown(f)
    if damage == "zero_db_cpu":
        assert all(w["database"]["cpu_bound_ceiling_tps"] is None for w in f["capacity"]["windows"].values())
    elif damage == "empty_app_servers":
        assert any(c["file"] == "app_servers.csv" for c in f["input_checks"])
    elif damage == "extra_field":
        assert any("number of fields" in c["message"] for c in f["input_checks"])
    else:
        assert f["baseline"]["available"] is False and "cannot be loaded" in f["baseline"]["reason"]
    assert "## SLA results" in md


def test_cli_reports_input_errors_with_exit_status(tmp_path):
    data = copy_run(tmp_path)
    (data / "vusers.csv").write_text("generator\n")
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "analyze.py"), str(data)], capture_output=True, text=True)
    assert r.returncode != 0 and "Cannot analyze" in r.stderr


# PEL-08
def test_every_standard_graph_is_valid_xml(tmp_path):
    for src in (S0, S1, S2):
        out = tmp_path / src.parent.name
        for _, name in analyze.write_charts(analyze.analyze(src), out):
            ET.parse(out / name)


def test_unsupported_sla_statistic_does_not_break_graphs(tmp_path):
    data = copy_run(tmp_path)
    edit_slas(data, lambda s: s[0].update(statistic="p99x_s"))
    f = analyze.analyze(data)
    assert f["sla_results"]["slas"]["SLA-1"]["result"] == "Not evaluated"
    made = analyze.write_charts(f, tmp_path / "charts")
    assert "checkout-p95.svg" in {n for _, n in made}
    for _, name in made:
        ET.parse(tmp_path / "charts" / name)
