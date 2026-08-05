# Khảo sát dữ liệu Payment của Olist

Nguồn: `data/olist_order_payments_dataset.csv` và `data/olist_order_items_dataset.csv`.
Script không nhân `payment_value` với `payment_installments`.

## Tổng quan

- Tổng số payment row: 103886.
- Số order có payment: 99440.
- Số order split payment (từ 2 payment row): 2961.
- Số order không có payment: 1.

## Payment value

- Min: 0.00 BRL.
- Max: 13664.08 BRL.
- Mean: 154.10 BRL.
- Median: 100.00 BRL.

### Payment type

| Giá trị | Số lượng |
|---:|---:|
| boleto | 19784 |
| credit_card | 76795 |
| debit_card | 1529 |
| not_defined | 3 |
| voucher | 5775 |

### Payment installments

| Giá trị | Số lượng |
|---:|---:|
| 0 | 2 |
| 1 | 52546 |
| 10 | 5328 |
| 11 | 23 |
| 12 | 133 |
| 13 | 16 |
| 14 | 15 |
| 15 | 74 |
| 16 | 5 |
| 17 | 8 |
| 18 | 27 |
| 2 | 12413 |
| 20 | 17 |
| 21 | 3 |
| 22 | 1 |
| 23 | 1 |
| 24 | 18 |
| 3 | 10461 |
| 4 | 7098 |
| 5 | 5239 |
| 6 | 3920 |
| 7 | 1626 |
| 8 | 4268 |
| 9 | 644 |

### Số payment row trên mỗi order

| Giá trị | Số lượng |
|---:|---:|
| 1 | 96479 |
| 10 | 5 |
| 11 | 8 |
| 12 | 8 |
| 13 | 3 |
| 14 | 2 |
| 15 | 2 |
| 19 | 2 |
| 2 | 2382 |
| 21 | 1 |
| 22 | 1 |
| 26 | 1 |
| 29 | 1 |
| 3 | 301 |
| 4 | 108 |
| 5 | 52 |
| 6 | 36 |
| 7 | 28 |
| 8 | 11 |
| 9 | 9 |

### Null theo cột

| Cột | Số null |
|---|---:|
| order_id | 0 |
| payment_sequential | 0 |
| payment_type | 0 |
| payment_installments | 0 |
| payment_value | 0 |

## Bất thường dữ liệu

- Dòng trùng hoàn toàn: 0.
- Cặp `order_id + payment_sequential` bị trùng: 0.
- `payment_value = 0`: 9 dòng.
- `payment_value < 0`: 0 dòng.
- Không có giá trị null trong bảng payment.

## Đối soát

Theo từng `order_id`: `payment_total_brl = sum(payment_value)`, `expected_total_brl = sum(price) + sum(freight_value)`, `difference_brl = abs(payment_total_brl - expected_total_brl)`. Payment khớp khi chênh lệch không quá 0.10 BRL. Split payment được xác định duy nhất bằng số payment row từ 2 trở lên, không phải bằng số kỳ trả góp.

## Order được chọn làm fixture

| Trường hợp mong muốn | order_id được chọn |
|---|---|
| một payment row và payment_installments > 1 | `00010242fe8c5a6d1ba2dd792cb16214` |
| split payment khớp tổng tiền | `0016dfedd97fc2950e388d2971d718c7` |
| split payment dùng nhiều payment_type | `0016dfedd97fc2950e388d2971d718c7` |
| nhiều hơn hai payment row | `009ac365164f8e06f59d18a08045f6c4` |
| split payment không khớp tổng tiền | `033ccfbdfc4d29677b7e1e6df3a82820` |

Các fixture chỉ sao chép giá trị thật từ CSV gốc; không chỉnh sửa tiền.
