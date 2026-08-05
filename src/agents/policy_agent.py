"""
Policy Agent.
Applies EC_POLICY_V1 business rules, evaluates root causes, responsible parties, financial refunds, and resolution actions.
"""

from typing import List, Dict, Any
from src.schemas import BaseAgent, CaseContext, AgentResult, PolicyResolution
from src import policies as pol


class PolicyAgent(BaseAgent):
    """Applies dispute resolution rules and determines final assessment."""

    def __init__(self):
        super().__init__(name="PolicyAgent")

    def process(self, context: CaseContext) -> AgentResult:
        order_seller = context.order_seller
        payment = context.payment
        delivery = context.delivery
        order_id = context.case_input.customer_request.claimed_order_id

        order_status = order_seller.order_status if order_seller else "unknown"
        payment_total = payment.payment_total_brl if payment else 0.0
        freight_total = order_seller.freight_total_brl if order_seller else 0.0

        primary_issue = ""
        cause_code = ""
        responsible_parties: List[Dict[str, Any]] = []
        recommended_refund = 0.0
        actions: List[str] = []
        case_status = "no_action"
        confidence = 0.95

        # 1. Canceled order paid
        if order_status == "canceled" and payment_total > 0:
            primary_issue = pol.ISSUE_CANCELED_ORDER_PAID
            cause_code = pol.CAUSE_ORDER_CANCELED_AFTER_PAYMENT
            responsible_parties.append({"party_type": "platform", "party_id": pol.PLATFORM_PARTY_ID})
            recommended_refund = payment_total
            actions.append(pol.ACTION_ISSUE_FULL_REFUND)
            case_status = "action_required"

        # 2. Unavailable order paid
        elif order_status == "unavailable" and payment_total > 0:
            primary_issue = pol.ISSUE_UNAVAILABLE_ORDER_PAID
            cause_code = pol.CAUSE_ORDER_UNAVAILABLE_AFTER_PAYMENT
            responsible_parties.append({"party_type": "platform", "party_id": pol.PLATFORM_PARTY_ID})
            recommended_refund = payment_total
            actions.append(pol.ACTION_ISSUE_FULL_REFUND)
            case_status = "action_required"

        # 3. Late delivery seller
        elif delivery and delivery.is_delivered_late and order_seller and order_seller.is_seller_late:
            primary_issue = pol.ISSUE_LATE_DELIVERY_SELLER
            cause_code = pol.CAUSE_SELLER_HANDOFF_AFTER_LIMIT
            seller_id = order_seller.seller_ids[0] if order_seller.seller_ids else "unknown_seller"
            responsible_parties.append({"party_type": "seller", "party_id": seller_id})
            recommended_refund = freight_total
            actions.append(pol.ACTION_REFUND_FREIGHT)
            case_status = "action_required"

        # 4. Late delivery logistics
        elif delivery and delivery.is_delivered_late and (not order_seller or not order_seller.is_seller_late):
            primary_issue = pol.ISSUE_LATE_DELIVERY_LOGISTICS
            cause_code = pol.CAUSE_CARRIER_DELIVERED_AFTER_ESTIMATE
            responsible_parties.append({"party_type": "logistics_provider", "party_id": pol.LOGISTICS_PARTY_ID})
            recommended_refund = freight_total
            actions.append(pol.ACTION_REFUND_FREIGHT)
            case_status = "action_required"

        # 5. Valid split payment
        elif payment and payment.is_split_payment and payment.reconciled_with_items:
            primary_issue = pol.ISSUE_VALID_SPLIT_PAYMENT
            cause_code = pol.CAUSE_MULTIPLE_PAYMENTS_RECONCILED
            recommended_refund = 0.0
            actions.append(pol.ACTION_EXPLAIN_VALID_SPLIT_PAYMENT)
            case_status = "no_action"

        # 6. Unsupported late claim (default / delivery within estimate)
        else:
            primary_issue = pol.ISSUE_UNSUPPORTED_LATE_CLAIM
            cause_code = pol.CAUSE_DELIVERY_WITHIN_ESTIMATE
            recommended_refund = 0.0
            actions.append(pol.ACTION_REJECT_LATE_REFUND)
            case_status = "no_action"

        # Construct evidence IDs list
        evidence_ids: List[str] = []
        if order_seller:
            evidence_ids.extend(order_seller.evidence_ids)
        if payment:
            # add payments evidence avoiding duplicates
            for p_ev in payment.evidence_ids:
                if p_ev not in evidence_ids:
                    evidence_ids.append(p_ev)
        
        # Policy evidence
        policy_ev = pol.fmt_policy_evidence(cause_code)
        if policy_ev not in evidence_ids:
            evidence_ids.append(policy_ev)

        # Filter unique preserving order
        unique_ev: List[str] = []
        for ev in evidence_ids:
            if ev not in unique_ev:
                unique_ev.append(ev)

        resolution = PolicyResolution(
            primary_issue=primary_issue,
            case_status=case_status,
            confidence=confidence,
            ranked_causes=[{"cause_code": cause_code, "rank": 1}],
            responsible_parties=responsible_parties,
            recommended_refund_brl=round(recommended_refund, 2),
            resolution_actions=actions,
            evidence_ids=unique_ev[:10]  # Cap at max 10
        )

        context.policy = resolution

        return AgentResult(
            agent_name=self.name,
            success=True,
            data={
                "primary_issue": primary_issue,
                "case_status": case_status,
                "recommended_refund_brl": resolution.recommended_refund_brl,
                "actions": actions
            }
        )
