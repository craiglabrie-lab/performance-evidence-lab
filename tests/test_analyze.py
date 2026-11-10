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
