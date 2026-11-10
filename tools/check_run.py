#!/usr/bin/env python3
"""Workflow checks for the agent run: run between steps by the orchestration runner.

The agents follow instructions; this script checks the parts that can be checked
mechanically, so a missing handoff, a stale file from an earlier run, or an SLA result the
data or the test validity result does not support stops the workflow instead of reaching
the test summary.

Usage:
  python3 tools/check_run.py init  <test run folder>            # create a fresh run folder, print its path
  python3 tools/check_run.py ready <run folder> <step>          # before dispatching a step (1-9)
  python3 tools/check_run.py results <run folder> <file>        # check the Results block in 09 or TEST-SUMMARY.md

Exit status 0 means the check passed. Any other status means stop: do not dispatch the step
or publish the file; record the message in the run log.

Rules for the Results block (method/test-summary-results.md):
  * Test validity must match the Test Execution Analyst's result in 03-test-execution.md.
  * Every SLA in scenario.json is listed, with Pass, Fail or Not evaluated.
  * A reported result can never be stronger than the computed candidate result in facts.json:
    candidate Pass -> Pass or Not evaluated; Fail -> Fail or Not evaluated; Not evaluated -> Not evaluated.
  * When the test is Invalid, every SLA result is Not evaluated, and the go/no-go is not a Go.

Standard library only.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

VALIDITY = ("Valid", "Valid with limitations", "Invalid")
SLA_RESULTS = ("Pass", "Fail", "Not evaluated")
GO_NO_GO = ("Go", "Go with conditions", "No-go", "No recommendation")
ALLOWED = {"Pass": {"Pass", "Not evaluated"}, "Fail": {"Fail", "Not evaluated"}, "Not evaluated": {"Not evaluated"}}

# Handoffs that must exist, and be written during this run, before each step is dispatched.
REQUIRES = {
    1: [],
    2: ["01-analysis-plan.md"],
    3: ["01-analysis-plan.md", "02-data-inventory.md"],
    4: ["02-data-inventory.md", "03-test-execution.md"],
    5: ["03-test-execution.md", "04-results-analysis.md"],
    6: ["02-data-inventory.md"],
    7: ["03-test-execution.md", "04-results-analysis.md", "08a-initial-review.md"],
    8: ["02-data-inventory.md", "03-test-execution.md", "04-results-analysis.md",
        "08a-initial-review.md", "08b-peer-review.md"],
    9: ["03-test-execution.md", "04-results-analysis.md", "09-go-no-go.md"],
}


class CheckFailed(Exception):
    pass


def test_folder(run_dir: Path) -> Path:
    return run_dir.parent


def facts(run_dir: Path) -> dict:
    path = test_folder(run_dir) / "facts.json"
    if not path.exists():
        raise CheckFailed(f"{path} not found: run tools/analyze.py first")
    return json.loads(path.read_text())


def validity(run_dir: Path) -> str:
    path = run_dir / "03-test-execution.md"
    if not path.exists():
        raise CheckFailed("03-test-execution.md not found: no test validity result")
    m = re.search(r"^Test validity:\s*(.+?)\s*$", path.read_text(), re.M)
    if not m or m.group(1) not in VALIDITY:
        raise CheckFailed("03-test-execution.md has no line 'Test validity: Valid | Valid with limitations | Invalid'")
    return m.group(1)


def init(test_dir: Path) -> Path:
    if not (test_dir / "facts.json").exists():
        raise CheckFailed(f"{test_dir}/facts.json not found: run tools/analyze.py first")
    run_dir = test_dir / ("run-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
    run_dir.mkdir()  # fails if it exists: a run folder is never reused
    return run_dir


def ready(run_dir: Path, step: int) -> None:
    if step not in REQUIRES:
        raise CheckFailed(f"unknown step {step}")
    if not run_dir.is_dir() or not run_dir.name.startswith("run-"):
        raise CheckFailed(f"{run_dir} is not a run folder created by 'check_run.py init'")
    facts_time = (test_folder(run_dir) / "facts.json").stat().st_mtime
    problems = []
    for name in REQUIRES[step]:
        p = run_dir / name
        if not p.exists() or not p.read_text().strip():
            problems.append(f"{name} is missing or empty")
        elif p.stat().st_mtime < facts_time:
            problems.append(f"{name} is older than facts.json (stale)")
    if problems:
        raise CheckFailed(f"step {step} cannot start: " + "; ".join(problems))
    if step >= 4:
        validity(run_dir)


def results_block(text: str) -> dict:
    m = re.search(r"^## Results block\s*$(.*?)(?=^## |\Z)", text, re.M | re.S)
    if not m:
        raise CheckFailed("no '## Results block' section")
    block = {}
    for line in m.group(1).splitlines():
        line = line.strip().strip("`").lstrip("-* ").strip()
        kv = re.match(r"^(Test validity|Go/no-go|SLA-[\w.-]+):\s*(.+?)\s*$", line)
        if kv:
            block[kv.group(1)] = kv.group(2).rstrip(".")
    return block


def results(run_dir: Path, file: Path) -> None:
    block = results_block(file.read_text())
    f = facts(run_dir)
    candidates = {sid: v["result"] for sid, v in f["sla_results"]["slas"].items()}
    val = validity(run_dir)
    problems = []
    if block.get("Test validity") != val:
        problems.append(f"Test validity is '{block.get('Test validity')}', but 03-test-execution.md says '{val}'")
    for sid, cand in candidates.items():
        got = block.get(sid)
        if got not in SLA_RESULTS:
            problems.append(f"{sid}: '{got}' is not one of {', '.join(SLA_RESULTS)}")
        elif val == "Invalid" and got != "Not evaluated":
            problems.append(f"{sid}: the test is Invalid, so the SLA result is Not evaluated, not {got}")
        elif got not in ALLOWED[cand]:
            problems.append(f"{sid}: reported {got}, but the computed candidate result is {cand}")
    gng = block.get("Go/no-go")
    if gng not in GO_NO_GO:
        problems.append(f"Go/no-go '{gng}' is not one of {', '.join(GO_NO_GO)}")
    elif val == "Invalid" and gng.startswith("Go"):
        problems.append("the test is Invalid, so the recommendation cannot be a Go")
    if problems:
        raise CheckFailed(f"{file.name}: " + "; ".join(problems))


def main(argv: list[str]) -> int:
    try:
        if len(argv) == 2 and argv[0] == "init":
            print(init(Path(argv[1])))
        elif len(argv) == 3 and argv[0] == "ready":
            ready(Path(argv[1]), int(argv[2]))
            print(f"step {argv[2]}: ready")
        elif len(argv) == 3 and argv[0] == "results":
            results(Path(argv[1]), Path(argv[2]))
            print(f"{Path(argv[2]).name}: results block consistent")
        else:
            print(__doc__, file=sys.stderr)
            return 2
    except (CheckFailed, FileExistsError, OSError, ValueError, json.JSONDecodeError) as e:
        print(f"STOP: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
