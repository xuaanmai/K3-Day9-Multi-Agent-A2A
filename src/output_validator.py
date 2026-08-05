"""Batch validation for the 50 official case outputs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from src.agents.verifier_agent import VerifierAgent


EXPECTED_CASE_IDS = [f"EC_{index:03d}" for index in range(1, 51)]


def validate_output_directory(
    output_dir: str | Path,
    input_dir: str | Path,
    data_repository: Any,
) -> Dict[str, Any]:
    """Validate file coverage, JSON parsing, case mapping and CSV-backed content."""

    output_path = Path(output_dir)
    input_path = Path(input_dir)
    verifier = VerifierAgent(data_repository)
    errors: List[Dict[str, str]] = []
    valid_cases: List[str] = []

    actual_names = {path.name for path in output_path.glob("*.json")}
    expected_names = {f"{case_id}.json" for case_id in EXPECTED_CASE_IDS}

    for missing in sorted(expected_names - actual_names):
        errors.append({"file": missing, "code": "MISSING_OUTPUT", "message": "Thiếu output."})
    for extra in sorted(actual_names - expected_names):
        errors.append({"file": extra, "code": "UNEXPECTED_OUTPUT", "message": "Output không thuộc 50 case."})

    for case_id in EXPECTED_CASE_IDS:
        name = f"{case_id}.json"
        output_file = output_path / name
        input_file = input_path / name
        if not output_file.exists():
            continue
        if not input_file.exists():
            errors.append({"file": name, "code": "MISSING_INPUT", "message": "Không có input tương ứng."})
            continue

        try:
            payload = json.loads(output_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append({"file": name, "code": "INVALID_JSON", "message": str(exc)})
            continue

        if payload.get("case_id") != case_id:
            errors.append({
                "file": name,
                "code": "CASE_ID_MISMATCH",
                "message": f"case_id phải là {case_id}.",
            })
            continue

        result = verifier.validate_payload(payload)
        if result.valid:
            valid_cases.append(case_id)
        else:
            errors.extend({
                "file": name,
                "code": error.code,
                "message": f"{error.field}: {error.message}",
            } for error in result.errors)

    return {
        "valid": not errors and len(valid_cases) == 50,
        "expected_count": 50,
        "valid_count": len(valid_cases),
        "error_count": len(errors),
        "errors": errors,
    }
