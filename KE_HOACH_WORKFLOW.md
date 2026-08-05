# Kế hoạch và workflow dự án Multi-Agent E-commerce Dispute Resolution

## 1. Mục tiêu dự án

Xây dựng hệ thống multi-agent xử lý 50 yêu cầu hỗ trợ khách hàng từ `EC_001.json` đến `EC_050.json` dựa trên dữ liệu Olist.

Với mỗi case, hệ thống phải:

- Truy xuất đúng order được khách hàng cung cấp.
- Đối chiếu order, item, seller, payment và delivery.
- Xác định vấn đề chính theo `EC_POLICY_V1`.
- Xác định nguyên nhân gốc và bên chịu trách nhiệm.
- Tạo evidence ID có thể kiểm chứng từ CSV.
- Tính số tiền hoàn đề xuất.
- Đưa ra hành động xử lý.
- Kiểm tra kết quả trước khi ghi vào `output/`.

Sản phẩm cuối cùng gồm:

- 50 file JSON trong `output/`.
- `trace.jsonl` của lượt chạy mới nhất.
- `metadata.json`.
- `architecture.md`.
- Báo cáo cá nhân của từng thành viên.
- File ZIP chỉ chứa 50 file JSON trong `output/`.

## 2. Kiến trúc hệ thống

Hệ thống có 6 agent logic và dùng chung một model LLM không vượt quá 10B tham số.

```text
EC_xxx.json
    |
    v
Coordinator Agent
    |
    +---> Order & Seller Agent ------> OrderSellerAnalysis
    |
    +---> Payment Agent -------------> PaymentAnalysis
    |
    +---> Delivery Agent ------------> DeliveryAnalysis
                                          |
                                          v
                                     Policy Agent
                                          |
                                          v
                                     PolicyDecision
                                          |
                                          v
                                    Verifier Agent
                                          |
                              +-----------+-----------+
                              |                       |
                            Hợp lệ                Không hợp lệ
                              |                       |
                         Ghi output             Trả lỗi để sửa
```

Danh sách agent:

1. Coordinator Agent.
2. Order & Seller Agent.
3. Payment Agent.
4. Delivery Agent.
5. Policy Agent.
6. Verifier Agent.

Đây là 6 vai trò logic, không phải 6 model khác nhau.

## 3. Phân công thành viên

| Thành viên | Vai trò chính | Module sở hữu | Sản phẩm bàn giao |
|---|---|---|---|
| Người 1 | Coordinator & Integration | Điều phối, trace, chạy pipeline | 50 output hoàn chỉnh |
| Người 2 | Data + Order/Seller Agent | Đọc/join CSV, order, item, seller | `OrderSellerAnalysis` |
| Người 3 | Payment Agent | Payment, đối soát và tổng tiền | `PaymentAnalysis` |
| Người 4 | Delivery + Policy Agent | Delivery và áp dụng policy | `DeliveryAnalysis`, `PolicyDecision` |
| Người 5 | Verifier + QA | Schema, evidence, test, ZIP | Kết quả validation và file ZIP |

### 3.1. Người 1 — Coordinator & Integration

Phụ trách:

- Đọc 50 input JSON.
- Điều phối các agent theo đúng workflow.
- Tích hợp LLM client dùng chung.
- Quản lý lỗi và retry.
- Ghi `trace.jsonl`.
- Tổng hợp kết quả thành output cuối.
- Chạy một case hoặc toàn bộ 50 case.
- Tổng hợp nội dung `architecture.md`.

File dự kiến:

```text
src/main.py
src/coordinator.py
src/llm_client.py
src/trace_writer.py
metadata.json
```

### 3.2. Người 2 — Data + Order/Seller Agent

Phụ trách:

- Khảo sát schema của 9 file CSV.
- Đọc và chuẩn hóa dữ liệu.
- Tạo index theo `order_id`.
- Join orders, order items và sellers.
- Tính tổng item và tổng freight.
- Xác định seller bàn giao trễ.
- Sinh item và seller entity IDs.
- Kiểm chứng item/seller evidence.

File dự kiến:

```text
src/data_repository.py
src/agents/order_seller_agent.py
tests/test_data_repository.py
tests/test_order_seller.py
```

### 3.3. Người 3 — Payment Agent

Phụ trách:

- Lấy toàn bộ payment row của order.
- Tính `payment_total_brl`.
- Đếm số payment row.
- Phát hiện split payment.
- Đối soát payment với item và freight.
- Sinh payment IDs và payment evidence.
- Viết test cho các trường hợp biên về tiền.

File dự kiến:

```text
src/agents/payment_agent.py
tests/test_payment.py
```

### 3.4. Người 4 — Delivery + Policy Agent

Phụ trách Delivery Agent:

- Parse timestamp.
- So sánh ngày giao thực tế với estimated delivery date.
- Kiểm tra seller bàn giao đúng hay trễ hạn.
- Trả `DeliveryAnalysis`.

Phụ trách Policy Agent:

- Áp dụng 6 rule theo đúng thứ tự ưu tiên.
- Xác định primary issue.
- Xác định root cause.
- Xác định responsible party.
- Tính refund theo policy.
- Chọn resolution action.
- Đặt confidence theo quy tắc nhất quán.

File dự kiến:

```text
src/agents/delivery_agent.py
src/agents/policy_agent.py
src/policies.py
tests/test_delivery.py
tests/test_policy.py
```

### 3.5. Người 5 — Verifier + QA

Phụ trách:

- Định nghĩa Pydantic hoặc JSON Schema.
- Kiểm tra cấu trúc output.
- Kiểm tra entity và evidence tồn tại.
- Kiểm tra tổng tiền và refund.
- Kiểm tra giới hạn số phần tử.
- Viết test end-to-end.
- Kiểm tra đủ 50 output.
- Tạo script đóng gói ZIP.

File dự kiến:

```text
src/schemas.py
src/agents/verifier_agent.py
src/output_validator.py
tests/test_verifier.py
tests/test_end_to_end.py
scripts/validate_outputs.py
scripts/package_output.py
```

## 4. Cấu trúc thư mục đề xuất

```text
K3-Day9-Multi-Agent-A2A/
|-- data/
|-- input/
|-- output/
|-- scripts/
|   |-- inspect_data.py
|   |-- validate_outputs.py
|   `-- package_output.py
|-- src/
|   |-- agents/
|   |   |-- order_seller_agent.py
|   |   |-- payment_agent.py
|   |   |-- delivery_agent.py
|   |   |-- policy_agent.py
|   |   `-- verifier_agent.py
|   |-- coordinator.py
|   |-- data_repository.py
|   |-- llm_client.py
|   |-- policies.py
|   |-- schemas.py
|   |-- trace_writer.py
|   `-- main.py
|-- tests/
|   |-- fixtures/
|   |-- test_order_seller.py
|   |-- test_payment.py
|   |-- test_delivery.py
|   |-- test_policy.py
|   |-- test_verifier.py
|   `-- test_end_to_end.py
|-- .env.example
|-- .gitignore
|-- architecture.md
|-- metadata.json
|-- requirements.txt
`-- trace.jsonl
```

## 5. Công nghệ và quy ước chung

Đề xuất sử dụng:

```text
Ngôn ngữ: Python 3.11+
Đọc CSV: pandas
Schema: Pydantic
Tính tiền: Decimal
Kiểm thử: pytest
Biến môi trường: python-dotenv
```

Quy ước:

- Dùng `Decimal` khi tính tiền.
- Chỉ đổi sang `float` khi xuất JSON.
- Tất cả số tiền làm tròn hai chữ số thập phân.
- Không nhân `payment_value` với `payment_installments`.
- Không cho LLM tự cộng tiền hoặc tự tạo evidence.
- Timestamp được so sánh theo giá trị trong CSV, không đổi múi giờ.
- Model name phải được khai báo trong source code và `metadata.json`.
- API key chỉ đặt trong `.env`, không commit lên Git.

## 6. Contract giữa các agent

Các thành viên phải thống nhất contract trước khi triển khai module.

### 6.1. CaseInput

```json
{
  "case_id": "EC_001",
  "opened_at": "2018-10-18T00:00:00-03:00",
  "claimed_order_id": "abc123",
  "customer_message": "...",
  "language": "vi",
  "policy_version": "EC_POLICY_V1"
}
```

### 6.2. OrderSellerAnalysis

```json
{
  "order_id": "abc123",
  "order_found": true,
  "order_status": "delivered",
  "delivered_carrier_date": "2018-01-02 10:00:00",
  "delivered_customer_date": "2018-01-10 12:00:00",
  "estimated_delivery_date": "2018-01-08 00:00:00",
  "items": [
    {
      "order_item_id": 1,
      "seller_id": "seller01",
      "price_brl": 100.0,
      "freight_brl": 15.0,
      "shipping_limit_date": "2018-01-01 23:59:59",
      "seller_handoff_late": true
    }
  ],
  "item_total_brl": 100.0,
  "freight_total_brl": 15.0,
  "seller_ids": ["seller01"],
  "late_seller_ids": ["seller01"]
}
```

Seller bàn giao trễ khi:

```python
delivered_carrier_date > shipping_limit_date
```

Nếu order không có item:

```json
{
  "items": [],
  "seller_ids": [],
  "late_seller_ids": [],
  "item_total_brl": 0.0,
  "freight_total_brl": 0.0
}
```

### 6.3. PaymentAnalysis

```json
{
  "order_id": "abc123",
  "payments": [
    {
      "payment_sequential": 1,
      "payment_type": "credit_card",
      "payment_value_brl": 115.0
    }
  ],
  "payment_ids": ["abc123:1"],
  "payment_row_count": 1,
  "payment_total_brl": 115.0,
  "expected_total_brl": 115.0,
  "difference_brl": 0.0,
  "payment_matches": true,
  "is_split_payment": false
}
```

Đối soát payment:

```python
expected_total = item_total + freight_total
difference = abs(payment_total - expected_total)
payment_matches = difference <= Decimal("0.10")
```

### 6.4. DeliveryAnalysis

```json
{
  "order_id": "abc123",
  "delivered_after_estimate": true,
  "seller_handoff_after_limit": true,
  "late_seller_ids": ["seller01"],
  "timestamps_complete": true
}
```

Giao trễ khi:

```python
delivered_customer_date > estimated_delivery_date
```

### 6.5. PolicyDecision

```json
{
  "primary_issue": "late_delivery_seller",
  "case_status": "action_required",
  "confidence": 0.97,
  "root_cause_code": "SELLER_HANDOFF_AFTER_LIMIT",
  "responsible_parties": [
    {
      "party_type": "seller",
      "party_id": "seller01"
    }
  ],
  "recommended_refund_brl": 15.0,
  "resolution_actions": ["refund_freight"]
}
```

### 6.6. VerificationResult

```json
{
  "valid": true,
  "errors": [],
  "warnings": []
}
```

Nếu không hợp lệ:

```json
{
  "valid": false,
  "errors": [
    {
      "code": "INVALID_REFUND",
      "field": "financial_resolution.recommended_refund_brl",
      "message": "Refund phải bằng freight total"
    }
  ],
  "warnings": []
}
```

## 7. Workflow xử lý một case

### Bước 1 — Coordinator đọc input

Coordinator:

1. Đọc `EC_xxx.json`.
2. Validate input cơ bản.
3. Lấy `claimed_order_id`.
4. Tạo event `case_started` trong trace.

### Bước 2 — Order & Seller Agent phân tích đơn hàng

Agent thực hiện:

1. Tìm order theo `order_id`.
2. Lấy toàn bộ item.
3. Lấy seller của từng item.
4. Tính tổng item.
5. Tính tổng freight.
6. So carrier date với shipping limit của từng item.
7. Tạo `OrderSellerAnalysis`.

### Bước 3 — Payment Agent đối soát thanh toán

Agent thực hiện:

1. Lấy toàn bộ payment rows.
2. Tính tổng payment.
3. Đếm payment rows.
4. Phát hiện split payment.
5. Tính chênh lệch payment với item + freight.
6. Tạo `PaymentAnalysis`.

### Bước 4 — Delivery Agent phân tích giao hàng

Agent thực hiện:

1. So ngày giao thực tế với estimated date.
2. Kiểm tra seller handoff.
3. Xác định giao đúng hoặc trễ hạn.
4. Tạo `DeliveryAnalysis`.

### Bước 5 — Policy Agent áp dụng policy

Policy Agent nhận kết quả của ba agent trước và xét đúng thứ tự:

1. `canceled_order_paid`.
2. `unavailable_order_paid`.
3. `late_delivery_seller`.
4. `late_delivery_logistics`.
5. `valid_split_payment`.
6. `unsupported_late_claim`.

Pseudo-code:

```python
if status == "canceled" and payment_total > 0:
    issue = "canceled_order_paid"
elif status == "unavailable" and payment_total > 0:
    issue = "unavailable_order_paid"
elif delivered_late and seller_handoff_late:
    issue = "late_delivery_seller"
elif delivered_late and not seller_handoff_late:
    issue = "late_delivery_logistics"
elif payment_count >= 2 and payment_matches:
    issue = "valid_split_payment"
elif not delivered_late and payment_matches:
    issue = "unsupported_late_claim"
else:
    raise UnsupportedPolicyCase()
```

### Bước 6 — Coordinator dựng output

Coordinator kết hợp:

- Case input.
- `OrderSellerAnalysis`.
- `PaymentAnalysis`.
- `DeliveryAnalysis`.
- `PolicyDecision`.

Sau đó tạo output đúng schema đề bài.

### Bước 7 — Verifier kiểm tra

Verifier kiểm tra:

- Schema.
- Entity IDs.
- Evidence IDs.
- Tổng tiền.
- Refund.
- Root cause.
- Responsible party.
- Resolution action.
- Giới hạn số phần tử.

Nếu hợp lệ, Coordinator ghi output. Nếu không hợp lệ, output không được ghi và lỗi phải được đưa vào trace.

## 8. Bảng policy chuẩn

| Priority | Primary issue | Root cause | Responsible party | Refund | Action |
|---:|---|---|---|---:|---|
| 1 | `canceled_order_paid` | `ORDER_CANCELED_AFTER_PAYMENT` | `platform/OLIST_PLATFORM` | Tổng payment | `issue_full_refund` |
| 2 | `unavailable_order_paid` | `ORDER_UNAVAILABLE_AFTER_PAYMENT` | `platform/OLIST_PLATFORM` | Tổng payment | `issue_full_refund` |
| 3 | `late_delivery_seller` | `SELLER_HANDOFF_AFTER_LIMIT` | Seller vi phạm | Tổng freight | `refund_freight` |
| 4 | `late_delivery_logistics` | `CARRIER_DELIVERED_AFTER_ESTIMATE` | `logistics_provider/LOGISTICS_PROVIDER` | Tổng freight | `refund_freight` |
| 5 | `valid_split_payment` | `MULTIPLE_PAYMENTS_RECONCILED` | Không có | 0 | `explain_valid_split_payment` |
| 6 | `unsupported_late_claim` | `DELIVERY_WITHIN_ESTIMATE` | Không có | 0 | `reject_late_refund` |

Quy tắc case status:

```text
recommended_refund_brl > 0  => action_required
recommended_refund_brl == 0 => no_action
```

## 9. Evidence

Chỉ dùng evidence theo các định dạng:

```text
order:<order_id>
item:<order_id>:<order_item_id>
payment:<order_id>:<payment_sequential>
seller:<seller_id>
policy:<root_cause_code>
```

Thứ tự ưu tiên khi có quá nhiều evidence:

1. Order.
2. Item liên quan trực tiếp.
3. Payment.
4. Seller chịu trách nhiệm.
5. Policy.

Không được tạo:

- Tracking checkpoint không tồn tại.
- Refund transaction ID.
- Evidence giao sai hoặc giao thiếu không có trong CSV.
- Item, payment hoặc seller ID không tồn tại.

## 10. Sử dụng LLM

Tất cả agent dùng chung một model LLM dưới hoặc bằng 10B tham số.

Mỗi agent có:

- System prompt riêng.
- Phạm vi dữ liệu riêng.
- Input schema riêng.
- Output schema riêng.

Python chịu trách nhiệm:

- Truy xuất và join CSV.
- Cộng tiền.
- So sánh timestamp.
- Xác minh ID.
- Kiểm tra output.

LLM có thể hỗ trợ:

- Điều phối.
- Tóm tắt facts.
- Áp dụng policy trên facts đã xác minh.
- Sinh structured response.

LLM không được tự tạo facts, ID hoặc số tiền.

## 11. Trace

`trace.jsonl` phải chứa trace thật của lượt chạy mới nhất và phải được ghi đè khi bắt đầu lượt chạy chính thức.

Các event đề xuất:

```text
run_started
case_started
agent_started
agent_completed
handoff
verification_failed
case_completed
run_completed
```

Ví dụ:

```json
{"run_id":"run-001","case_id":"EC_001","agent":"coordinator","event":"case_started"}
{"run_id":"run-001","case_id":"EC_001","agent":"order_seller","event":"completed","summary":{"item_count":1}}
{"run_id":"run-001","case_id":"EC_001","from":"order_seller","to":"payment","event":"handoff"}
{"run_id":"run-001","case_id":"EC_001","agent":"verifier","event":"completed","valid":true}
```

Không ghi API key, secret hoặc reasoning nội bộ dài vào trace.

## 12. Kế hoạch triển khai theo giai đoạn

### Giai đoạn 0 — Chốt thiết kế

Toàn nhóm thực hiện:

1. Chốt model và provider.
2. Chốt SDK.
3. Chốt cấu trúc thư mục.
4. Chốt schema.
5. Chốt contract giữa các agent.
6. Chốt format trace.
7. Chốt quy tắc confidence.

Điều kiện hoàn thành:

- Mọi thành viên dùng cùng tên field và kiểu dữ liệu.
- Không còn contract do từng người tự đặt.

### Giai đoạn 1 — Khảo sát dữ liệu và dựng nền

Người 1:

- Tạo project skeleton.
- Tạo CLI.
- Tạo interface agent.

Người 2:

- Khảo sát CSV.
- Viết `DataRepository`.
- Chuẩn bị fixture order/item/seller.

Người 3:

- Khảo sát payment.
- Tìm order có split payment.
- Chuẩn bị fixture payment.

Người 4:

- Viết decision table.
- Tạo mapping policy.

Người 5:

- Dựng Pydantic schema.
- Tạo test skeleton.

### Giai đoạn 2 — Phát triển song song

- Người 1 xây Coordinator và Trace Writer.
- Người 2 xây Order/Seller Agent.
- Người 3 xây Payment Agent.
- Người 4 xây Delivery và Policy Agent.
- Người 5 xây Verifier và validator.

Mỗi module phải có unit test trước khi merge.

### Giai đoạn 3 — Tích hợp deterministic pipeline

Trình tự tích hợp:

1. Data Repository.
2. Order/Seller Agent.
3. Payment Agent.
4. Delivery Agent.
5. Policy Agent.
6. Verifier Agent.
7. Coordinator.

Chạy thử:

1. Một case cho mỗi loại policy.
2. Năm case.
3. Mười case.
4. Toàn bộ 50 case.

### Giai đoạn 4 — Tích hợp LLM

Chỉ thực hiện sau khi pipeline deterministic chạy đúng.

Yêu cầu:

- Có LLM client dùng chung.
- Mỗi agent dùng prompt riêng.
- Structured output có schema.
- Retry tối đa 2–3 lần.
- Lỗi API được ghi trace.
- Không log API key.

### Giai đoạn 5 — Kiểm thử và sửa lỗi

Mỗi module cần test ít nhất các trường hợp sau.

Order/Seller:

- Một item.
- Nhiều item.
- Nhiều seller.
- Seller bàn giao đúng hạn.
- Seller bàn giao trễ.
- Order không có item.
- Timestamp null.

Payment:

- Một payment.
- Nhiều payment.
- Sai lệch đúng 0.10 BRL.
- Sai lệch 0.11 BRL.
- Payment bằng 0.
- Không có payment.
- Có installments.

Delivery:

- Giao trước hạn.
- Giao đúng hạn.
- Giao trễ.
- Thiếu timestamp.

Policy:

- Đủ 6 loại primary issue.
- Kiểm tra đúng thứ tự priority.
- Kiểm tra refund, cause, party và action.

Verifier:

- Evidence sai định dạng.
- Evidence không tồn tại.
- Refund sai.
- Case status sai.
- Vượt giới hạn mảng.
- Confidence ngoài `[0,1]`.

### Giai đoạn 6 — Hoàn thiện tài liệu

Phân chia nội dung `architecture.md`:

| Nội dung | Người phụ trách |
|---|---|
| Sơ đồ, Coordinator, handoff | Người 1 |
| Data access, Order/Seller | Người 2 |
| Payment và đối soát | Người 3 |
| Delivery, Policy, LLM | Người 4 |
| Verification, test, packaging | Người 5 |

Người 1 tổng hợp và chỉnh sửa tài liệu cuối.

Mỗi người tự viết báo cáo cá nhân theo đúng phần mình trực tiếp thực hiện.

### Giai đoạn 7 — Chạy chính thức

1. Dọn output thử cũ một cách có kiểm soát.
2. Mở `trace.jsonl` ở chế độ ghi đè.
3. Chạy toàn bộ 50 case.
4. Kiểm tra không có case lỗi.
5. Chạy validator độc lập.
6. Sửa lỗi nếu có.
7. Chạy lại toàn bộ để tạo trace cuối.
8. Commit source code.
9. Đóng gói riêng `output/`.

## 13. Kiểm thử và điều kiện merge

Mỗi pull request phải có:

- Mô tả thay đổi.
- Danh sách file thay đổi.
- Input/output contract liên quan.
- Lệnh test đã chạy.
- Kết quả test.
- Ví dụ output nếu cần.
- Không chứa `.env` hoặc secret.

Thứ tự merge đề xuất:

1. Project skeleton.
2. Schema và contract.
3. Data Repository.
4. Order/Seller Agent.
5. Payment Agent.
6. Delivery Agent.
7. Policy Agent.
8. Verifier Agent.
9. Coordinator integration.
10. LLM integration.
11. Documentation.
12. Final outputs.

Branch đề xuất:

```text
feature/coordinator
feature/data-order-seller
feature/payment
feature/delivery-policy
feature/verifier-qa
```

## 14. Lịch trình mẫu bốn ngày

### Ngày 1 — Thiết kế và dữ liệu

- Chốt công nghệ và model.
- Chốt schema và contract.
- Dựng project skeleton.
- Khảo sát CSV/input.
- Tạo fixture cho 6 policy.

Kết quả cuối ngày:

- Repository đọc được dữ liệu.
- Interface agent thống nhất.
- Test skeleton chạy được.

### Ngày 2 — Xây dựng agent

- Người 2 hoàn thành Order/Seller Agent.
- Người 3 hoàn thành Payment Agent.
- Người 4 hoàn thành Delivery và Policy Agent.
- Người 5 hoàn thành Verifier cơ bản.
- Người 1 hoàn thành Coordinator skeleton và trace.

Kết quả cuối ngày:

- Các agent chạy độc lập.
- Unit test chính pass.

### Ngày 3 — Tích hợp

- Nối toàn bộ pipeline.
- Chạy thử 6 loại case.
- Tích hợp LLM.
- Chạy 10–20 case.
- Sửa lỗi contract, timestamp, tiền và evidence.

Kết quả cuối ngày:

- Pipeline end-to-end ổn định.
- Test đủ 6 policy.

### Ngày 4 — Chạy chính thức và nộp

- Chạy đủ 50 case.
- Validate độc lập.
- Sửa lỗi cuối.
- Chạy lại để tạo trace mới nhất.
- Hoàn thiện architecture và metadata.
- Hoàn thiện báo cáo cá nhân.
- Commit toàn bộ source.
- Nén riêng thư mục output.

## 15. Definition of Done

### Người 1 hoàn thành khi

- Chạy được một case và 50 case.
- Handoff đúng contract.
- Trace đầy đủ.
- Chỉ ghi output sau khi verifier pass.
- Pipeline xử lý lỗi rõ ràng.

### Người 2 hoàn thành khi

- Repository join đúng dữ liệu.
- Tổng item và freight đúng.
- Late seller đúng theo từng item.
- Xử lý được order không có item.
- Unit test pass.

### Người 3 hoàn thành khi

- Tổng payment đúng.
- Split payment đúng.
- Sai số 0.10 BRL đúng.
- Không nhân installments.
- Unit test payment pass.

### Người 4 hoàn thành khi

- Phân tích delivery đúng.
- Policy đúng thứ tự ưu tiên.
- Cause, party, refund và action đúng.
- Confidence nhất quán.
- Test đủ 6 policy.

### Người 5 hoàn thành khi

- Schema validator pass.
- Evidence được kiểm chứng.
- Financial validation đúng.
- End-to-end test pass.
- ZIP chứa đúng 50 JSON.

## 16. Checklist trước khi nộp

- [ ] Có đúng 50 file từ `EC_001.json` đến `EC_050.json`.
- [ ] Không thiếu hoặc thừa file output.
- [ ] Tất cả output parse được JSON.
- [ ] `case_id` khớp tên file.
- [ ] Tất cả evidence đúng định dạng và tồn tại.
- [ ] Mọi phép tính tiền được làm tròn hai chữ số.
- [ ] Policy áp dụng đúng thứ tự ưu tiên.
- [ ] Refund, cause, party và action đúng.
- [ ] `trace.jsonl` thuộc lượt chạy mới nhất và không append trace cũ.
- [ ] `metadata.json` khai báo đúng model và kích thước.
- [ ] Model không vượt quá 10B tham số.
- [ ] `architecture.md` đã hoàn thiện.
- [ ] Mỗi thành viên có báo cáo cá nhân.
- [ ] `.env` và API key không được commit.
- [ ] Source code đã được commit trước khi nộp.
- [ ] ZIP chỉ chứa 50 file JSON của thư mục `output/`.

## 17. Nguyên tắc thực hiện quan trọng

Thứ tự nên tuân thủ:

```text
Chốt schema và contract
    -> xử lý deterministic
    -> unit test
    -> tích hợp pipeline
    -> tích hợp LLM
    -> verifier
    -> chạy 50 case
    -> tài liệu và đóng gói
```

Không nên tích hợp LLM trước khi các phép join, tính tiền và so sánh timestamp đã được kiểm chứng bằng code.
