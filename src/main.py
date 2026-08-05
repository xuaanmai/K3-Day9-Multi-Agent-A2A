import sys
from pathlib import Path
from typing import Any, Dict

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.data_repository import DataRepository
from src.coordinator import Coordinator
from src.llm_client import LLMClient
from src.trace_writer import TraceWriter


def run_case(case_definition: Dict[str, Any], data_dir: str = "data") -> Dict[str, Any]:
    repository = DataRepository(data_dir=data_dir)
    trace_writer = TraceWriter(trace_file="trace.jsonl")
    llm_client = LLMClient()
    coordinator = Coordinator(
        data_repository=repository,
        trace_writer=trace_writer,
        llm_client=llm_client,
    )
    return coordinator.run(case_definition)


if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) != 2:
        raise SystemExit("Usage: python -m src.main <input_json_file>")

    path = Path(sys.argv[1])
    case_def = json.loads(path.read_text(encoding="utf-8"))
    output = run_case(case_def)
    print(json.dumps(output, ensure_ascii=False, indent=2))
