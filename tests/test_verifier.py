"""
Unit tests for VerifierAgent.
"""

from src.schemas import (
    CaseInput, CustomerRequest, CaseContext,
    OrderSellerAnalysis, PaymentAnalysis, PolicyResolution
)
from src.agents.verifier_agent import VerifierAgent


def test_verifier_agent_valid_payload():
    agent = VerifierAgent()
    case_input = CaseInput(
        case_id="EC_TEST",
        opened_at="2018-10-18T00:00:00-03:00",
        customer_request=CustomerRequest(
            language="vi",
            message="Test message",
            claimed_order_id="test_order_123"
        )
    )
    context = CaseContext(case_input=case_input)
    context.order_seller = OrderSellerAnalysis(
        order_id="test_order_123",
        order_status="delivered",
        item_ids=["item:test_order_123:1"],
        seller_ids=["seller_abc"],
        item_total_brl=100.0,
        freight_total_brl=15.0
    )
    context.payment = PaymentAnalysis(
        order_id="test_order_123",
        payment_ids=["payment:test_order_123:1"],
        payment_total_brl=115.0
    )
    context.policy = PolicyResolution(
        primary_issue="late_delivery_seller",
        case_status="action_required",
        confidence=0.92,
        ranked_causes=[{"cause_code": "SELLER_HANDOFF_AFTER_LIMIT", "rank": 1}],
        responsible_parties=[{"party_type": "seller", "party_id": "seller_abc"}],
        recommended_refund_brl=15.0,
        resolution_actions=["refund_freight"],
        evidence_ids=["order:test_order_123", "item:test_order_123:1"]
    )

    result = agent.process(context)
    assert result.success is True
    assert "assessment" in result.data
    assert result.data["assessment"]["primary_issue"] == "late_delivery_seller"
