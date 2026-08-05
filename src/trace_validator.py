"""Validation for the latest real 50-case multi-agent JSONL trace."""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from src.output_validator import EXPECTED_CASE_IDS


EXPECTED_AGENT_ORDER = [
    "CoordinatorAgent",
    "OrderSellerAgent",
    "PaymentAgent",
    "DeliveryAgent",
    "PolicyAgent",
    "VerifierAgent",
]
REQUIRED_FIELDS = {
    "case_id", "timestamp", "agent", "model", "parameter_size", "provider",
    "action", "llm_invoked", "llm_success", "llm_summary", "details",
}


def validate_trace_file(
    trace_file: str | Path, *, require_llm: bool = True
) -> Dict[str, Any]:
    path = Path(trace_file)
    errors: List[Dict[str, Any]] = []
    events_by_case: Dict[str, List[str]] = defaultdict(list)
    line_count = 0

    if not path.exists():
        return {
            "valid": False,
            "line_count": 0,
            "case_count": 0,
            "error_count": 1,
            "errors": [{"line": 0, "code": "TRACE_NOT_FOUND", "message": str(path)}],
        }

    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw_line.strip():
            errors.append({"line": line_number, "code": "EMPTY_TRACE_LINE", "message": "Dòng rỗng."})
            continue
        line_count += 1
        try:
            event = json.loads(raw_line)
        except json.JSONDecodeError as exc:
            errors.append({"line": line_number, "code": "INVALID_TRACE_JSON", "message": str(exc)})
            continue

        missing = REQUIRED_FIELDS - set(event)
        if missing:
            errors.append({
                "line": line_number,
                "code": "TRACE_FIELDS_MISSING",
                "message": f"Thiếu: {sorted(missing)}",
            })
            continue
        if not isinstance(event["details"], dict):
            errors.append({"line": line_number, "code": "INVALID_TRACE_DETAILS", "message": "details phải là object."})
        if not isinstance(event["model"], str) or not event["model"].strip():
            errors.append({"line": line_number, "code": "INVALID_TRACE_MODEL", "message": "model bị trống."})
        if require_llm and event["llm_invoked"] is not True:
            errors.append({"line": line_number, "code": "LLM_NOT_INVOKED", "message": event["agent"]})
        if event["llm_success"] is not True:
            errors.append({"line": line_number, "code": "LLM_CALL_FAILED", "message": event["agent"]})
        try:
            datetime.fromisoformat(str(event["timestamp"]).replace("Z", "+00:00"))
        except ValueError:
            errors.append({"line": line_number, "code": "INVALID_TRACE_TIMESTAMP", "message": str(event["timestamp"])})

        case_id = event["case_id"]
        if case_id not in EXPECTED_CASE_IDS:
            errors.append({"line": line_number, "code": "UNEXPECTED_TRACE_CASE", "message": str(case_id)})
        events_by_case[case_id].append(event["agent"])

    for case_id in EXPECTED_CASE_IDS:
        agents = events_by_case.get(case_id, [])
        if agents != EXPECTED_AGENT_ORDER:
            errors.append({
                "line": 0,
                "code": "TRACE_AGENT_SEQUENCE_MISMATCH",
                "message": f"{case_id}: expected {EXPECTED_AGENT_ORDER}, received {agents}",
            })

    unexpected_cases = sorted(set(events_by_case) - set(EXPECTED_CASE_IDS))
    return {
        "valid": not errors and line_count == 300,
        "line_count": line_count,
        "expected_line_count": 300,
        "case_count": len(set(events_by_case) - set(unexpected_cases)),
        "error_count": len(errors),
        "errors": errors,
    }
