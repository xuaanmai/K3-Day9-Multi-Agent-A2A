"""
Unit tests for DeliveryAgent.
"""

from src.schemas import CaseInput, CustomerRequest, CaseContext
from src.agents.delivery_agent import DeliveryAgent


def test_delivery_agent_late_delivery():
    agent = DeliveryAgent()
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
        "order_row": {
            "order_id": "test_order_123",
            "order_delivered_customer_date": "2018-10-20 10:00:00",
            "order_estimated_delivery_date": "2018-10-15 10:00:00"
        }
    }
    context = CaseContext(case_input=case_input, raw_data=raw_data)
    result = agent.process(context)

    assert result.success is True
    assert context.delivery is not None
    assert context.delivery.is_delivered_late is True
