# Báo cáo cá nhân — Lê Tuấn Hiệp

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
|---|---|
| Họ và tên | Lê Tuấn Hiệp |
| MSSV | 2A202601667 |
| Khóa/Lớp | K3 |
| Vai trò chính | Role 3 — Payment Agent |
| Ngày hoàn thành | 2026-08-05 |

## 2. Vai trò và phạm vi công việc

| Module/deliverable | File/hàm phụ trách | Input | Output | Trạng thái |
|---|---|---|---|---|
| Payment Agent | `src/agents/payment_agent.py` | Payment rows, item/freight totals | `PaymentAnalysis` | Hoàn thành |
| Payment profiling | `scripts/explore_payments.py`, `docs/payment_data_profile.md` | Olist payment/item CSV | Báo cáo dữ liệu và case mẫu | Hoàn thành |
| Payment fixtures/tests | `tests/fixtures/payment_*`, `tests/test_payment.py` | Payment edge cases | Kết quả đối soát | Hoàn thành |

Việc hỗ trợ: thống nhất payment IDs/evidence và expected totals với Policy và Verifier.

## 3. Kết quả theo vai trò

| Nhiệm vụ | Artifact | Kết quả | Cách xác minh |
|---|---|---|---|
| Tính payment total | `PaymentAgent.process` | Tổng payment bằng `Decimal` | `python -m pytest tests/test_payment.py -q` |
| Split payment | `PaymentAnalysis` | Nhận diện từ hai payment row trở lên | Payment fixtures |
| Đối soát | `difference_brl`, `payment_matches` | Sai số tối đa 0.10 BRL | Tests 0.10/0.11 BRL |
| Evidence | `payment_ids`, `evidence_ids` | ID theo payment sequential | Output validator |

Kết quả cụ thể: payment totals của 50 output khớp từng payment row trong CSV.

## 4. Giải thích kỹ thuật

### Vấn đề cần giải quyết

Một order có thể có nhiều payment row và installments. Cần cộng `payment_value` từng row, không nhân theo installments, rồi đối soát với item + freight.

### Cách triển khai

Payment Agent lọc payment theo order, sắp xếp bằng `payment_sequential`, chuyển số sang `Decimal`, cộng và làm tròn `ROUND_HALF_UP`. `expected_total = item_total + freight_total`; payment match khi chênh lệch không quá 0.10 BRL. Split payment dựa vào số row, không dựa vào installments.

### Input, output và contract

| Thành phần | Mô tả |
|---|---|
| Input | Payment rows, `OrderSellerAnalysis` totals |
| Output | `PaymentAnalysis` |
| Module phụ thuộc | `src/schemas.py` |
| Module sử dụng output | Policy và Verifier |
| Lỗi cần xử lý | Không có payment, zero payment, nhiều payment type, rounding |

### Cách xác minh

```powershell
python -m pytest tests/test_payment.py -q
```

- Kết quả mong đợi: totals/split/tolerance đúng.
- Kết quả thực tế: payment tests và toàn bộ 73 test pass.
- Artifact: payment fixtures và `docs/payment_data_profile.md`.

## 5. Quyết định kỹ thuật quan trọng

- Bối cảnh: dùng `float` có thể gây sai khác quanh tolerance 0.10.
- Phương án cân nhắc: float; hoặc `Decimal` từ chuỗi nguồn.
- Phương án chọn: `Decimal` và `ROUND_HALF_UP`.
- Lý do: kết quả tiền tái hiện được, tránh binary floating-point.
- Bằng chứng: tests tại biên 0.10 và 0.11 BRL pass.

## 6. Lỗi hoặc blocker đã xử lý

- Triệu chứng: có thể tính sai nếu nhân `payment_value` với `payment_installments`.
- Nguyên nhân gốc: hiểu installments là số giao dịch thay vì thuộc tính phương thức trả góp.
- Cách xử lý: chỉ cộng mỗi payment row một lần; installments không tham gia công thức.
- Xác minh: test single payment có installments >1 vẫn chỉ tính một `payment_value`.
- Bài học: cần đọc đúng ý nghĩa cột trước khi xây công thức tài chính.

## 7. Hiểu biết luồng end-to-end

Payment Agent nhận totals từ Order/Seller, đối soát payment và handoff cho Policy. Policy chỉ chọn `valid_split_payment` khi có ít nhất hai row và totals match. Với canceled/unavailable, payment total là refund. Verifier tính lại payment từ CSV để ngăn sai số hoặc evidence giả.

## 8. Cam kết

- [x] Báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi hiểu luồng end-to-end.
- [x] Chỉ ghi kết quả đã kiểm chứng.
- [x] Không chứa secret.
- [x] Không sao chép báo cáo thành viên khác.

**Họ và tên:** Lê Tuấn Hiệp  
**Ngày xác nhận:** 2026-08-05
