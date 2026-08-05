"""Official CLI for the modular multi-agent pipeline. It never creates ZIP files."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict


ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.coordinator import Coordinator
from src.data_repository import DataRepository
from src.llm_client import LLMClient
from src.output_validator import EXPECTED_CASE_IDS, validate_output_directory
from src.trace_validator import validate_trace_file
from src.trace_writer import TraceWriter


def build_coordinator(
    *, data_dir: Path, trace_file: Path, deterministic: bool
) -> Coordinator:
    repository = DataRepository(data_dir=data_dir)
    llm_client = LLMClient(enabled=not deterministic)
    llm_client.assert_ready()
    return Coordinator(
        data_repository=repository,
        trace_writer=TraceWriter(trace_file=trace_file, reset=True),
        llm_client=llm_client,
    )


def run_case(
    case_definition: Dict[str, Any],
    data_dir: str | Path = "data",
    *,
    deterministic: bool = False,
    trace_file: str | Path = "trace.jsonl",
) -> Dict[str, Any]:
    coordinator = build_coordinator(
        data_dir=Path(data_dir),
        trace_file=Path(trace_file),
        deterministic=deterministic,
    )
    return coordinator.run(case_definition)


def run_all(
    *,
    input_dir: Path,
    output_dir: Path,
    data_dir: Path,
    trace_file: Path,
    deterministic: bool,
) -> Dict[str, Any]:
    coordinator = build_coordinator(
        data_dir=data_dir,
        trace_file=trace_file,
        deterministic=deterministic,
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    for case_id in EXPECTED_CASE_IDS:
        input_file = input_dir / f"{case_id}.json"
        case_definition = json.loads(input_file.read_text(encoding="utf-8"))
        output = coordinator.run(case_definition)
        (output_dir / f"{case_id}.json").write_text(
            json.dumps(output, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"[{case_id}] verified")

    output_report = validate_output_directory(
        output_dir, input_dir, coordinator.data_repository
    )
    if not output_report["valid"]:
        raise RuntimeError(f"Output validation failed: {output_report['errors']}")

    trace_report = validate_trace_file(trace_file, require_llm=not deterministic)
    if not trace_report["valid"]:
        raise RuntimeError(f"Trace validation failed: {trace_report['errors']}")
    return {"outputs": output_report, "trace": trace_report}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--all", action="store_true", help="Process EC_001 through EC_050")
    mode.add_argument("--case", type=Path, help="Process one input JSON and print output")
    parser.add_argument("--deterministic", action="store_true", help="Skip Ollama calls (tests only)")
    parser.add_argument("--data-dir", type=Path, default=ROOT_DIR / "data")
    parser.add_argument("--input-dir", type=Path, default=ROOT_DIR / "input")
    parser.add_argument("--output-dir", type=Path, default=ROOT_DIR / "output")
    parser.add_argument("--trace-file", type=Path, default=ROOT_DIR / "trace.jsonl")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.all:
        report = run_all(
            input_dir=args.input_dir,
            output_dir=args.output_dir,
            data_dir=args.data_dir,
            trace_file=args.trace_file,
            deterministic=args.deterministic,
        )
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        case_definition = json.loads(args.case.read_text(encoding="utf-8"))
        output = run_case(
            case_definition,
            args.data_dir,
            deterministic=args.deterministic,
            trace_file=args.trace_file,
        )
        print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
