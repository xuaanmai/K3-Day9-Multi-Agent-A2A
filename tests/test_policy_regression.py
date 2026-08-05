"""Regression lock for EC_POLICY_V1 decisions and priority order."""

import pytest

from src.agents.policy_agent import PolicyAgent
from src.schemas import (
    CaseContext,
    CaseInput,
    CustomerRequest,
    DeliveryAnalysis,
    OrderSellerAnalysis,
    PaymentAnalysis,
)


def make_context(status="delivered", payment_total=115.0, *, late=False, seller_late=False, split=False):
    order_id = "regression-order"
    context = CaseContext(
        case_input=CaseInput(
            case_id="EC_REGRESSION",
            opened_at="2018-01-01T00:00:00-03:00",
            customer_request=CustomerRequest(
                language="vi", message="Regression", claimed_order_id=order_id
            ),
        )
    )
    context.order_seller = OrderSellerAnalysis(
        order_id=order_id,
        order_status=status,
        seller_ids=["seller-001"],
        item_total_brl=100.0,
        freight_total_brl=15.0,
        is_seller_late=seller_late,
        evidence_ids=[f"order:{order_id}"],
    )
    context.payment = PaymentAnalysis(
        order_id=order_id,
        payment_total_brl=payment_total,
        payment_row_count=2 if split else 1,
        payment_matches=True,
        is_split_payment=split,
    )
    context.delivery = DeliveryAnalysis(order_id=order_id, is_delivered_late=late)
    return context


@pytest.mark.parametrize(
    ("context", "issue", "cause", "refund", "action"),
    [
        (make_context("canceled"), "canceled_order_paid", "ORDER_CANCELED_AFTER_PAYMENT", 115.0, "issue_full_refund"),
        (make_context("unavailable"), "unavailable_order_paid", "ORDER_UNAVAILABLE_AFTER_PAYMENT", 115.0, "issue_full_refund"),
        (make_context(late=True, seller_late=True), "late_delivery_seller", "SELLER_HANDOFF_AFTER_LIMIT", 15.0, "refund_freight"),
        (make_context(late=True), "late_delivery_logistics", "CARRIER_DELIVERED_AFTER_ESTIMATE", 15.0, "refund_freight"),
        (make_context(split=True), "valid_split_payment", "MULTIPLE_PAYMENTS_RECONCILED", 0.0, "explain_valid_split_payment"),
        (make_context(), "unsupported_late_claim", "DELIVERY_WITHIN_ESTIMATE", 0.0, "reject_late_refund"),
    ],
)
def test_all_policy_decisions_remain_stable(context, issue, cause, refund, action):
    PolicyAgent().process(context)
    decision = context.policy

    assert decision is not None
    assert decision.primary_issue == issue
    assert decision.ranked_causes[0]["cause_code"] == cause
    assert decision.recommended_refund_brl == refund
    assert decision.resolution_actions == [action]


def test_canceled_rule_keeps_priority_over_late_delivery():
    context = make_context("canceled", late=True, seller_late=True)
    PolicyAgent().process(context)
    assert context.policy.primary_issue == "canceled_order_paid"
