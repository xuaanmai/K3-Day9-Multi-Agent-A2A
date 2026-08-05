"""Deterministic payment reconciliation agent."""

from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from src.schemas import AgentResult, BaseAgent, CaseContext, Payment, PaymentAnalysis


CENT = Decimal("0.01")
MATCH_TOLERANCE = Decimal("0.10")


def _decimal(value: Any) -> Decimal:
    """Convert source money to Decimal without passing through binary float math."""
    if value is None or value == "":
        return Decimal("0")
    return Decimal(str(value))


def _money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


class PaymentAgent(BaseAgent):
    """Audits order payment records and reconciles with item + freight totals."""

    def __init__(self):
        super().__init__(name="PaymentAgent")

    def process(self, context: CaseContext) -> AgentResult:
        order_id = context.case_input.customer_request.claimed_order_id
        raw_payments = context.raw_data.get("payments") or []
        payments_for_order = [row for row in raw_payments if row.get("order_id") == order_id]
        payments_for_order.sort(key=lambda row: int(row["payment_sequential"]))

        payment_total = _money(
            sum((_decimal(row.get("payment_value")) for row in payments_for_order), Decimal("0"))
        )
        item_total = _decimal(context.order_seller.item_total_brl if context.order_seller else 0)
        freight_total = _decimal(context.order_seller.freight_total_brl if context.order_seller else 0)
        expected_total = _money(item_total + freight_total)
        difference = _money(abs(payment_total - expected_total))

        payments = [
            Payment(
                payment_sequential=int(row["payment_sequential"]),
                payment_type=str(row.get("payment_type") or ""),
                payment_value_brl=float(_money(_decimal(row.get("payment_value")))),
            )
            for row in payments_for_order
        ]
        payment_ids = [f"{order_id}:{payment.payment_sequential}" for payment in payments]
        payment_row_count = len(payments)

        analysis = PaymentAnalysis(
            order_id=order_id,
            payments=payments,
            payment_ids=payment_ids,
            payment_row_count=payment_row_count,
            payment_total_brl=float(payment_total),
            expected_total_brl=float(expected_total),
            difference_brl=float(difference),
            payment_matches=difference <= MATCH_TOLERANCE,
            is_split_payment=payment_row_count >= 2,
        )
        context.payment = analysis

        return AgentResult(
            agent_name=self.name,
            success=True,
            data=analysis.to_dict(),
        )
