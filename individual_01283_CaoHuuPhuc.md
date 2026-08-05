# Báo cáo cá nhân — Cao Hữu Phúc

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
|---|---|
| Họ và tên | Cao Hữu Phúc |
| MSSV | 2A202601283 |
| Khóa/Lớp | K3 |
| Vai trò chính | Role 4 — Delivery + Policy Agent |
| Ngày hoàn thành | 2026-08-05 |

## 2. Vai trò và phạm vi công việc

| Module/deliverable | File/hàm phụ trách | Input | Output | Trạng thái |
|---|---|---|---|---|
| Delivery Agent | `src/agents/delivery_agent.py` | Order timestamps và seller handoff | `DeliveryAnalysis` | Hoàn thành |
| Policy Agent | `src/agents/policy_agent.py` | Order, payment, delivery facts | `PolicyResolution` | Hoàn thành |
| Policy definitions | `src/policies.py` | `EC_POLICY_V1` | Mapping issue/cause/party/refund/action | Hoàn thành |
| Regression tests | `tests/test_delivery.py`, `tests/test_policy.py`, `tests/test_policy_regression.py` | Case contexts | Khóa hành vi 6 policy | Hoàn thành |

Việc hỗ trợ: thống nhất rule priority với Coordinator và refund expectation với Verifier.

## 3. Kết quả theo vai trò

| Nhiệm vụ | Artifact | Kết quả | Cách xác minh |
|---|---|---|---|
| Phân loại delivery | `DeliveryAgent.process` | Xác định giao đúng/trễ và seller handoff | `python -m pytest tests/test_delivery.py -q` |
| Áp dụng policy | `PolicyAgent.process` | Chọn đúng issue, cause, party, refund và action | `python -m pytest tests/test_policy.py -q` |
| Chống regression | `test_policy_regression.py` | Kiểm tra đủ sáu rule và priority canceled | `python -m pytest tests/test_policy_regression.py -q` |

Kết quả cụ thể: phân bố output gồm đủ sáu primary issue và không có lỗi mapping issue–cause–party–action.

## 4. Giải thích kỹ thuật

### Vấn đề cần giải quyết

Cùng một claim giao trễ có thể thuộc seller hoặc logistics; ngoài ra canceled/unavailable phải được ưu tiên trước delivery và split payment.

### Cách triển khai

Delivery Agent so sánh `order_delivered_customer_date` với `order_estimated_delivery_date`; seller handoff lấy từ kết quả Order/Seller. Policy Agent sử dụng chuỗi `if/elif` đúng thứ tự sáu rule. Mapping trong `src/policies.py` cố định cause code, party type, refund type, action và case status.

### Input, output và contract

| Thành phần | Mô tả |
|---|---|
| Input | `OrderSellerAnalysis`, `PaymentAnalysis`, `DeliveryAnalysis` |
| Output | `PolicyResolution` |
| Module phụ thuộc | `src/policies.py`, `src/schemas.py` |
| Module sử dụng output | Verifier Agent |
| Lỗi cần xử lý | Timestamp null, nhiều điều kiện cùng đúng, seller ID động |

### Cách xác minh

```powershell
python -m pytest tests/test_delivery.py tests/test_policy.py tests/test_policy_regression.py -q
```

- Kết quả mong đợi: đủ sáu quyết định đúng mapping.
- Kết quả thực tế: regression test và toàn bộ 73 test pass.
- Artifact: `output/`, `trace.jsonl`.

## 5. Quyết định kỹ thuật quan trọng

- Bối cảnh: một case có thể đồng thời canceled, paid và có timestamps giao hàng.
- Phương án cân nhắc: đánh giá rule độc lập; hoặc chuỗi priority duy nhất.
- Phương án chọn: chuỗi priority theo README.
- Lý do: ngăn rule thấp ghi đè canceled/unavailable.
- Bằng chứng: test `test_canceled_rule_keeps_priority_over_late_delivery` pass.

## 6. Lỗi hoặc blocker đã xử lý

- Triệu chứng: nếu dùng nhiều `if`, một case có thể nhận hơn một issue.
- Nguyên nhân gốc: các điều kiện policy có vùng giao nhau.
- Cách xử lý: dùng `if/elif` đúng priority 1–6 và regression test.
- Xác minh: sáu policy test đều pass.
- Bài học: priority là một phần của contract nghiệp vụ, không chỉ là thứ tự trình bày.

## 7. Hiểu biết luồng end-to-end

Sau khi DataRepository và ba domain agent tạo facts, Policy Agent chỉ áp dụng dữ liệu đã xác minh. Refund là payment total cho canceled/unavailable, freight total cho hai loại late delivery và bằng 0 cho split payment/unsupported claim. Verifier tính lại toàn bộ trước khi output được ghi.

## 8. Cam kết

- [x] Báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi hiểu luồng end-to-end.
- [x] Chỉ ghi kết quả đã kiểm chứng.
- [x] Không chứa secret.
- [x] Không sao chép báo cáo thành viên khác.

**Họ và tên:** Cao Hữu Phúc  
**Ngày xác nhận:** 2026-08-05
