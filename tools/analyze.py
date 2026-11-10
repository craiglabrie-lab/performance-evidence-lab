#!/usr/bin/env python3
"""Computed results summary for a load test results folder.

Deterministic tooling for the agentic workflow: the agents analyze, this
script does the math. It reads the files listed in scenario.json and writes
the computed results summary (facts.md / facts.json) that every sub-agent
works from, so no agent calculates numbers on its own.

What it does:
  * inventory: rows, time range (normalized to UTC), missing minutes per entity
  * load profile: scheduled vs running virtual users, throughput, error rate, Little's Law
  * SLA results: per steady-state minute Pass/Fail against scenario.json
  * windowed summaries of every numeric metric, per entity
  * prompt-injection scan of text logs
  * transaction summary, errors by type, standard graphs (SVG)
  * capacity: Utilization Law service demand and CPU headroom per tier
  * baseline comparison against the run named in scenario.json
  * trace breakdown (when traces exist)

What it never does:
  * average percentiles. Per-minute p95 values are reported as median/max of
    the minute values and labeled as such; a run-level p95 is not computed
  * fill gaps. Missing minutes are listed, never zero-filled

Usage:
  python tools/analyze.py examples/01-generator-saturation/data
  python tools/analyze.py <data_dir> --windows 10-16 17-39 --json facts.json
  python tools/analyze.py <data_dir> --md facts.md --charts charts

Standard library only.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import re
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ENTITY_COLUMNS = ("generator", "node", "component", "dependency")
INJECTION_PATTERNS = re.compile(
    r"ignore (all |your |the )?(previous |prior )?instructions|note to ai|system prompt|"
    r"report this test as|you are now|disregard", re.I)


# ------------------------------------------------------------------ loading
def parse_time(value: str) -> datetime:
    value = value.strip()
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    if re.search(r"[+-]\d{4}$", value):
        value = value[:-2] + ":" + value[-2:]
    ts = datetime.fromisoformat(value)
    if ts.tzinfo is None:
        raise ValueError(f"timestamp without timezone: {value!r}")
    return ts.astimezone(timezone.utc)


def load_csv(path: Path) -> list[dict]:
    with path.open(newline="") as fh:
        return list(csv.DictReader(fh))


def num(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def add_elapsed(rows: list[dict], start: datetime) -> str | None:
    """Ensure every row has elapsed_min and time_utc. Returns the source time column."""
    if not rows:
        return None
    time_col = next((c for c in rows[0] if c.startswith("window_start") or c.startswith("timestamp")), None)
    for r in rows:
        if time_col:
            ts = parse_time(r[time_col])
            r["_time_utc"] = ts.strftime("%Y-%m-%dT%H:%M:%SZ")
            if not r.get("elapsed_min"):
                r["elapsed_min"] = str(int((ts - start).total_seconds() // 60))
    return time_col


def entity_of(row: dict) -> str:
    for c in ENTITY_COLUMNS:
        if c in row:
            return row[c]
    return "all"


# ------------------------------------------------------------------ analysis
def inventory(data_dir: Path, scenario: dict, start: datetime, tables: dict) -> list[dict]:
    duration = scenario["run"]["duration_min"]
    out = []
    for s in scenario["sources"]:
        f = s["file"]
        path = data_dir / f
        item = {"file": f, "present": path.exists(), "timestamps": s["timestamps"],
                "limitations": s.get("known_limitations", "")}
        if not path.exists():
            out.append(item)
            continue
        if f == "transaction_summary.csv":
            item["rows"] = len(load_csv(path))
            item["coverage"] = {"steady state": "run-level summary"}
        elif f.endswith(".csv"):
            rows = tables[f]
            item["rows"] = len(rows)
            times = sorted(r["_time_utc"] for r in rows if "_time_utc" in r)
            item["range_utc"] = [times[0], times[-1]] if times else None
            if s["timestamps"] != "UTC":
                item["normalization"] = "converted to UTC using the offset in each timestamp"
            per_entity = defaultdict(set)
            for r in rows:
                per_entity[entity_of(r)].add(int(r["elapsed_min"]))
            if f != "checkout_traces.csv":
                missing = {}
                for ent, mins in per_entity.items():
                    gaps = [m for m in range(duration) if m not in mins]
                    if gaps and not (f == "transactions.csv"):
                        missing[ent] = gaps
                item["missing_minutes"] = missing
                item["coverage"] = {e: f"{len(m)}/{duration} minutes" for e, m in per_entity.items()}
        else:
            text = path.read_text()
            item["lines"] = len(text.splitlines())
            flagged = [ln for ln in text.splitlines() if INJECTION_PATTERNS.search(ln)]
            item["prompt_injection_lines"] = flagged
        out.append(item)
    return out


def workload(scenario: dict, tables: dict) -> dict:
    wl = scenario["workload_model"]
    pacing = float(re.search(r"(\d+)s", wl["pacing"]).group(1))
    vus = defaultdict(lambda: {"scheduled": 0, "running": 0, "exited": 0})
    per_gen_running = defaultdict(dict)
    for r in tables["vusers.csv"]:
        m = int(r["elapsed_min"])
        vus[m]["scheduled"] += int(r["scheduled_vusers"])
        vus[m]["running"] += int(r["running_vusers"])
        vus[m]["exited"] += int(r["exited_with_error"])
        per_gen_running[r["generator"]][m] = int(r["running_vusers"])
    tx = defaultdict(lambda: {"count": 0, "failed": 0, "checkout": 0})
    gen_tps = defaultdict(lambda: defaultdict(float))
    for r in tables["transactions.csv"]:
        m = int(r["elapsed_min"])
        c = int(r["count"])
        tx[m]["count"] += c
        tx[m]["failed"] += int(r["failed"])
        gen_tps[r["generator"]][m] += c / 60
        if r["transaction"] == "checkout":
            tx[m]["checkout"] += c
    minutes = []
    for m in sorted(vus):
        t = tx.get(m, {"count": 0, "failed": 0, "checkout": 0})
        iters_per_s = t["checkout"] / 60
        running = vus[m]["running"]
        minutes.append({
            "elapsed_min": m,
            "scheduled_vusers": vus[m]["scheduled"], "running_vusers": running,
            "exited_with_error": vus[m]["exited"],
            "tps": round(t["count"] / 60, 1),
            "error_rate_pct": round(100 * t["failed"] / t["count"], 2) if t["count"] else None,
            "iterations_per_s": round(iters_per_s, 2),
            "implied_cycle_s": round(running / iters_per_s, 1) if iters_per_s else None,
        })
    return {"pacing_s": pacing, "minutes": minutes,
            "per_generator_tps": {g: {m: round(v, 1) for m, v in sorted(d.items())} for g, d in gen_tps.items()},
            "per_generator_running": {g: dict(sorted(d.items())) for g, d in per_gen_running.items()},
            "littles_law_note": "implied_cycle_s = running users / iterations per second (one checkout per "
                                "iteration). With fixed pacing it should equal the pacing interval; a larger "
                                "value means iterations are running late (responses + think time exceed pacing)."}


def criteria(scenario: dict, tables: dict, wl: dict) -> dict:
    lo, hi = scenario["workload_model"]["steady_state_min"]
    by_minute = {}
    for m in range(lo, hi + 1):
        rows = [r for r in tables["transactions.csv"] if int(r["elapsed_min"]) == m]
        checkout = {r["generator"]: num(r["p95_s"]) for r in rows if r["transaction"] == "checkout"}
        w = next(x for x in wl["minutes"] if x["elapsed_min"] == m)
        by_minute[m] = {
            "SLA-1 checkout p95 by generator (s)": checkout,
            "SLA-1": "FAIL" if any(v is not None and v > 2.0 for v in checkout.values()) else "PASS",
            "SLA-2 tps": w["tps"], "SLA-2": "PASS" if w["tps"] >= 90 else "FAIL",
            "SLA-3 error %": w["error_rate_pct"],
            "SLA-3": "PASS" if (w["error_rate_pct"] or 0) <= 1.0 else "FAIL",
        }
    fails = {k: [m for m, v in by_minute.items() if v[k] == "FAIL"] for k in ("SLA-1", "SLA-2", "SLA-3")}
    steady_tx = [r for r in tables["transactions.csv"] if lo <= int(r["elapsed_min"]) <= hi]
    total = sum(int(r["count"]) for r in steady_tx)
    failed = sum(int(r["failed"]) for r in steady_tx)
    first_fail = min((m for ms in fails.values() for m in ms), default=None)
    return {"steady_state_min": [lo, hi], "per_minute": by_minute, "failing_minutes": fails,
            "steady_error_rate_pct": round(100 * failed / total, 2) if total else None,
            "first_failing_minute": first_fail,
            "note": "SLA-1 is judged per generator per minute because p95 values cannot be averaged."}


def summarize(tables: dict, windows: list[tuple[int, int]]) -> dict:
    out = {}
    for f, rows in tables.items():
        if not rows:
            continue
        numeric = [c for c in rows[0] if c not in ("elapsed_min", "window_seconds") and not c.startswith("_")
                   and any(num(r[c]) is not None for r in rows[:5]) and not c.startswith("window_start")]
        p_cols = [c for c in numeric if re.match(r"p\d+", c)]
        group_cols = [c for c in ENTITY_COLUMNS + ("transaction",) if c in rows[0]]
        res = {}
        for lo, hi in windows:
            key = f"min {lo}-{hi}"
            groups = defaultdict(list)
            for r in rows:
                if lo <= int(r["elapsed_min"]) <= hi:
                    groups[" / ".join(r[c] for c in group_cols) or "all"].append(r)
            wres = {}
            for g, rs in sorted(groups.items()):
                stats = {"minutes_present": len({r["elapsed_min"] for r in rs})}
                for c in numeric:
                    vals = [num(r[c]) for r in rs if num(r[c]) is not None]
                    if not vals:
                        stats[c] = "no values"
                        continue
                    if c in p_cols:
                        stats[c] = {"median_of_minute_values": round(statistics.median(vals), 2),
                                    "max_minute_value": round(max(vals), 2)}
                    else:
                        stats[c] = {"min": round(min(vals), 2), "mean": round(statistics.fmean(vals), 2),
                                    "max": round(max(vals), 2)}
                wres[g] = stats
            res[key] = wres
        out[f] = res
    return out


def traces(tables: dict, windows) -> dict | None:
    rows = tables.get("checkout_traces.csv")
    if not rows:
        return None
    out = {}
    for lo, hi in windows:
        rs = [r for r in rows if lo <= int(r["elapsed_min"]) <= hi]
        if not rs:
            continue
        def med(c):
            return round(statistics.median(float(r[c]) for r in rs), 0)
        held = [float(r["db_connection_held_ms"]) for r in rs]
        pay = [float(r["payment_call_ms"]) for r in rs]
        out[f"min {lo}-{hi}"] = {
            "traces": len(rs),
            "median_total_ms": med("total_ms"), "median_pool_wait_ms": med("pool_wait_ms"),
            "median_sql_ms": med("sql_ms"), "median_payment_call_ms": med("payment_call_ms"),
            "median_connection_held_ms": med("db_connection_held_ms"),
            "payment_share_of_connection_hold_pct": round(100 * sum(pay) / sum(held), 1),
        }
    return out


def default_windows(scenario: dict, first_fail: int | None) -> list[tuple[int, int]]:
    w = scenario["workload_model"]
    r_lo, r_hi = w["ramp_up_min"]
    s_lo, s_hi = w["steady_state_min"]
    d_lo, d_hi = w["ramp_down_min"]
    wins = [(r_lo, r_hi)]
    if first_fail and s_lo < first_fail <= s_hi:
        wins += [(s_lo, first_fail - 1), (first_fail, s_hi)]
    else:
        wins.append((s_lo, s_hi))
    wins.append((d_lo, d_hi))
    return wins


def analyze(data_dir: Path, windows=None) -> dict:
    scenario = json.loads((data_dir / "scenario.json").read_text())
    start = parse_time(scenario["run"]["start_utc"])
    tables = {}
    for s in scenario["sources"]:
        p = data_dir / s["file"]
        if p.suffix == ".csv" and p.exists() and s["file"] != "transaction_summary.csv":
            rows = load_csv(p)
            add_elapsed(rows, start)
            tables[s["file"]] = rows
    wl = workload(scenario, tables)
    crit = criteria(scenario, tables, wl)
    wins = windows or default_windows(scenario, crit["first_failing_minute"])
    return {
        "run": scenario["run"], "test_objective": scenario["test_objective"],
        "generated_by": "tools/analyze.py (deterministic; no AI model involved)",
        "windows": [f"min {a}-{b}" for a, b in wins],
        "window_rule": "Default windows: planned ramp-up, steady state split at the first minute any "
                       "SLA fails, and ramp-down." if not windows else "User-specified.",
        "inventory": inventory(data_dir, scenario, start, tables),
        "load_profile": wl, "sla_results": crit,
        "summaries": summarize(tables, wins),
        "traces": traces(tables, wins),
        "execution": execution(scenario),
        "transaction_summary": transaction_summary(data_dir),
        "errors_by_type": errors_by_type(tables, wins),
        "capacity": capacity(tables, wins),
        "baseline": baseline_comparison(data_dir, scenario, tables),
        "_tables": tables, "_scenario": scenario,
    }


# ------------------------------------------------------------------ tester and engineer views
def execution(scenario: dict) -> dict:
    keys = ("test_type", "build_under_test", "environment_parity", "scripts", "test_data",
            "runtime_settings", "load_generators", "baseline")
    return {k: scenario.get(k) for k in keys if scenario.get(k) is not None}


def transaction_summary(data_dir: Path) -> list[dict] | None:
    path = data_dir / "transaction_summary.csv"
    return load_csv(path) if path.exists() else None


def errors_by_type(tables: dict, windows) -> dict | None:
    rows = tables.get("transactions.csv", [])
    if not rows or "failed_timeout" not in rows[0]:
        return None
    out = {}
    for lo, hi in windows:
        agg = defaultdict(lambda: {"failed": 0, "timeout": 0, "http_5xx": 0, "content_check": 0, "count": 0})
        for r in rows:
            if lo <= int(r["elapsed_min"]) <= hi:
                a = agg[r["generator"]]
                a["count"] += int(r["count"])
                a["failed"] += int(r["failed"])
                a["timeout"] += int(r["failed_timeout"])
                a["http_5xx"] += int(r["failed_http_5xx"])
                a["content_check"] += int(r["failed_content_check"])
        out[f"min {lo}-{hi}"] = dict(agg)
    return out


def steady_tps(rows: list[dict], lo: int, hi: int) -> float:
    per_min = defaultdict(int)
    for r in rows:
        m = int(r["elapsed_min"])
        if lo <= m <= hi:
            per_min[m] += int(r["count"])
    return round(statistics.fmean(v / 60 for v in per_min.values()), 1) if per_min else None


def capacity(tables: dict, windows) -> dict:
    """Utilization Law (U = X * D): CPU percent per transaction/s, and the throughput at 80% CPU.

    Assumes the load balancer splits traffic evenly across app nodes, CPU scales linearly
    with throughput, and CPU is the limiting resource. Results apply to this test
    environment only.
    """
    tx = tables.get("transactions.csv", [])
    tps = defaultdict(float)
    for r in tx:
        tps[int(r["elapsed_min"])] += int(r["count"]) / 60
    out = {"assumptions": "Even load balancing across app nodes; CPU scales linearly with throughput; CPU is "
                          "the limiting resource. Applies to this test environment only.", "windows": {}}
    for lo, hi in windows:
        res = {}
        mins = [m for m in tps if lo <= m <= hi and tps[m] > 0]
        if not mins:
            continue
        x = statistics.fmean(tps[m] for m in mins)
        for node in sorted({r["node"] for r in tables.get("app_servers.csv", [])}):
            cpus = [num(r["cpu_pct"]) for r in tables["app_servers.csv"]
                    if r["node"] == node and lo <= int(r["elapsed_min"]) <= hi]
            if cpus:
                u = statistics.fmean(cpus)
                d = u / (x / 2)
                res[node] = {"mean_cpu_pct": round(u, 1), "tps_handled": round(x / 2, 1),
                             "cpu_pct_per_tps": round(d, 3), "tps_at_80pct_cpu": round(80 / d, 1)}
        cpus = [num(r["cpu_pct"]) for r in tables.get("database.csv", []) if lo <= int(r["elapsed_min"]) <= hi]
        if cpus:
            u = statistics.fmean(cpus)
            d = u / x
            res["database"] = {"mean_cpu_pct": round(u, 1), "tps_handled": round(x, 1),
                               "cpu_pct_per_tps": round(d, 3), "tps_at_80pct_cpu": round(80 / d, 1)}
        out["windows"][f"min {lo}-{hi}"] = res
    return out


def baseline_comparison(data_dir: Path, scenario: dict, tables: dict) -> dict | None:
    b = scenario.get("baseline")
    if not b:
        return None
    bdir = (data_dir / b["data_dir"]).resolve()
    base = transaction_summary(bdir)
    cur = transaction_summary(data_dir)
    if not base or not cur:
        return {"run_id": b["run_id"], "available": False}
    thr = b.get("regression_threshold_pct", 10)
    lo, hi = scenario["workload_model"]["steady_state_min"]
    bt = steady_tps(load_csv(bdir / "transactions.csv"), lo, hi)
    ct = steady_tps(tables["transactions.csv"], lo, hi)
    rows = []
    bmap = {(r["generator"], r["transaction"]): r for r in base}
    for r in cur:
        if r["generator"] != "ALL":
            continue
        br = bmap[("ALL", r["transaction"])]
        row = {"transaction": r["transaction"]}
        for c in ("avg_s", "p90_s", "p95_s", "p99_s"):
            bv, cv = float(br[c]), float(r[c])
            row[c] = {"baseline": bv, "current": cv, "change_pct": round(100 * (cv - bv) / bv, 1)}
        row["error_pct"] = {"baseline": float(br["error_pct"]), "current": float(r["error_pct"])}
        row["regression"] = row["p90_s"]["change_pct"] > thr or row["p95_s"]["change_pct"] > thr
        rows.append(row)
    return {"run_id": b["run_id"], "build": b.get("build"), "available": True, "threshold_pct": thr,
            "steady_tps": {"baseline": bt, "current": ct,
                           "change_pct": round(100 * (ct - bt) / bt, 1) if bt and ct else None},
            "transactions": rows,
            "note": "Compares this run with the baseline run. Baseline data is never used to fill gaps "
                    "in this run."}


# ------------------------------------------------------------------ graphs (SVG)
SERIES = ["#2a78d6", "#eb6834", "#1baf7a"]  # categorical slots 1-3 of the reference palette
INK, INK2, GRID, SURFACE = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"


def svg_line_chart(path: Path, title: str, series: dict, y_label: str, threshold=None,
                   steady=None, x_max=44) -> None:
    W, H, L, R_, T, B = 720, 300, 56, 16, 52, 40
    ys = [y for pts in series.values() for _, y in pts if y is not None]
    raw = max(ys + ([threshold[0]] if threshold else [])) * 1.08 or 1
    mag = 10 ** math.floor(math.log10(raw / 4))
    step = next(m * mag for m in (1, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10) if m * mag * 4 >= raw)
    y_max = step * 4
    sx = lambda x: L + (W - L - R_) * x / x_max
    sy = lambda y: H - B - (H - T - B) * y / y_max
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
         f'font-family="system-ui, -apple-system, Segoe UI, sans-serif" role="img" aria-label="{title}">',
         f'<rect width="{W}" height="{H}" fill="{SURFACE}"/>',
         f'<text x="{L}" y="20" font-size="14" font-weight="600" fill="{INK}">{title}</text>']
    for i in range(5):
        v = y_max * i / 4
        o.append(f'<line x1="{L}" x2="{W - R_}" y1="{sy(v):.1f}" y2="{sy(v):.1f}" stroke="{GRID}" stroke-width="1"/>')
        o.append(f'<text x="{L - 6}" y="{sy(v) + 4:.1f}" font-size="11" fill="{INK2}" text-anchor="end">{v:g}</text>')
    for x in range(0, x_max + 1, 5):
        o.append(f'<text x="{sx(x):.1f}" y="{H - B + 16}" font-size="11" fill="{INK2}" text-anchor="middle">{x}</text>')
    o.append(f'<text x="{(L + W - R_) / 2}" y="{H - 6}" font-size="11" fill="{INK2}" text-anchor="middle">Elapsed minute</text>')
    o.append(f'<text x="14" y="{(T + H - B) / 2}" font-size="11" fill="{INK2}" text-anchor="middle" '
             f'transform="rotate(-90 14 {(T + H - B) / 2})">{y_label}</text>')
    if steady:
        for x, lab in ((steady[0], "steady state starts"), (steady[1], "ends")):
            o.append(f'<line x1="{sx(x):.1f}" x2="{sx(x):.1f}" y1="{T}" y2="{H - B}" stroke="{INK2}" '
                     f'stroke-width="1" stroke-dasharray="2 3"/>')
            o.append(f'<text x="{sx(x) + 4:.1f}" y="{T + 10}" font-size="10" fill="{INK2}">{lab}</text>')
    if threshold:
        o.append(f'<line x1="{L}" x2="{W - R_}" y1="{sy(threshold[0]):.1f}" y2="{sy(threshold[0]):.1f}" '
                 f'stroke="{INK}" stroke-width="1.5" stroke-dasharray="6 4"/>')
        o.append(f'<text x="{W - R_ - 4}" y="{sy(threshold[0]) - 5:.1f}" font-size="11" fill="{INK}" '
                 f'text-anchor="end">{threshold[1]}</text>')
    lx = L
    for i, (name, pts) in enumerate(series.items()):
        c = SERIES[i % len(SERIES)]
        segs, cur = [], []
        for x, y in pts:
            if y is None:
                if cur:
                    segs.append(cur)
                cur = []
            else:
                cur.append(f"{sx(x):.1f},{sy(y):.1f}")
        if cur:
            segs.append(cur)
        for sg in segs:
            o.append(f'<polyline points="{" ".join(sg)}" fill="none" stroke="{c}" stroke-width="2" '
                     f'stroke-linejoin="round" stroke-linecap="round"/>')
        o.append(f'<rect x="{lx}" y="30" width="12" height="3" rx="1.5" fill="{c}"/>')
        o.append(f'<text x="{lx + 16}" y="35" font-size="11" fill="{INK}">{name}</text>')
        lx += 24 + 7 * len(name)
    o.append("</svg>")
    path.write_text("\n".join(o) + "\n")


def write_charts(f: dict, out_dir: Path) -> list[tuple[str, str]]:
    out_dir.mkdir(parents=True, exist_ok=True)
    t = f["_tables"]
    sc = f["_scenario"]
    steady = sc["workload_model"]["steady_state_min"]
    gens = sorted({r["generator"] for r in t["vusers.csv"]})
    made = []

    def by_gen(rows, col, gen, tx=None, agg=False):
        d = defaultdict(float) if agg else {}
        for r in rows:
            if r["generator"] == gen and (tx is None or r["transaction"] == tx):
                v = num(r[col])
                if agg:
                    d[int(r["elapsed_min"])] += v or 0
                else:
                    d[int(r["elapsed_min"])] = v
        return sorted(d.items())

    charts = [
        ("running-vusers.svg", "Running Vusers by load generator",
         {g: by_gen(t["vusers.csv"], "running_vusers", g) for g in gens}, "Vusers", None),
        ("throughput.svg", "Throughput (all transactions)",
         {"Total TPS": [(m["elapsed_min"], m["tps"]) for m in f["load_profile"]["minutes"]]}, "Transactions/s",
         (90, "SLA-2: 90 TPS")),
        ("checkout-p95.svg", "Checkout p95 response time by load generator",
         {g: by_gen(t["transactions.csv"], "p95_s", g, "checkout") for g in gens}, "Seconds",
         (2.0, "SLA-1: 2.0 s")),
    ]
    if t["transactions.csv"] and "failed_timeout" in t["transactions.csv"][0]:
        err = {}
        for col, name in (("failed_timeout", "Client timeouts"), ("failed_http_5xx", "HTTP 5xx"),
                          ("failed_content_check", "Content check failures")):
            d = defaultdict(int)
            for r in t["transactions.csv"]:
                d[int(r["elapsed_min"])] += int(r[col])
            err[name] = sorted(d.items())
        charts.append(("errors.svg", "Failed transactions per minute by type", err, "Failures/minute", None))
    for name, title, series, ylab, thr in charts:
        svg_line_chart(out_dir / name, title, series, ylab, threshold=thr, steady=steady)
        made.append((title, name))
    return made


# ------------------------------------------------------------------ output
def overview_markdown(f: dict, charts=None) -> list[str]:
    L = []
    ex = f.get("execution") or {}
    if ex:
        b = ex.get("build_under_test", {})
        L += ["## Test run overview", "", "| Item | Value |", "| --- | --- |",
              f"| Test type | {ex.get('test_type', 'not stated')} |",
              f"| Build under test | {b.get('application', '')} {b.get('version', '')} |",
              f"| Changes since baseline | {', '.join(b.get('changes_since_baseline') or []) or 'none listed'} |"]
        bl = ex.get("baseline")
        L.append(f"| Baseline run | {bl['run_id']} (build {bl.get('build')}) |" if bl else "| Baseline run | none |")
        for k, v in (ex.get("environment_parity") or {}).items():
            L.append(f"| Environment parity: {k.replace('_', ' ')} | {v} |")
        for k, v in (ex.get("runtime_settings") or {}).items():
            L.append(f"| Runtime setting: {k.replace('_', ' ')} | {v} |")
        for g, v in (ex.get("load_generators") or {}).items():
            if isinstance(v, dict):
                L.append(f"| {g} | {v.get('vcpu')} vCPU, log level {v.get('log_level')} |")
        for sc in ex.get("scripts") or []:
            L.append(f"| Script | {sc['name']} v{sc['version']}: {sc.get('content_checks', '')}; "
                     f"correlation {sc.get('correlation', '')} |")
        for k, v in (ex.get("test_data") or {}).items():
            L.append(f"| Test data: {k} | {v} |")
        L.append("")
    ts = f.get("transaction_summary")
    if ts:
        L += ["## Transaction summary (steady state)", "",
              "From `transaction_summary.csv`, the load tool's run-level summary. Response times are for passed "
              "transactions, in seconds.", "",
              "| Load generator | Transaction | Count | Passed | Failed | Error % | Min | Avg | p90 | p95 | p99 | Max | Std dev |",
              "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
        for r in ts:
            L.append(f"| {r['generator']} | {r['transaction']} | {r['count']} | {r['passed']} | {r['failed']} | "
                     f"{r['error_pct']} | {r['min_s']} | {r['avg_s']} | {r['p90_s']} | {r['p95_s']} | {r['p99_s']} | "
                     f"{r['max_s']} | {r['std_dev_s']} |")
        L.append("")
    if charts:
        L += ["## Graphs", ""]
        L += [f"![{title}]({path})" for title, path in charts]
        L.append("")
    bc = f.get("baseline")
    if bc and bc.get("available"):
        L += [f"## Baseline comparison: {bc['run_id']} (build {bc['build']})", "",
              f"{bc['note']} A transaction is flagged when p90 or p95 is more than {bc['threshold_pct']}% "
              "slower than the baseline.", "",
              f"Steady-state throughput: {bc['steady_tps']['current']} TPS against {bc['steady_tps']['baseline']} TPS "
              f"in the baseline ({bc['steady_tps']['change_pct']}%).", "",
              "| Transaction | Avg (base → now) | p90 (base → now) | p95 (base → now) | p99 (base → now) | Error % (base → now) | Regression |",
              "| --- | --- | --- | --- | --- | --- | --- |"]
        for r in bc["transactions"]:
            cells = [f"{r[c]['baseline']} → {r[c]['current']} ({r[c]['change_pct']:+}%)" for c in ("avg_s", "p90_s", "p95_s", "p99_s")]
            L.append(f"| {r['transaction']} | " + " | ".join(cells) +
                     f" | {r['error_pct']['baseline']} → {r['error_pct']['current']} | {'YES' if r['regression'] else 'no'} |")
        L.append("")
    eb = f.get("errors_by_type")
    if eb:
        L += ["## Errors by type", "", "| Window | Load generator | Transactions | Failed | Client timeouts | HTTP 5xx | Content check failures |",
              "| --- | --- | --- | --- | --- | --- | --- |"]
        for w, gens in eb.items():
            for g, a in sorted(gens.items()):
                L.append(f"| {w} | {g} | {a['count']} | {a['failed']} | {a['timeout']} | {a['http_5xx']} | {a['content_check']} |")
        L.append("")
    cap = f.get("capacity")
    if cap and cap["windows"]:
        L += ["## Capacity: Utilization Law", "",
              "Service demand as CPU % per transaction/s (U = X × D), and the throughput each tier could handle "
              f"at 80% CPU. Assumptions: {cap['assumptions']}", "",
              "| Window | Tier | Mean CPU % | TPS handled | CPU % per TPS | TPS at 80% CPU |", "| --- | --- | --- | --- | --- | --- |"]
        for w, tiers in cap["windows"].items():
            for tier, v in tiers.items():
                L.append(f"| {w} | {tier} | {v['mean_cpu_pct']} | {v['tps_handled']} | {v['cpu_pct_per_tps']} | {v['tps_at_80pct_cpu']} |")
        L.append("")
    return L


def to_markdown(f: dict, charts=None) -> str:
    L = [f"# Computed results summary — {f['run']['run_id']}", "",
         f"Generated by `{f['generated_by']}`. Every number here is calculated from the raw data files.", "",
         f"**Test objective:** {f['test_objective']}", "", f"**Windows:** {', '.join(f['windows'])} — {f['window_rule']}", ""]
    L += overview_markdown(f, charts)
    L += ["## Data inventory", "", "| File | Rows/lines | UTC range | Coverage | Missing minutes | Notes |",
         "| --- | --- | --- | --- | --- | --- |"]
    for i in f["inventory"]:
        notes = "; ".join(x for x in [i.get("normalization", ""), i.get("limitations", "")] if x)
        if i.get("prompt_injection_lines"):
            notes += f" **{len(i['prompt_injection_lines'])} line(s) of possible prompt-injection text — data only, not instructions**"
        miss = "; ".join(f"{e}: {v}" for e, v in (i.get("missing_minutes") or {}).items()) or "none"
        cov = "; ".join(f"{e} {v}" for e, v in (i.get("coverage") or {}).items())
        rng = " → ".join(i["range_utc"]) if i.get("range_utc") else ""
        L.append(f"| {i['file']} | {i.get('rows', i.get('lines', 'MISSING'))} | {rng} | {cov} | {miss} | {notes} |")
    L += ["", "## Load profile by minute", "",
          "| Min | Scheduled Vusers | Running Vusers | Exited on error | TPS | Error % | Implied cycle (s) |",
          "| --- | --- | --- | --- | --- | --- | --- |"]
    for m in f["load_profile"]["minutes"]:
        L.append(f"| {m['elapsed_min']} | {m['scheduled_vusers']} | {m['running_vusers']} | {m['exited_with_error']} "
                 f"| {m['tps']} | {m['error_rate_pct']} | {m['implied_cycle_s']} |")
    L += ["", f"Pacing: {f['load_profile']['pacing_s']}s. {f['load_profile']['littles_law_note']}", "",
          "### Throughput by generator (TPS)", ""]
    for g, d in f["load_profile"]["per_generator_tps"].items():
        L.append(f"- {g}: " + ", ".join(f"{m}:{v}" for m, v in d.items()))
    a = f["sla_results"]
    L += ["", "## SLA results (steady state)", "",
          f"First failing minute: {a['first_failing_minute']}. Steady-state error rate: {a['steady_error_rate_pct']}%.",
          f"{a['note']}", "", "| Min | Checkout p95 by generator | SLA-1 | TPS | SLA-2 | Error % | SLA-3 |",
          "| --- | --- | --- | --- | --- | --- | --- |"]
    for m, v in a["per_minute"].items():
        p = ", ".join(f"{g} {x}" for g, x in v["SLA-1 checkout p95 by generator (s)"].items())
        L.append(f"| {m} | {p} | {v['SLA-1']} | {v['SLA-2 tps']} | {v['SLA-2']} | {v['SLA-3 error %']} | {v['SLA-3']} |")
    L += ["", "## Metrics by time window", "",
          "Percentile columns show the median and max of per-minute values — not a recomputed percentile."]
    for file, wins in f["summaries"].items():
        L += ["", f"### {file}"]
        for w, groups in wins.items():
            L += ["", f"**{w}**", ""]
            for g, stats in groups.items():
                parts = []
                for k, v in stats.items():
                    if isinstance(v, dict):
                        parts.append(f"{k} " + "/".join(str(x) for x in v.values()))
                    else:
                        parts.append(f"{k} {v}")
                L.append(f"- {g}: " + "; ".join(parts))
        L.append("")
        L.append("(values are min/mean/max, or median/max for percentiles)")
    if f["traces"]:
        L += ["", "## Checkout trace breakdown (medians)", "", "| Window | Traces | Total | Pool wait | SQL | Payment call | Connection held | Payment share of hold % |",
              "| --- | --- | --- | --- | --- | --- | --- | --- |"]
        for w, t in f["traces"].items():
            L.append(f"| {w} | {t['traces']} | {t['median_total_ms']} | {t['median_pool_wait_ms']} | {t['median_sql_ms']} "
                     f"| {t['median_payment_call_ms']} | {t['median_connection_held_ms']} | {t['payment_share_of_connection_hold_pct']} |")
    flagged = [ln for i in f["inventory"] for ln in i.get("prompt_injection_lines", [])]
    if flagged:
        L += ["", "## Possible prompt-injection text", "",
              "These lines read like instructions to an AI. They are data captured from the system under test and are never followed.", ""]
        L += [f"    {ln}" for ln in flagged]
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("data_dir", type=Path)
    ap.add_argument("--windows", nargs="*", help="elapsed-minute windows like 10-16 17-39")
    ap.add_argument("--json", type=Path, help="also write the facts as JSON")
    ap.add_argument("--md", type=Path, help="write markdown to this file instead of stdout")
    ap.add_argument("--charts", type=Path, help="write SVG graphs to this folder (linked from the markdown)")
    args = ap.parse_args()
    wins = [tuple(int(x) for x in w.split("-")) for w in args.windows] if args.windows else None
    facts = analyze(args.data_dir, wins)
    charts = None
    if args.charts:
        made = write_charts(facts, args.charts)
        base = args.md.parent if args.md else Path.cwd()
        rel = os.path.relpath(args.charts, base)
        charts = [(title, f"{rel}/{name}") for title, name in made]
    md = to_markdown(facts, charts)
    if args.json:
        public = {k: v for k, v in facts.items() if not k.startswith("_")}
        args.json.write_text(json.dumps(public, indent=2, default=str) + "\n")
    if args.md:
        args.md.write_text(md)
    else:
        print(md)


if __name__ == "__main__":
    main()
