"""Unit tests for the deterministic Payment Agent."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

import pytest

from src.agents.payment_agent import PaymentAgent
from src.schemas import CaseContext, CaseInput, CustomerRequest


FIXTURE_DIR = Path(__file__).parent / "fixtures"


@dataclass
class OrderSellerTotals:
    item_total_brl: float
    freight_total_brl: float


def read_fixture(name: str) -> list[dict[str, str]]:
    with (FIXTURE_DIR / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def make_context(
    order_id: str,
    payments: list[dict[str, object]] | None,
    item_total: float,
    freight_total: float,
    *,
    include_payments_key: bool = True,
) -> CaseContext:
    raw_data = {"payments": payments} if include_payments_key else {}
    return CaseContext(
        case_input=CaseInput(
            case_id="EC_TEST",
            opened_at="2018-10-18T00:00:00-03:00",
            customer_request=CustomerRequest(
                language="vi", message="Kiểm tra payment", claimed_order_id=order_id
            ),
        ),
        raw_data=raw_data,
        order_seller=OrderSellerTotals(item_total, freight_total),
    )


def run_agent(context: CaseContext):
    result = PaymentAgent().process(context)
    assert result.success is True
    assert context.payment is not None
    assert result.data == context.payment.to_dict()
    return context.payment


def test_real_fixtures_match_expected_results():
    payments = read_fixture("payment_rows.csv")
    items = read_fixture("payment_order_items.csv")
    expected = read_fixture("payment_expected_results.csv")

    for expected_row in expected:
        order_id = expected_row["order_id"]
        order_payments = [row for row in payments if row["order_id"] == order_id]
        order_items = [row for row in items if row["order_id"] == order_id]
        item_total = sum(float(row["price"]) for row in order_items)
        freight_total = sum(float(row["freight_value"]) for row in order_items)
        analysis = run_agent(make_context(order_id, order_payments, item_total, freight_total))

        assert analysis.payment_row_count == int(expected_row["payment_row_count"])
        assert analysis.payment_total_brl == float(expected_row["payment_total_brl"])
        assert analysis.expected_total_brl == float(expected_row["expected_total_brl"])
        assert analysis.difference_brl == float(expected_row["difference_brl"])
        assert analysis.payment_matches is (expected_row["payment_matches"] == "true")
        assert analysis.is_split_payment is (expected_row["is_split_payment"] == "true")


def test_real_single_installment_payment_is_not_split_and_is_not_multiplied():
    order_id = "00010242fe8c5a6d1ba2dd792cb16214"
    rows = [row for row in read_fixture("payment_rows.csv") if row["order_id"] == order_id]
    analysis = run_agent(make_context(order_id, rows, 58.90, 13.29))

    assert rows[0]["payment_installments"] == "2"
    assert analysis.payment_row_count == 1
    assert analysis.payment_total_brl == 72.19
    assert analysis.is_split_payment is False


def test_real_split_payment_uses_multiple_payment_types():
    order_id = "0016dfedd97fc2950e388d2971d718c7"
    rows = [row for row in read_fixture("payment_rows.csv") if row["order_id"] == order_id]
    analysis = run_agent(make_context(order_id, rows, 49.75, 20.80))

    assert {payment.payment_type for payment in analysis.payments} == {"credit_card", "voucher"}
    assert analysis.payment_row_count == 2
    assert analysis.payment_matches is True
    assert analysis.is_split_payment is True


def test_real_split_payment_with_more_than_two_rows():
    order_id = "009ac365164f8e06f59d18a08045f6c4"
    rows = [row for row in read_fixture("payment_rows.csv") if row["order_id"] == order_id]
    analysis = run_agent(make_context(order_id, rows, 16.90, 15.10))

    assert analysis.payment_row_count == 6
    assert analysis.payment_total_brl == 32.0
    assert analysis.is_split_payment is True


@pytest.mark.parametrize(
    ("payment_value", "expected_match", "expected_difference"),
    [("9.90", True, 0.10), ("9.89", False, 0.11)],
)
def test_payment_matching_tolerance(payment_value, expected_match, expected_difference):
    rows = [{"order_id": "tol", "payment_sequential": 1, "payment_type": "voucher", "payment_value": payment_value}]
    analysis = run_agent(make_context("tol", rows, 10.0, 0.0))
    assert analysis.difference_brl == expected_difference
    assert analysis.payment_matches is expected_match


def test_zero_payment_value():
    rows = [{"order_id": "zero", "payment_sequential": 1, "payment_type": "voucher", "payment_value": "0.00"}]
    analysis = run_agent(make_context("zero", rows, 0.0, 0.0))
    assert analysis.payment_row_count == 1
    assert analysis.payment_total_brl == 0.0
    assert analysis.payment_matches is True


@pytest.mark.parametrize("include_payments_key", [True, False])
def test_no_payment_or_missing_payments_key_does_not_crash(include_payments_key):
    analysis = run_agent(
        make_context("none", [], 12.34, 0.66, include_payments_key=include_payments_key)
    )
    assert analysis.payments == []
    assert analysis.payment_ids == []
    assert analysis.payment_row_count == 0
    assert analysis.payment_total_brl == 0.0
    assert analysis.expected_total_brl == 13.0
    assert analysis.difference_brl == 13.0
    assert analysis.payment_matches is False
    assert analysis.is_split_payment is False


def test_payment_ids_format_and_sorting_by_sequence():
    rows = [
        {"order_id": "sort", "payment_sequential": 2, "payment_type": "voucher", "payment_value": "2.00"},
        {"order_id": "sort", "payment_sequential": 1, "payment_type": "credit_card", "payment_value": "3.00"},
    ]
    analysis = run_agent(make_context("sort", rows, 5.0, 0.0))
    assert [payment.payment_sequential for payment in analysis.payments] == [1, 2]
    assert analysis.payment_ids == ["sort:1", "sort:2"]
    assert all(not payment_id.startswith("payment:") for payment_id in analysis.payment_ids)


def test_money_is_rounded_to_two_decimal_places():
    rows = [
        {"order_id": "round", "payment_sequential": 1, "payment_type": "voucher", "payment_value": "0.105"},
        {"order_id": "round", "payment_sequential": 2, "payment_type": "voucher", "payment_value": "0.105"},
    ]
    analysis = run_agent(make_context("round", rows, 0.10, 0.10))
    assert analysis.payment_total_brl == 0.21
    assert analysis.expected_total_brl == 0.20
    assert analysis.difference_brl == 0.01
    assert [payment.payment_value_brl for payment in analysis.payments] == [0.11, 0.11]


def test_only_rows_for_current_order_are_processed():
    rows = [
        {"order_id": "current", "payment_sequential": 1, "payment_type": "boleto", "payment_value": "5.00"},
        {"order_id": "other", "payment_sequential": 1, "payment_type": "boleto", "payment_value": "999.00"},
    ]
    analysis = run_agent(make_context("current", rows, 5.0, 0.0))
    assert analysis.payment_row_count == 1
    assert analysis.payment_total_brl == 5.0
    assert analysis.payment_ids == ["current:1"]
