"""
Verifier Agent.
Audits final assessment, entity lists, evidence formatting, financial totals, bounds, and builds final JSON payload.
"""

from typing import Dict, Any, List
from src.schemas import BaseAgent, CaseContext, AgentResult


class VerifierAgent(BaseAgent):
    """Verifies compliance of final case assessment with output schema constraints."""

    def __init__(self):
        super().__init__(name="VerifierAgent")

    def process(self, context: CaseContext) -> AgentResult:
        errors: List[str] = []

        case_id = context.case_input.case_id
        order_id = context.case_input.customer_request.claimed_order_id

        order_seller = context.order_seller
        payment = context.payment
        policy = context.policy

        order_ids = [order_id] if order_id else []
        item_ids = order_seller.item_ids if order_seller else []
        seller_ids = order_seller.seller_ids if order_seller else []
        payment_ids = payment.payment_ids if payment else []

        item_total = order_seller.item_total_brl if order_seller else 0.0
        freight_total = order_seller.freight_total_brl if order_seller else 0.0
        payment_total = payment.payment_total_brl if payment else 0.0

        primary_issue = policy.primary_issue if policy else "unsupported_late_claim"
        case_status = policy.case_status if policy else "no_action"
        confidence = policy.confidence if policy else 0.90
        ranked_causes = policy.ranked_causes if policy else []
        responsible_parties = policy.responsible_parties if policy else []
        recommended_refund = policy.recommended_refund_brl if policy else 0.0
        resolution_actions = policy.resolution_actions if policy else []
        evidence_ids = policy.evidence_ids if policy else []

        # Validate bounds & cap if needed
        order_ids = order_ids[:5]
        item_ids = item_ids[:5]
        seller_ids = seller_ids[:5]
        payment_ids = payment_ids[:5]
        evidence_ids = evidence_ids[:10]
        ranked_causes = ranked_causes[:3]
        responsible_parties = responsible_parties[:3]
        resolution_actions = resolution_actions[:5]

        if not (0.0 <= confidence <= 1.0):
            errors.append(f"Confidence {confidence} out of range [0, 1]")
            confidence = max(0.0, min(1.0, confidence))

        if recommended_refund > 0.0 and case_status != "action_required":
            errors.append("case_status should be 'action_required' when refund > 0")
            case_status = "action_required"

        final_payload: Dict[str, Any] = {
            "case_id": case_id,
            "assessment": {
                "primary_issue": primary_issue,
                "case_status": case_status,
                "confidence": round(confidence, 2)
            },
            "affected_entities": {
                "order_ids": order_ids,
                "item_ids": item_ids,
                "seller_ids": seller_ids,
                "payment_ids": payment_ids
            },
            "root_cause_analysis": {
                "ranked_causes": ranked_causes,
                "responsible_parties": responsible_parties
            },
            "evidence_ids": evidence_ids,
            "financial_resolution": {
                "currency": "BRL",
                "item_total_brl": round(item_total, 2),
                "freight_total_brl": round(freight_total, 2),
                "payment_total_brl": round(payment_total, 2),
                "recommended_refund_brl": round(recommended_refund, 2)
            },
            "resolution_actions": resolution_actions
        }

        context.verification_errors = errors

        return AgentResult(
            agent_name=self.name,
            success=len(errors) == 0,
            data=final_payload,
            error_message="; ".join(errors) if errors else None
        )
