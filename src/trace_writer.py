"""JSONL trace writer. A new instance starts a fresh run by default."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


class TraceWriter:
    def __init__(self, trace_file: str = "trace.jsonl", *, reset: bool = True):
        self.trace_file = Path(trace_file)
        self.trace_file.parent.mkdir(parents=True, exist_ok=True)
        if reset:
            self.trace_file.write_text("", encoding="utf-8")

    def write_event(
        self,
        *,
        case_id: str,
        agent: str,
        model: str,
        parameter_size: str,
        provider: str,
        action: str,
        details: Dict[str, Any],
        llm_result: Dict[str, Any],
    ) -> None:
        event = {
            "case_id": case_id,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "agent": agent,
            "model": model,
            "parameter_size": parameter_size,
            "provider": provider,
            "action": action,
            "llm_invoked": llm_result.get("invoked", False),
            "llm_success": llm_result.get("success", False),
            "llm_summary": llm_result.get("summary", ""),
            "details": details,
        }
        with self.trace_file.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")

    def write(self, trace: Dict[str, Any]) -> None:
        """Backward-compatible raw writer for non-official diagnostics."""
        with self.trace_file.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(trace, ensure_ascii=False) + "\n")
