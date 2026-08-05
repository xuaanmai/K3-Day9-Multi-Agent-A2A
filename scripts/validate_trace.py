"""Validate trace.jsonl for 50 cases and six ordered agent events per case."""

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.trace_validator import validate_trace_file


def main() -> int:
    report = validate_trace_file(ROOT / "trace.jsonl")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
