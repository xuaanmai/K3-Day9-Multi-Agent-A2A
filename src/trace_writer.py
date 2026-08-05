import json
from pathlib import Path
from typing import Any, Dict


class TraceWriter:
    def __init__(self, trace_file: str = "trace.jsonl"):
        self.trace_file = Path(trace_file)
        self.trace_file.parent.mkdir(parents=True, exist_ok=True)
        self.trace_file.write_text("", encoding="utf-8")

    def write(self, trace: Dict[str, Any]) -> None:
        with self.trace_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(trace, ensure_ascii=False) + "\n")
