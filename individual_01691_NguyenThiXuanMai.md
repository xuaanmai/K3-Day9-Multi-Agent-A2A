# Báo cáo cá nhân — Nguyễn Thị Xuân Mai

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
|---|---|
| Họ và tên | Nguyễn Thị Xuân Mai |
| MSSV | 2A202601691 |
| Khóa/Lớp | K3 |
| Vai trò chính | Role 2 — Data + Order/Seller Agent |
| Ngày hoàn thành | 2026-08-05 |

## 2. Vai trò và phạm vi công việc

| Module/deliverable | File/hàm phụ trách | Input | Output | Trạng thái |
|---|---|---|---|---|
| Data Repository | `src/data_repository.py` | 9 file CSV Olist | Các hàm truy xuất theo `order_id` | Hoàn thành |
| Order/Seller Agent | `src/agents/order_seller_agent.py` | Order row và item rows | `OrderSellerAnalysis` | Hoàn thành |
| Data tests | `tests/test_data_repository.py`, `tests/test_order_seller.py` | Dữ liệu fixture/Olist | Kết quả kiểm chứng join và tổng tiền | Hoàn thành |

Việc hỗ trợ: cung cấp contract dữ liệu cho Payment, Delivery và Verifier; hỗ trợ xác định định dạng entity/evidence từ row CSV thật.

## 3. Kết quả theo vai trò

| Nhiệm vụ | Artifact | Kết quả | Cách xác minh |
|---|---|---|---|
| Nạp và truy xuất dữ liệu | `DataRepository` | Truy xuất order, items, payments và kiểm tra seller/item/payment tồn tại | `python -m pytest tests/test_data_repository.py -q` |
| Phân tích order và seller | `OrderSellerAgent.process` | Tính item total, freight total, seller IDs và seller handoff late | `python -m pytest tests/test_order_seller.py -q` |
| Handoff cho agent sau | `OrderSellerAnalysis` trong `src/schemas.py` | Contract thống nhất cho Payment/Delivery/Policy | `python -m pytest -q` |

Output cụ thể: facts của 50 order được truy xuất theo `claimed_order_id`, không suy diễn tracking hoặc refund ledger không tồn tại.

## 4. Giải thích kỹ thuật

### Vấn đề cần giải quyết

Mỗi order có thể có nhiều item và seller; tổng tiền hàng, freight và trách nhiệm seller phải được tính từ đúng các row của order đó.

### Cách triển khai

`DataRepository` đọc CSV với `dtype=str`, chuẩn hóa `NaN` thành `None` và cung cấp các hàm `get_order`, `get_order_items`, `get_order_payments`, `seller_exists`, `item_exists`, `payment_exists`. `OrderSellerAgent` duyệt item, cộng `price` và `freight_value`, tạo entity/evidence, đồng thời so sánh `order_delivered_carrier_date > shipping_limit_date` theo từng item.

### Input, output và contract

| Thành phần | Mô tả |
|---|---|
| Input | `claimed_order_id`, order row, item rows |
| Output | `OrderSellerAnalysis` |
| Module phụ thuộc | `src/data_repository.py`, `src/schemas.py` |
| Module sử dụng output | Payment, Delivery, Policy, Verifier |
| Lỗi cần xử lý | Order không tồn tại, không có item, timestamp null, nhiều item/seller |

### Cách xác minh

```powershell
python -m pytest tests/test_data_repository.py tests/test_order_seller.py -q
```

- Kết quả mong đợi: truy xuất đúng row và tổng tiền.
- Kết quả thực tế: toàn bộ test dự án pass; 50 output qua kiểm chứng CSV.
- Artifact: `output/`, `trace.jsonl`.

## 5. Quyết định kỹ thuật quan trọng

- Bối cảnh: cần quyết định đưa toàn bộ CSV cho LLM hay truy xuất bằng code.
- Phương án cân nhắc: để LLM đọc dữ liệu thô; hoặc dùng repository deterministic rồi chỉ handoff facts.
- Phương án chọn: repository deterministic.
- Lý do: tránh hallucination, join sai order và tính sai tổng; dễ tái hiện và kiểm thử.
- Bằng chứng: `python scripts\validate_outputs.py` trả 50/50 output hợp lệ.

## 6. Lỗi hoặc blocker đã xử lý

- Triệu chứng: ID và số tiền từ CSV đều được đọc dưới dạng chuỗi, một số ô có `NaN`.
- Nguyên nhân gốc: pandas tự suy luận kiểu có thể làm mất tính nhất quán ID và null.
- Cách xử lý: đọc `dtype=str`, chuẩn hóa row và chỉ ép kiểu tại thời điểm tính toán.
- Xác minh: test repository và Order/Seller Agent pass.
- Bài học: giữ ID dưới dạng chuỗi; chỉ chuyển kiểu cho trường nghiệp vụ cần tính.

## 7. Hiểu biết luồng end-to-end

Input cung cấp `claimed_order_id`; Coordinator dùng DataRepository lấy facts, sau đó Order/Seller, Payment và Delivery lần lượt phân tích domain. Policy áp dụng sáu rule theo priority. Verifier đọc lại CSV để kiểm tra entity, evidence, totals và refund trước khi ghi output. Ollama `qwen2.5:0.5b` kiểm duyệt mỗi handoff nhưng không được tự quyết định số tiền.

## 8. Cam kết

- [x] Báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi hiểu luồng end-to-end, không chỉ module mình phụ trách.
- [x] Chỉ ghi kết quả đã được kiểm chứng.
- [x] Báo cáo không chứa API key, token hoặc secret.
- [x] Báo cáo không sao chép nguyên văn báo cáo thành viên khác.

**Họ và tên:** Nguyễn Thị Xuân Mai  
**Ngày xác nhận:** 2026-08-05
