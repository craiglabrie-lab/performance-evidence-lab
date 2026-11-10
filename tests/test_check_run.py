"""Tests for the workflow checks the runner applies between agents."""
import json
import os
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import check_run  # noqa: E402

S1 = ROOT / "examples" / "01-generator-saturation"
S2 = ROOT / "examples" / "02-connection-pool"


def make_run(tmp_path, src=S2):
    test = tmp_path / src.name
    test.mkdir()
    shutil.copy(src / "facts.json", test / "facts.json")
    return check_run.init(test)


def write(run, name, text="Agent: test\n"):
    (run / name).write_text(text)


def block(validity, slas, gng):
    lines = ["# Go/no-go", "", "## Results block", "", f"Test validity: {validity}"]
    lines += [f"{k}: {v}" for k, v in slas.items()] + [f"Go/no-go: {gng}", "", "## Findings", "SLA-1: Pass"]
    return "\n".join(lines) + "\n"


def test_init_creates_a_fresh_folder_and_never_reuses_one(tmp_path):
    run = make_run(tmp_path)
    assert run.is_dir() and run.name.startswith("run-") and not any(run.iterdir())
    with pytest.raises(FileExistsError):
        run.mkdir()


def test_missing_handoff_stops_the_dependent_step(tmp_path):
    run = make_run(tmp_path)
    check_run.ready(run, 1)
    write(run, "01-analysis-plan.md")
    with pytest.raises(check_run.CheckFailed, match="02-data-inventory.md is missing"):
        check_run.ready(run, 3)
    assert check_run.main(["ready", str(run), "3"]) == 1


def test_stale_handoff_stops_the_step(tmp_path):
    run = make_run(tmp_path)
    write(run, "01-analysis-plan.md")
    old = (run.parent / "facts.json").stat().st_mtime - 3600
    os.utime(run / "01-analysis-plan.md", (old, old))
    with pytest.raises(check_run.CheckFailed, match="stale"):
        check_run.ready(run, 2)


def test_validity_line_is_required_before_results_analysis(tmp_path):
    run = make_run(tmp_path)
    write(run, "02-data-inventory.md")
    write(run, "03-test-execution.md", "Agent: Test Execution Analyst\nThe test looks fine.\n")
    with pytest.raises(check_run.CheckFailed, match="Test validity"):
        check_run.ready(run, 4)
    write(run, "03-test-execution.md", "Agent: Test Execution Analyst\n\nTest validity: Valid\n")
    check_run.ready(run, 4)


def test_invalid_test_cannot_report_sla_results_or_a_go(tmp_path):
    run = make_run(tmp_path, S1)
    write(run, "03-test-execution.md", "Test validity: Invalid\n")
    bad = run / "09-go-no-go.md"
    bad.write_text(block("Invalid", {"SLA-1": "Fail", "SLA-2": "Fail", "SLA-3": "Fail"}, "Go"))
    with pytest.raises(check_run.CheckFailed) as e:
        check_run.results(run, bad)
    assert "Not evaluated, not Fail" in str(e.value) and "cannot be a Go" in str(e.value)
    bad.write_text(block("Invalid", {"SLA-1": "Not evaluated", "SLA-2": "Not evaluated",
                                     "SLA-3": "Not evaluated"}, "No-go"))
    check_run.results(run, bad)


def test_reported_result_never_stronger_than_the_candidate(tmp_path):
    run = make_run(tmp_path)
    write(run, "03-test-execution.md", "Test validity: Valid\n")
    f = run / "09-go-no-go.md"
    f.write_text(block("Valid", {"SLA-1": "Pass", "SLA-2": "Fail", "SLA-3": "Pass"}, "No-go"))
    with pytest.raises(check_run.CheckFailed, match="SLA-1: reported Pass, but the computed candidate result is Fail"):
        check_run.results(run, f)
    f.write_text(block("Valid", {"SLA-1": "Fail", "SLA-2": "Fail", "SLA-3": "Pass"}, "No-go"))
    check_run.results(run, f)


def test_validity_must_match_the_test_execution_analyst(tmp_path):
    run = make_run(tmp_path)
    write(run, "03-test-execution.md", "Test validity: Valid with limitations\n")
    f = run / "TEST-SUMMARY.md"
    f.write_text(block("Valid", {"SLA-1": "Fail", "SLA-2": "Fail", "SLA-3": "Pass"}, "No-go"))
    with pytest.raises(check_run.CheckFailed, match="03-test-execution.md says"):
        check_run.results(run, f)


def test_every_sla_must_be_listed(tmp_path):
    run = make_run(tmp_path)
    write(run, "03-test-execution.md", "Test validity: Valid\n")
    f = run / "09-go-no-go.md"
    f.write_text(block("Valid", {"SLA-1": "Fail"}, "No-go"))
    with pytest.raises(check_run.CheckFailed, match="SLA-2"):
        check_run.results(run, f)
    assert json.loads((run.parent / "facts.json").read_text())["sla_results"]["slas"]
