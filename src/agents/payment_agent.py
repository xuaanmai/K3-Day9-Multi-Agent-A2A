"""
Payment Domain Agent.
Responsible for auditing payment transactions, split payment reconciliation, and total payment value checks.
"""

from typing import List
from src.schemas import BaseAgent, CaseContext, AgentResult, PaymentAnalysis
from src.policies import fmt_payment_evidence


class PaymentAgent(BaseAgent):
    """Audits order payment records and reconciles with item + freight totals."""

    def __init__(self):
        super().__init__(name="PaymentAgent")

    def process(self, context: CaseContext) -> AgentResult:
        order_id = context.case_input.customer_request.claimed_order_id
        raw_data = context.raw_data
        payments = raw_data.get("payments") or []

        payment_ids: List[str] = []
        evidence_ids: List[str] = []
        payment_total_brl = 0.0

        for pay in payments:
            seq = pay.get("payment_sequential")
            p_val = float(pay.get("payment_value", 0.0))
            payment_total_brl += p_val

            if seq is not None:
                p_id = fmt_payment_evidence(order_id, seq)
                payment_ids.append(p_id)
                evidence_ids.append(p_id)

        payment_total_brl = round(payment_total_brl, 2)
        payment_count = len(payments)
        is_split = payment_count >= 2

        # Reconcile with order items + freight if order_seller analysis exists
        item_total = context.order_seller.item_total_brl if context.order_seller else 0.0
        freight_total = context.order_seller.freight_total_brl if context.order_seller else 0.0
        expected_total = round(item_total + freight_total, 2)
        
        diff = abs(payment_total_brl - expected_total)
        reconciled = diff <= 0.10

        analysis = PaymentAnalysis(
            order_id=order_id,
            payment_ids=payment_ids,
            payment_total_brl=payment_total_brl,
            payment_count=payment_count,
            is_split_payment=is_split,
            reconciled_with_items=reconciled,
            payment_diff_brl=round(diff, 2),
            evidence_ids=evidence_ids
        )

        context.payment = analysis

        return AgentResult(
            agent_name=self.name,
            success=True,
            data={
                "payment_count": payment_count,
                "payment_total_brl": payment_total_brl,
                "is_split_payment": is_split,
                "reconciled_with_items": reconciled,
                "diff_brl": round(diff, 2)
            }
        )
