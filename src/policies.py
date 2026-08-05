"""
EC_POLICY_V1 Policy Definitions and Mapping Engine.

Maps dispute issues to root causes, responsible parties, financial refund types,
and resolution actions according to priority rules (1 to 6).
"""

from typing import Dict, List, Any, Optional

# Primary Issue Codes
ISSUE_CANCELED_ORDER_PAID = "canceled_order_paid"
ISSUE_UNAVAILABLE_ORDER_PAID = "unavailable_order_paid"
ISSUE_LATE_DELIVERY_SELLER = "late_delivery_seller"
ISSUE_LATE_DELIVERY_LOGISTICS = "late_delivery_logistics"
ISSUE_VALID_SPLIT_PAYMENT = "valid_split_payment"
ISSUE_UNSUPPORTED_LATE_CLAIM = "unsupported_late_claim"

# Root Cause Codes
CAUSE_ORDER_CANCELED_AFTER_PAYMENT = "ORDER_CANCELED_AFTER_PAYMENT"
CAUSE_ORDER_UNAVAILABLE_AFTER_PAYMENT = "ORDER_UNAVAILABLE_AFTER_PAYMENT"
CAUSE_SELLER_HANDOFF_AFTER_LIMIT = "SELLER_HANDOFF_AFTER_LIMIT"
CAUSE_CARRIER_DELIVERED_AFTER_ESTIMATE = "CARRIER_DELIVERED_AFTER_ESTIMATE"
CAUSE_MULTIPLE_PAYMENTS_RECONCILED = "MULTIPLE_PAYMENTS_RECONCILED"
CAUSE_DELIVERY_WITHIN_ESTIMATE = "DELIVERY_WITHIN_ESTIMATE"

# Responsible Party Constant Identifiers
PLATFORM_PARTY_ID = "OLIST_PLATFORM"
LOGISTICS_PARTY_ID = "LOGISTICS_PROVIDER"

# Resolution Action Codes
ACTION_ISSUE_FULL_REFUND = "issue_full_refund"
ACTION_REFUND_FREIGHT = "refund_freight"
ACTION_EXPLAIN_VALID_SPLIT_PAYMENT = "explain_valid_split_payment"
ACTION_REJECT_LATE_REFUND = "reject_late_refund"

# Policy Evidence Formatter
def fmt_policy_evidence(cause_code: str) -> str:
    """Returns standardized evidence ID for policy rules."""
    return f"policy:{cause_code}"


# Mapping: primary_issue -> cause -> party -> refund_type -> action
POLICY_MAPPING: Dict[str, Dict[str, Any]] = {
    ISSUE_CANCELED_ORDER_PAID: {
        "priority": 1,
        "cause_code": CAUSE_ORDER_CANCELED_AFTER_PAYMENT,
        "party_type": "platform",
        "default_party_id": PLATFORM_PARTY_ID,
        "refund_type": "payment_total",
        "action": ACTION_ISSUE_FULL_REFUND,
        "case_status": "action_required",
        "description": "Canceled order with payment > 0"
    },
    ISSUE_UNAVAILABLE_ORDER_PAID: {
        "priority": 2,
        "cause_code": CAUSE_ORDER_UNAVAILABLE_AFTER_PAYMENT,
        "party_type": "platform",
        "default_party_id": PLATFORM_PARTY_ID,
        "refund_type": "payment_total",
        "action": ACTION_ISSUE_FULL_REFUND,
        "case_status": "action_required",
        "description": "Unavailable order with payment > 0"
    },
    ISSUE_LATE_DELIVERY_SELLER: {
        "priority": 3,
        "cause_code": CAUSE_SELLER_HANDOFF_AFTER_LIMIT,
        "party_type": "seller",
        "default_party_id": None,  # Dynamic seller_id from order item
        "refund_type": "freight_total",
        "action": ACTION_REFUND_FREIGHT,
        "case_status": "action_required",
        "description": "Late delivery due to seller handoff after shipping_limit_date"
    },
    ISSUE_LATE_DELIVERY_LOGISTICS: {
        "priority": 4,
        "cause_code": CAUSE_CARRIER_DELIVERED_AFTER_ESTIMATE,
        "party_type": "logistics_provider",
        "default_party_id": LOGISTICS_PARTY_ID,
        "refund_type": "freight_total",
        "action": ACTION_REFUND_FREIGHT,
        "case_status": "action_required",
        "description": "Late delivery due to carrier after seller handed off on time"
    },
    ISSUE_VALID_SPLIT_PAYMENT: {
        "priority": 5,
        "cause_code": CAUSE_MULTIPLE_PAYMENTS_RECONCILED,
        "party_type": None,
        "default_party_id": None,
        "refund_type": "zero",
        "action": ACTION_EXPLAIN_VALID_SPLIT_PAYMENT,
        "case_status": "no_action",
        "description": "Multiple payments reconciled with items + freight"
    },
    ISSUE_UNSUPPORTED_LATE_CLAIM: {
        "priority": 6,
        "cause_code": CAUSE_DELIVERY_WITHIN_ESTIMATE,
        "party_type": None,
        "default_party_id": None,
        "refund_type": "zero",
        "action": ACTION_REJECT_LATE_REFUND,
        "case_status": "no_action",
        "description": "Delivery delivered on or before estimated date"
    }
}


# Execution Priority Rules Table
POLICY_RULES: List[Dict[str, Any]] = [
    {
        "priority": 1,
        "condition_name": "Canceled và payment > 0",
        "primary_issue": ISSUE_CANCELED_ORDER_PAID,
        "cause_code": CAUSE_ORDER_CANCELED_AFTER_PAYMENT,
        "responsible_party_type": "platform",
        "responsible_party_id": PLATFORM_PARTY_ID,
        "refund_type": "Payment",
        "action": ACTION_ISSUE_FULL_REFUND,
        "case_status": "action_required"
    },
    {
        "priority": 2,
        "condition_name": "Unavailable và payment > 0",
        "primary_issue": ISSUE_UNAVAILABLE_ORDER_PAID,
        "cause_code": CAUSE_ORDER_UNAVAILABLE_AFTER_PAYMENT,
        "responsible_party_type": "platform",
        "responsible_party_id": PLATFORM_PARTY_ID,
        "refund_type": "Payment",
        "action": ACTION_ISSUE_FULL_REFUND,
        "case_status": "action_required"
    },
    {
        "priority": 3,
        "condition_name": "Giao trễ, seller bàn giao trễ",
        "primary_issue": ISSUE_LATE_DELIVERY_SELLER,
        "cause_code": CAUSE_SELLER_HANDOFF_AFTER_LIMIT,
        "responsible_party_type": "seller",
        "responsible_party_id": "<seller_id>",
        "refund_type": "Freight",
        "action": ACTION_REFUND_FREIGHT,
        "case_status": "action_required"
    },
    {
        "priority": 4,
        "condition_name": "Giao trễ, seller bàn giao đúng",
        "primary_issue": ISSUE_LATE_DELIVERY_LOGISTICS,
        "cause_code": CAUSE_CARRIER_DELIVERED_AFTER_ESTIMATE,
        "responsible_party_type": "logistics_provider",
        "responsible_party_id": LOGISTICS_PARTY_ID,
        "refund_type": "Freight",
        "action": ACTION_REFUND_FREIGHT,
        "case_status": "action_required"
    },
    {
        "priority": 5,
        "condition_name": ">= 2 payments và đối soát đúng",
        "primary_issue": ISSUE_VALID_SPLIT_PAYMENT,
        "cause_code": CAUSE_MULTIPLE_PAYMENTS_RECONCILED,
        "responsible_party_type": None,
        "responsible_party_id": None,
        "refund_type": "0",
        "action": ACTION_EXPLAIN_VALID_SPLIT_PAYMENT,
        "case_status": "no_action"
    },
    {
        "priority": 6,
        "condition_name": "Giao đúng hạn và payment đúng",
        "primary_issue": ISSUE_UNSUPPORTED_LATE_CLAIM,
        "cause_code": CAUSE_DELIVERY_WITHIN_ESTIMATE,
        "responsible_party_type": None,
        "responsible_party_id": None,
        "refund_type": "0",
        "action": ACTION_REJECT_LATE_REFUND,
        "case_status": "no_action"
    }
]
