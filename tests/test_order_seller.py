"""
Unit tests for OrderSellerAgent.
"""

from src.schemas import CaseInput, CustomerRequest, CaseContext
from src.agents.order_seller_agent import OrderSellerAgent


def test_order_seller_agent_process():
    agent = OrderSellerAgent()
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
            "order_status": "delivered",
            "order_delivered_carrier_date": "2018-10-10 10:00:00"
        },
        "items": [
            {
                "order_id": "test_order_123",
                "order_item_id": 1,
                "seller_id": "seller_abc",
                "price": 50.0,
                "freight_value": 10.0,
                "shipping_limit_date": "2018-10-08 10:00:00"
            }
        ]
    }
    context = CaseContext(case_input=case_input, raw_data=raw_data)
    result = agent.process(context)

    assert result.success is True
    assert context.order_seller is not None
    assert context.order_seller.is_seller_late is True
    assert context.order_seller.item_total_brl == 50.0
    assert context.order_seller.freight_total_brl == 10.0
