from typing import Dict

ISSUE_CANCELED_ORDER_PAID = "canceled_order_paid"
ISSUE_UNAVAILABLE_ORDER_PAID = "unavailable_order_paid"
ISSUE_LATE_DELIVERY_SELLER = "late_delivery_seller"
ISSUE_LATE_DELIVERY_LOGISTICS = "late_delivery_logistics"
ISSUE_VALID_SPLIT_PAYMENT = "valid_split_payment"
ISSUE_UNSUPPORTED_LATE_CLAIM = "unsupported_late_claim"

CAUSE_ORDER_CANCELED_AFTER_PAYMENT = "ORDER_CANCELED_AFTER_PAYMENT"
CAUSE_ORDER_UNAVAILABLE_AFTER_PAYMENT = "ORDER_UNAVAILABLE_AFTER_PAYMENT"
CAUSE_SELLER_HANDOFF_AFTER_LIMIT = "SELLER_HANDOFF_AFTER_LIMIT"
CAUSE_CARRIER_DELIVERED_AFTER_ESTIMATE = "CARRIER_DELIVERED_AFTER_ESTIMATE"
CAUSE_MULTIPLE_PAYMENTS_RECONCILED = "MULTIPLE_PAYMENTS_RECONCILED"
CAUSE_DELIVERY_WITHIN_ESTIMATE = "DELIVERY_WITHIN_ESTIMATE"

ACTION_ISSUE_FULL_REFUND = "issue_full_refund"
ACTION_REFUND_FREIGHT = "refund_freight"
ACTION_EXPLAIN_VALID_SPLIT_PAYMENT = "explain_valid_split_payment"
ACTION_REJECT_LATE_REFUND = "reject_late_refund"

PLATFORM_PARTY_ID = "OLIST_PLATFORM"
LOGISTICS_PARTY_ID = "LOGISTICS_PROVIDER"


def fmt_order_evidence(order_id: str) -> str:
    return f"order:{order_id}"


def fmt_item_evidence(order_id: str, item_id: int) -> str:
    return f"item:{order_id}:{item_id}"


def fmt_payment_evidence(order_id: str, sequence: int) -> str:
    return f"payment:{order_id}:{sequence}"


def fmt_seller_evidence(seller_id: str) -> str:
    return f"seller:{seller_id}"


def fmt_policy_evidence(cause_code: str) -> str:
    return f"policy:{cause_code}"
