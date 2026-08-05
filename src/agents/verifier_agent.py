"""
Verifier Agent.
Audits final assessment, entity lists, evidence formatting, financial totals, bounds, and builds final JSON payload.
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, List, Optional, Tuple

from pydantic import ValidationError

from src.schemas import (
    AgentResult,
    BaseAgent,
    CaseContext,
    CaseOutput,
    VerificationError,
    VerificationResult,
)


class VerifierAgent(BaseAgent):
    """Verifies compliance of final case assessment with output schema constraints."""

    def __init__(self, data_repository: Optional[Any] = None):
        super().__init__(name="VerifierAgent")
        self.data_repository = data_repository

    def validate_payload(
        self, payload: Dict[str, Any], data_repository: Optional[Any] = None
    ) -> VerificationResult:
        """Validate schema, source-backed entities, totals and policy refund."""

        try:
            output = CaseOutput.model_validate(payload)
        except ValidationError as exc:
            errors = [
                VerificationError(
                    code=str(error["type"]).upper(),
                    field=".".join(str(part) for part in error["loc"]),
                    message=str(error["msg"]),
                )
                for error in exc.errors()
            ]
            return VerificationResult(valid=False, errors=errors)

        repository = data_repository or self.data_repository
        if repository is None:
            return VerificationResult(
                valid=True,
                warnings=["DataRepository chưa được cung cấp; bỏ qua kiểm chứng CSV."],
            )

        errors = self._validate_against_repository(output, repository)
        return VerificationResult(valid=not errors, errors=errors)

    @staticmethod
    def _money(value: Any) -> Decimal:
        return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @staticmethod
    def _split_scoped_id(value: str) -> Optional[Tuple[str, int]]:
        try:
            order_id, sequence = value.rsplit(":", 1)
            return order_id, int(sequence)
        except (AttributeError, TypeError, ValueError):
            return None

    @staticmethod
    def _error(code: str, field: str, message: str) -> VerificationError:
        return VerificationError(code=code, field=field, message=message)

    def _validate_against_repository(
        self, output: CaseOutput, repository: Any
    ) -> List[VerificationError]:
        errors: List[VerificationError] = []
        entities = output.affected_entities

        for index, order_id in enumerate(entities.order_ids):
            if not repository.get_order(order_id):
                errors.append(self._error(
                    "ORDER_NOT_FOUND",
                    f"affected_entities.order_ids.{index}",
                    f"Order không tồn tại trong CSV: {order_id}",
                ))

        for index, item_id in enumerate(entities.item_ids):
            parsed = self._split_scoped_id(item_id)
            if parsed is None or not repository.item_exists(*parsed):
                errors.append(self._error(
                    "ITEM_NOT_FOUND",
                    f"affected_entities.item_ids.{index}",
                    f"Item không tồn tại trong CSV: {item_id}",
                ))

        for index, seller_id in enumerate(entities.seller_ids):
            if not repository.seller_exists(seller_id):
                errors.append(self._error(
                    "SELLER_NOT_FOUND",
                    f"affected_entities.seller_ids.{index}",
                    f"Seller không tồn tại trong CSV: {seller_id}",
                ))

        for index, payment_id in enumerate(entities.payment_ids):
            parsed = self._split_scoped_id(payment_id)
            if parsed is None or not repository.payment_exists(*parsed):
                errors.append(self._error(
                    "PAYMENT_NOT_FOUND",
                    f"affected_entities.payment_ids.{index}",
                    f"Payment không tồn tại trong CSV: {payment_id}",
                ))

        # The financial totals are recomputed from every affected order.
        source_items = []
        source_payments = []
        for order_id in entities.order_ids:
            source_items.extend(repository.get_order_items(order_id))
            source_payments.extend(repository.get_order_payments(order_id))

        item_total = self._money(sum(
            (Decimal(str(row.get("price") or 0)) for row in source_items),
            Decimal("0"),
        ))
        freight_total = self._money(sum(
            (Decimal(str(row.get("freight_value") or 0)) for row in source_items),
            Decimal("0"),
        ))
        payment_total = self._money(sum(
            (Decimal(str(row.get("payment_value") or 0)) for row in source_payments),
            Decimal("0"),
        ))

        financial = output.financial_resolution
        total_checks = (
            ("ITEM_TOTAL_MISMATCH", "item_total_brl", financial.item_total_brl, item_total),
            ("FREIGHT_TOTAL_MISMATCH", "freight_total_brl", financial.freight_total_brl, freight_total),
            ("PAYMENT_TOTAL_MISMATCH", "payment_total_brl", financial.payment_total_brl, payment_total),
        )
        for code, field, actual, expected in total_checks:
            if self._money(actual) != expected:
                errors.append(self._error(
                    code,
                    f"financial_resolution.{field}",
                    f"Giá trị {actual:.2f} không khớp CSV; phải là {expected:.2f}",
                ))

        issue = output.assessment.primary_issue
        if issue in {"canceled_order_paid", "unavailable_order_paid"}:
            expected_refund = payment_total
        elif issue in {"late_delivery_seller", "late_delivery_logistics"}:
            expected_refund = freight_total
        else:
            expected_refund = Decimal("0.00")

        if self._money(financial.recommended_refund_brl) != expected_refund:
            errors.append(self._error(
                "REFUND_POLICY_MISMATCH",
                "financial_resolution.recommended_refund_brl",
                f"Refund không đúng policy; phải là {expected_refund:.2f}",
            ))

        expected_status = "action_required" if expected_refund > 0 else "no_action"
        if output.assessment.case_status != expected_status:
            errors.append(self._error(
                "CASE_STATUS_MISMATCH",
                "assessment.case_status",
                f"case_status phải là {expected_status} theo refund",
            ))

        return errors

    def process(self, context: CaseContext) -> AgentResult:
        errors: List[str] = []

        case_id = context.case_input.case_id
        order_id = context.case_input.customer_request.claimed_order_id

        order_seller = context.order_seller
        payment = context.payment
        policy = context.policy

        order_ids = [order_id] if order_id else []
        item_ids = order_seller.item_ids if order_seller else []
        # Older OrderSellerAgent versions used evidence IDs in the entity set.
        item_ids = [value[5:] if value.startswith("item:") else value for value in item_ids]
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

        if not (0.0 <= confidence <= 1.0):
            errors.append(f"Confidence {confidence} out of range [0, 1]")

        if recommended_refund > 0.0 and case_status != "action_required":
            errors.append("case_status should be 'action_required' when refund > 0")
        if recommended_refund == 0.0 and case_status != "no_action":
            errors.append("case_status should be 'no_action' when refund is 0")

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

        verification = self.validate_payload(final_payload)
        errors.extend(f"{error.code}: {error.message}" for error in verification.errors)
        context.verification_errors = errors

        return AgentResult(
            agent_name=self.name,
            success=len(errors) == 0,
            data=final_payload,
            error_message="; ".join(errors) if errors else None
        )
