"""
Unit tests for PolicyAgent.
"""

from src.schemas import (
    CaseInput, CustomerRequest, CaseContext,
    OrderSellerAnalysis, PaymentAnalysis, DeliveryAnalysis
)
from src.agents.policy_agent import PolicyAgent


def test_policy_agent_canceled_order():
    agent = PolicyAgent()
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
    context.order_seller = OrderSellerAnalysis(order_id="test_order_123", order_status="canceled")
    context.payment = PaymentAnalysis(order_id="test_order_123", payment_total_brl=150.0)

    result = agent.process(context)

    assert result.success is True
    assert context.policy is not None
    assert context.policy.primary_issue == "canceled_order_paid"
    assert context.policy.recommended_refund_brl == 150.0
    assert context.policy.case_status == "action_required"
