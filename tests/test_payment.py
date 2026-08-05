"""
Unit tests for PaymentAgent.
"""

from src.schemas import CaseInput, CustomerRequest, CaseContext, OrderSellerAnalysis
from src.agents.payment_agent import PaymentAgent


def test_payment_agent_reconciliation():
    agent = PaymentAgent()
    case_input = CaseInput(
        case_id="EC_TEST",
        opened_at="2018-10-18T00:00:00-03:00",
        customer_request=CustomerRequest(
            language="vi",
            message="Test message",
            claimed_order_id="test_order_123"
        )
    )
    raw_data = {
        "payments": [
            {"payment_sequential": 1, "payment_value": 30.0},
            {"payment_sequential": 2, "payment_value": 30.0}
        ]
    }
    context = CaseContext(case_input=case_input, raw_data=raw_data)
    context.order_seller = OrderSellerAnalysis(
        order_id="test_order_123",
        order_status="delivered",
        item_total_brl=50.0,
        freight_total_brl=10.0
    )

    result = agent.process(context)

    assert result.success is True
    assert context.payment is not None
    assert context.payment.is_split_payment is True
    assert context.payment.payment_total_brl == 60.0
    assert context.payment.reconciled_with_items is True
