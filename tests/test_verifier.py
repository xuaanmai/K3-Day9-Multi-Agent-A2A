"""
Unit tests for VerifierAgent.
"""

import json
from copy import deepcopy
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.schemas import (
    CaseInput, CustomerRequest, CaseContext,
    CaseOutput, OrderSellerAnalysis, PaymentAnalysis, PolicyResolution,
    VerificationError, VerificationResult,
)
from src.agents.verifier_agent import VerifierAgent
from src.evidence_validator import is_valid_evidence_id


FIXTURE_DIR = Path(__file__).parent / "fixtures"


def load_fixture(name):
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


class FakeDataRepository:
    """Small source of truth used to isolate semantic verifier tests."""

    def __init__(self):
        self.orders = {"order-001": {"order_id": "order-001"}}
        self.items = {
            "order-001": [
                {
                    "order_id": "order-001",
                    "order_item_id": "1",
                    "seller_id": "seller-001",
                    "price": "100.00",
                    "freight_value": "15.00",
                }
            ]
        }
        self.payments = {
            "order-001": [
                {
                    "order_id": "order-001",
                    "payment_sequential": "1",
                    "payment_value": "115.00",
                }
            ]
        }
        self.sellers = {"seller-001"}

    def get_order(self, order_id):
        return self.orders.get(order_id, {})

    def get_order_items(self, order_id):
        return self.items.get(order_id, [])

    def get_order_payments(self, order_id):
        return self.payments.get(order_id, [])

    def seller_exists(self, seller_id):
        return seller_id in self.sellers

    def item_exists(self, order_id, item_id):
        return any(
            int(row["order_item_id"]) == item_id
            for row in self.get_order_items(order_id)
        )

    def payment_exists(self, order_id, sequence):
        return any(
            int(row["payment_sequential"]) == sequence
            for row in self.get_order_payments(order_id)
        )


def semantic_result(payload=None):
    return VerifierAgent(FakeDataRepository()).validate_payload(
        payload or load_fixture("valid_output.json")
    )


def test_verifier_agent_valid_payload():
    agent = VerifierAgent()
    case_input = CaseInput(
        case_id="EC_TEST",
        opened_at="2018-10-18T00:00:00-03:00",
        customer_request=CustomerRequest(
            language="vi",
            message="Test message",
            claimed_order_id="test_order_123"
        )
    )
    context = CaseContext(case_input=case_input)
    context.order_seller = OrderSellerAnalysis(
        order_id="test_order_123",
        order_status="delivered",
        item_ids=["item:test_order_123:1"],
        seller_ids=["seller_abc"],
        item_total_brl=100.0,
        freight_total_brl=15.0
    )
    context.payment = PaymentAnalysis(
        order_id="test_order_123",
        payment_ids=["payment:test_order_123:1"],
        payment_total_brl=115.0
    )
    context.policy = PolicyResolution(
        primary_issue="late_delivery_seller",
        case_status="action_required",
        confidence=0.92,
        ranked_causes=[{"cause_code": "SELLER_HANDOFF_AFTER_LIMIT", "rank": 1}],
        responsible_parties=[{"party_type": "seller", "party_id": "seller_abc"}],
        recommended_refund_brl=15.0,
        resolution_actions=["refund_freight"],
        evidence_ids=["order:test_order_123", "item:test_order_123:1"]
    )

    result = agent.process(context)
    assert result.success is True
    assert "assessment" in result.data
    assert result.data["assessment"]["primary_issue"] == "late_delivery_seller"


def test_valid_output_fixture_matches_submission_schema():
    output = CaseOutput.model_validate(load_fixture("valid_output.json"))
    assert output.case_id == "EC_001"


def test_invalid_output_fixture_reports_all_main_error_groups():
    result = VerifierAgent().validate_payload(load_fixture("invalid_output.json"))
    fields = {error.field for error in result.errors}

    assert result.valid is False
    assert "assessment.confidence" in fields
    assert "affected_entities.order_ids" in fields
    assert "evidence_ids" in fields


@pytest.mark.parametrize(
    "evidence_id",
    [
        "order:order-001",
        "item:order-001:1",
        "payment:order-001:2",
        "seller:seller-001",
        "policy:SELLER_HANDOFF_AFTER_LIMIT",
    ],
)
def test_allowed_evidence_formats(evidence_id):
    assert is_valid_evidence_id(evidence_id)


@pytest.mark.parametrize(
    "evidence_id",
    [
        "tracking:abc",
        "refund:abc:1",
        "order:",
        "item:abc",
        "item:abc:0",
        "payment:abc:not-a-number",
        "policy:INVENTED_CAUSE",
        "seller:abc:extra",
        None,
    ],
)
def test_rejected_evidence_formats(evidence_id):
    assert not is_valid_evidence_id(evidence_id)


@pytest.mark.parametrize(
    ("path", "extra_values"),
    [
        (("affected_entities", "order_ids"), ["o2", "o3", "o4", "o5", "o6"]),
        (("affected_entities", "item_ids"), ["i2", "i3", "i4", "i5", "i6"]),
        (("affected_entities", "seller_ids"), ["s2", "s3", "s4", "s5", "s6"]),
        (("affected_entities", "payment_ids"), ["p2", "p3", "p4", "p5", "p6"]),
    ],
)
def test_each_entity_set_is_limited_to_five(path, extra_values):
    payload = load_fixture("valid_output.json")
    payload[path[0]][path[1]].extend(extra_values)
    with pytest.raises(ValidationError):
        CaseOutput.model_validate(payload)


def test_evidence_is_limited_to_ten():
    payload = load_fixture("valid_output.json")
    payload["evidence_ids"] = [f"order:o-{index}" for index in range(11)]
    with pytest.raises(ValidationError):
        CaseOutput.model_validate(payload)


def test_root_causes_are_limited_to_three():
    payload = load_fixture("valid_output.json")
    cause = payload["root_cause_analysis"]["ranked_causes"][0]
    payload["root_cause_analysis"]["ranked_causes"] = [deepcopy(cause) for _ in range(4)]
    with pytest.raises(ValidationError):
        CaseOutput.model_validate(payload)


def test_responsible_parties_are_limited_to_three():
    payload = load_fixture("valid_output.json")
    party = payload["root_cause_analysis"]["responsible_parties"][0]
    payload["root_cause_analysis"]["responsible_parties"] = [deepcopy(party) for _ in range(4)]
    with pytest.raises(ValidationError):
        CaseOutput.model_validate(payload)


def test_actions_are_limited_to_five():
    payload = load_fixture("valid_output.json")
    payload["resolution_actions"] = ["refund_freight"] * 6
    with pytest.raises(ValidationError):
        CaseOutput.model_validate(payload)


@pytest.mark.parametrize("confidence", [-0.01, 1.01])
def test_confidence_must_be_between_zero_and_one(confidence):
    payload = load_fixture("valid_output.json")
    payload["assessment"]["confidence"] = confidence
    with pytest.raises(ValidationError):
        CaseOutput.model_validate(payload)


def test_verification_result_contract_for_coordinator():
    result = VerificationResult(
        valid=False,
        errors=[
            VerificationError(
                code="INVALID_EVIDENCE",
                field="evidence_ids.0",
                message="Evidence ID không hợp lệ",
            )
        ],
    )
    assert result.valid is False
    assert result.errors[0].code == "INVALID_EVIDENCE"


def test_repository_backed_valid_output_passes():
    result = semantic_result()
    assert result.valid is True
    assert result.errors == []
    assert result.warnings == []


def test_missing_order_is_reported():
    payload = load_fixture("valid_output.json")
    payload["affected_entities"]["order_ids"] = ["missing-order"]
    result = semantic_result(payload)
    assert "ORDER_NOT_FOUND" in {error.code for error in result.errors}


def test_missing_item_is_reported():
    payload = load_fixture("valid_output.json")
    payload["affected_entities"]["item_ids"] = ["order-001:99"]
    result = semantic_result(payload)
    assert "ITEM_NOT_FOUND" in {error.code for error in result.errors}


def test_malformed_item_entity_id_is_reported_as_not_found():
    payload = load_fixture("valid_output.json")
    payload["affected_entities"]["item_ids"] = ["invalid-item-id"]
    result = semantic_result(payload)
    assert "ITEM_NOT_FOUND" in {error.code for error in result.errors}


def test_missing_seller_is_reported():
    payload = load_fixture("valid_output.json")
    payload["affected_entities"]["seller_ids"] = ["missing-seller"]
    result = semantic_result(payload)
    assert "SELLER_NOT_FOUND" in {error.code for error in result.errors}


def test_missing_payment_is_reported():
    payload = load_fixture("valid_output.json")
    payload["affected_entities"]["payment_ids"] = ["order-001:99"]
    result = semantic_result(payload)
    assert "PAYMENT_NOT_FOUND" in {error.code for error in result.errors}


@pytest.mark.parametrize(
    ("field", "wrong_value", "expected_code"),
    [
        ("item_total_brl", 99.99, "ITEM_TOTAL_MISMATCH"),
        ("freight_total_brl", 14.99, "FREIGHT_TOTAL_MISMATCH"),
        ("payment_total_brl", 114.99, "PAYMENT_TOTAL_MISMATCH"),
    ],
)
def test_each_financial_total_is_recomputed(field, wrong_value, expected_code):
    payload = load_fixture("valid_output.json")
    payload["financial_resolution"][field] = wrong_value
    result = semantic_result(payload)
    assert expected_code in {error.code for error in result.errors}


@pytest.mark.parametrize(
    ("issue", "expected_refund"),
    [
        ("canceled_order_paid", 115.0),
        ("unavailable_order_paid", 115.0),
        ("late_delivery_seller", 15.0),
        ("late_delivery_logistics", 15.0),
        ("valid_split_payment", 0.0),
        ("unsupported_late_claim", 0.0),
    ],
)
def test_refund_is_checked_for_every_policy_type(issue, expected_refund):
    payload = load_fixture("valid_output.json")
    payload["assessment"]["primary_issue"] = issue
    payload["financial_resolution"]["recommended_refund_brl"] = expected_refund
    payload["assessment"]["case_status"] = (
        "action_required" if expected_refund > 0 else "no_action"
    )
    result = semantic_result(payload)
    assert "REFUND_POLICY_MISMATCH" not in {error.code for error in result.errors}


def test_wrong_refund_is_reported():
    payload = load_fixture("valid_output.json")
    payload["financial_resolution"]["recommended_refund_brl"] = 14.0
    result = semantic_result(payload)
    assert "REFUND_POLICY_MISMATCH" in {error.code for error in result.errors}


def test_case_status_must_match_refund_policy():
    payload = load_fixture("valid_output.json")
    payload["assessment"]["case_status"] = "no_action"
    result = semantic_result(payload)
    assert "CASE_STATUS_MISMATCH" in {error.code for error in result.errors}
