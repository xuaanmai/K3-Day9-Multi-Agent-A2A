"""End-to-end test from a real input file through all agents to final output."""

import json
from pathlib import Path

from src.coordinator import Coordinator
from src.data_repository import DataRepository
from src.llm_client import LLMClient
from src.schemas import CaseOutput
from src.trace_writer import TraceWriter


ROOT = Path(__file__).resolve().parent.parent


def test_real_case_runs_from_input_to_verified_output(tmp_path):
    repository = DataRepository(data_dir=ROOT / "data")
    trace_path = tmp_path / "trace.jsonl"
    coordinator = Coordinator(
        data_repository=repository,
        trace_writer=TraceWriter(trace_file=trace_path),
        llm_client=LLMClient(enabled=False),
    )
    case_input = json.loads((ROOT / "input" / "EC_001.json").read_text(encoding="utf-8"))

    result = coordinator.run(case_input)
    validated = CaseOutput.model_validate(result)

    assert validated.case_id == "EC_001"
    assert "verification_errors" not in result
    assert validated.assessment.primary_issue == "late_delivery_seller"
    assert validated.financial_resolution.recommended_refund_brl == 12.04

    trace_lines = trace_path.read_text(encoding="utf-8").splitlines()
    assert len(trace_lines) == 6
    events = [json.loads(line) for line in trace_lines]
    assert all(event["case_id"] == "EC_001" for event in events)
    assert [event["agent"] for event in events] == [
        "CoordinatorAgent",
        "OrderSellerAgent",
        "PaymentAgent",
        "DeliveryAgent",
        "PolicyAgent",
        "VerifierAgent",
    ]
