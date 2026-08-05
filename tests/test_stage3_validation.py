"""Tests for the 50-output and latest-trace validation gates."""

from pathlib import Path

from src.data_repository import DataRepository
from src.output_validator import validate_output_directory
from src.trace_validator import validate_trace_file


ROOT = Path(__file__).resolve().parent.parent


def test_all_50_repository_outputs_are_valid():
    report = validate_output_directory(
        ROOT / "output", ROOT / "input", DataRepository(ROOT / "data")
    )
    assert report["valid"] is True, report["errors"]
    assert report["valid_count"] == 50
    assert report["error_count"] == 0


def test_missing_outputs_fail_batch_gate(tmp_path):
    report = validate_output_directory(
        tmp_path / "output", tmp_path / "input", DataRepository(ROOT / "data")
    )
    assert report["valid"] is False
    assert report["valid_count"] == 0
    assert {error["code"] for error in report["errors"]} == {"MISSING_OUTPUT"}


def test_latest_repository_trace_is_valid():
    report = validate_trace_file(ROOT / "trace.jsonl", require_llm=False)
    assert report["valid"] is True, report["errors"]
    assert report["line_count"] == 300
    assert report["case_count"] == 50


def test_malformed_trace_fails_gate(tmp_path):
    trace = tmp_path / "trace.jsonl"
    trace.write_text('{"case_id":"EC_001"}\nnot-json\n', encoding="utf-8")
    report = validate_trace_file(trace)
    codes = {error["code"] for error in report["errors"]}
    assert report["valid"] is False
    assert "TRACE_FIELDS_MISSING" in codes
    assert "INVALID_TRACE_JSON" in codes
