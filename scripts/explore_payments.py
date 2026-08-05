"""Profile Olist payments and create reproducible, real-data payment fixtures."""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from statistics import median
from typing import Callable, Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
FIXTURE_DIR = PROJECT_ROOT / "tests" / "fixtures"
DOC_PATH = PROJECT_ROOT / "docs" / "payment_data_profile.md"

PAYMENTS_PATH = DATA_DIR / "olist_order_payments_dataset.csv"
ITEMS_PATH = DATA_DIR / "olist_order_items_dataset.csv"
ORDERS_PATH = DATA_DIR / "olist_orders_dataset.csv"

CENT = Decimal("0.01")
MATCH_TOLERANCE = Decimal("0.10")


def money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def decimal_text(value: Decimal) -> str:
    return f"{money(value):.2f}"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def require_columns(path: Path, rows: list[dict[str, str]], columns: Iterable[str]) -> None:
    present = set(rows[0]) if rows else set()
    missing = set(columns) - present
    if missing:
        raise ValueError(f"{path} is missing required columns: {', '.join(sorted(missing))}")


def write_csv(path: Path, columns: list[str], rows: Iterable[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def markdown_distribution(title: str, distribution: Counter[object]) -> list[str]:
    lines = [f"### {title}", "", "| Giá trị | Số lượng |", "|---:|---:|"]
    for key, count in sorted(distribution.items(), key=lambda pair: (str(pair[0]))):
        label = "(null)" if key == "" else str(key)
        lines.append(f"| {label} | {count} |")
    lines.append("")
    return lines


def main() -> None:
    missing = [path for path in (PAYMENTS_PATH, ITEMS_PATH) if not path.is_file()]
    if missing:
        names = "\n".join(f"- {path}" for path in missing)
        raise FileNotFoundError(f"Missing required Olist data file(s):\n{names}")

    payment_rows = read_csv(PAYMENTS_PATH)
    item_rows = read_csv(ITEMS_PATH)
    require_columns(
        PAYMENTS_PATH,
        payment_rows,
        ["order_id", "payment_sequential", "payment_type", "payment_installments", "payment_value"],
    )
    require_columns(
        ITEMS_PATH,
        item_rows,
        ["order_id", "order_item_id", "price", "freight_value"],
    )

    payment_columns = list(payment_rows[0])
    null_counts = {column: sum(row[column].strip() == "" for row in payment_rows) for column in payment_columns}
    full_duplicate_count = len(payment_rows) - len({tuple(row[column] for column in payment_columns) for row in payment_rows})
    key_counts = Counter((row["order_id"], row["payment_sequential"]) for row in payment_rows)
    duplicate_key_pair_count = sum(count > 1 for count in key_counts.values())

    payments_by_order: dict[str, list[dict[str, str]]] = defaultdict(list)
    payment_types = Counter()
    installment_distribution = Counter()
    values: list[Decimal] = []
    for row in payment_rows:
        payments_by_order[row["order_id"]].append(row)
        payment_types[row["payment_type"]] += 1
        installment_distribution[row["payment_installments"]] += 1
        values.append(Decimal(row["payment_value"]))

    items_by_order: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in item_rows:
        items_by_order[row["order_id"]].append(row)

    summaries: dict[str, dict[str, object]] = {}
    for order_id, rows in payments_by_order.items():
        ordered_rows = sorted(rows, key=lambda row: int(row["payment_sequential"]))
        payment_total = sum((Decimal(row["payment_value"]) for row in ordered_rows), Decimal("0"))
        order_items = items_by_order.get(order_id, [])
        item_total = sum((Decimal(row["price"]) for row in order_items), Decimal("0"))
        freight_total = sum((Decimal(row["freight_value"]) for row in order_items), Decimal("0"))
        expected_total = item_total + freight_total
        difference = abs(payment_total - expected_total)
        summaries[order_id] = {
            "order_id": order_id,
            "payment_row_count": len(ordered_rows),
            "payment_total_brl": money(payment_total),
            "item_total_brl": money(item_total),
            "freight_total_brl": money(freight_total),
            "expected_total_brl": money(expected_total),
            "difference_brl": money(difference),
            "payment_matches": difference <= MATCH_TOLERANCE,
            "is_split_payment": len(ordered_rows) >= 2,
        }

    row_count_distribution = Counter(len(rows) for rows in payments_by_order.values())
    split_order_count = sum(len(rows) >= 2 for rows in payments_by_order.values())

    # Pick real examples in a stable order. A selected order may cover multiple categories.
    candidates: list[tuple[str, Callable[[str], bool]]] = [
        (
            "một payment row và payment_installments > 1",
            lambda oid: len(payments_by_order[oid]) == 1
            and int(payments_by_order[oid][0]["payment_installments"]) > 1,
        ),
        (
            "split payment khớp tổng tiền",
            lambda oid: len(payments_by_order[oid]) >= 2 and bool(summaries[oid]["payment_matches"]),
        ),
        (
            "split payment dùng nhiều payment_type",
            lambda oid: len(payments_by_order[oid]) >= 2
            and len({row["payment_type"] for row in payments_by_order[oid]}) >= 2,
        ),
        ("nhiều hơn hai payment row", lambda oid: len(payments_by_order[oid]) > 2),
        (
            "split payment không khớp tổng tiền",
            lambda oid: len(payments_by_order[oid]) >= 2 and not bool(summaries[oid]["payment_matches"]),
        ),
    ]
    selected: list[str] = []
    category_selection: list[tuple[str, str | None]] = []
    order_ids = sorted(payments_by_order)
    for label, predicate in candidates:
        match = next((order_id for order_id in order_ids if predicate(order_id)), None)
        category_selection.append((label, match))
        if match is not None and match not in selected and len(selected) < 5:
            selected.append(match)

    fixture_payment_rows = [
        row
        for order_id in selected
        for row in sorted(payments_by_order[order_id], key=lambda item: int(item["payment_sequential"]))
    ]
    fixture_item_rows = [row for order_id in selected for row in items_by_order.get(order_id, [])]
    expected_rows = []
    for order_id in selected:
        summary = summaries[order_id]
        expected_rows.append(
            {
                **summary,
                "payment_total_brl": decimal_text(summary["payment_total_brl"]),
                "item_total_brl": decimal_text(summary["item_total_brl"]),
                "freight_total_brl": decimal_text(summary["freight_total_brl"]),
                "expected_total_brl": decimal_text(summary["expected_total_brl"]),
                "difference_brl": decimal_text(summary["difference_brl"]),
                "payment_matches": str(summary["payment_matches"]).lower(),
                "is_split_payment": str(summary["is_split_payment"]).lower(),
            }
        )

    fixture_paths = [
        FIXTURE_DIR / "payment_rows.csv",
        FIXTURE_DIR / "payment_order_items.csv",
        FIXTURE_DIR / "payment_expected_results.csv",
    ]
    write_csv(
        fixture_paths[0],
        ["order_id", "payment_sequential", "payment_type", "payment_installments", "payment_value"],
        fixture_payment_rows,
    )
    write_csv(fixture_paths[1], ["order_id", "order_item_id", "price", "freight_value"], fixture_item_rows)
    write_csv(
        fixture_paths[2],
        [
            "order_id",
            "payment_row_count",
            "payment_total_brl",
            "item_total_brl",
            "freight_total_brl",
            "expected_total_brl",
            "difference_brl",
            "payment_matches",
            "is_split_payment",
        ],
        expected_rows,
    )

    order_without_payment: int | None = None
    if ORDERS_PATH.is_file():
        orders = read_csv(ORDERS_PATH)
        require_columns(ORDERS_PATH, orders, ["order_id"])
        order_without_payment = len({row["order_id"] for row in orders} - set(payments_by_order))

    mean_value = sum(values, Decimal("0")) / Decimal(len(values))
    median_value = median(values)
    anomaly_lines = [
        f"- Dòng trùng hoàn toàn: {full_duplicate_count}.",
        f"- Cặp `order_id + payment_sequential` bị trùng: {duplicate_key_pair_count}.",
        f"- `payment_value = 0`: {sum(value == 0 for value in values)} dòng.",
        f"- `payment_value < 0`: {sum(value < 0 for value in values)} dòng.",
    ]
    if any(null_counts.values()):
        anomaly_lines.append("- Có giá trị null; xem bảng null theo cột bên dưới.")
    else:
        anomaly_lines.append("- Không có giá trị null trong bảng payment.")

    report = [
        "# Khảo sát dữ liệu Payment của Olist",
        "",
        f"Nguồn: `{PAYMENTS_PATH.relative_to(PROJECT_ROOT)}` và `{ITEMS_PATH.relative_to(PROJECT_ROOT)}`.",
        "Script không nhân `payment_value` với `payment_installments`.",
        "",
        "## Tổng quan",
        "",
        f"- Tổng số payment row: {len(payment_rows)}.",
        f"- Số order có payment: {len(payments_by_order)}.",
        f"- Số order split payment (từ 2 payment row): {split_order_count}.",
        f"- Số order không có payment: {order_without_payment if order_without_payment is not None else 'không tính được vì thiếu bảng orders'}.",
        "",
        "## Payment value",
        "",
        f"- Min: {decimal_text(min(values))} BRL.",
        f"- Max: {decimal_text(max(values))} BRL.",
        f"- Mean: {decimal_text(mean_value)} BRL.",
        f"- Median: {decimal_text(median_value)} BRL.",
        "",
    ]
    report += markdown_distribution("Payment type", payment_types)
    report += markdown_distribution("Payment installments", installment_distribution)
    report += markdown_distribution("Số payment row trên mỗi order", row_count_distribution)
    report += ["### Null theo cột", "", "| Cột | Số null |", "|---|---:|"]
    report += [f"| {column} | {count} |" for column, count in null_counts.items()]
    report += ["", "## Bất thường dữ liệu", "", *anomaly_lines, "", "## Đối soát", ""]
    report += [
        "Theo từng `order_id`: `payment_total_brl = sum(payment_value)`, "
        "`expected_total_brl = sum(price) + sum(freight_value)`, "
        "`difference_brl = abs(payment_total_brl - expected_total_brl)`. "
        "Payment khớp khi chênh lệch không quá 0.10 BRL. Split payment được xác định duy nhất bằng "
        "số payment row từ 2 trở lên, không phải bằng số kỳ trả góp.",
        "",
        "## Order được chọn làm fixture",
        "",
        "| Trường hợp mong muốn | order_id được chọn |",
        "|---|---|",
    ]
    for label, order_id in category_selection:
        report.append(f"| {label} | {f'`{order_id}`' if order_id else 'Không tìm thấy trong dữ liệu thật'} |")
    report += ["", "Các fixture chỉ sao chép giá trị thật từ CSV gốc; không chỉnh sửa tiền.", ""]

    DOC_PATH.parent.mkdir(parents=True, exist_ok=True)
    DOC_PATH.write_text("\n".join(report), encoding="utf-8")

    for path in [*fixture_paths, DOC_PATH]:
        print(f"Created: {path}")
    print("Selected fixture order_id(s):")
    for order_id in selected:
        print(f"- {order_id}")


if __name__ == "__main__":
    main()
