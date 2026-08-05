"""
End-to-end integration tests for Coordinator and full multi-agent pipeline.
"""

from src.data_repository import DataRepository
from src.trace_writer import TraceWriter
from src.llm_client import LLMClient
from src.coordinator import Coordinator


def test_coordinator_end_to_end_mock():
    repo = DataRepository(data_dir="data")
    trace_writer = TraceWriter(trace_file="trace.jsonl")
    llm_client = LLMClient()

    coordinator = Coordinator(data_repository=repo, trace_writer=trace_writer, llm_client=llm_client)

    sample_case = {
        "case_id": "EC_TEST_E2E",
        "opened_at": "2018-10-18T00:00:00-03:00",
        "customer_request": {
            "language": "vi",
            "message": "Đơn hàng của tôi bị chậm giao.",
            "claimed_order_id": "non_existent_order_id"
        },
        "policy_version": "EC_POLICY_V1"
    }

    result = coordinator.run(sample_case)

    assert "case_id" in result
    assert result["case_id"] == "EC_TEST_E2E"
    assert "assessment" in result
    assert "financial_resolution" in result
