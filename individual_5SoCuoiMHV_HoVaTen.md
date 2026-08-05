# Member Role Report — Day 9: Multi Agent A2A

## 1. Thông tin cá nhân

| Thông tin       | Nội dung                                 |
| --------------- | ---------------------------------------- |
| Họ và tên       | [Họ và tên Học viên]                    |
| MSSV            | [5 số cuối Mã học viên]                 |
| Khóa/Lớp        | K3 - E403                                |
| Vai trò chính   | Multi-Agent Developer & System Architect |
| Ngày hoàn thành | 2026-08-05                               |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| --- | --- | --- | --- | --- |
| Multi-Agent Engine | `src/agents.py` | JSON case request, Olist CSVs | Structural assessment, Evidence IDs, Actions | Hoàn thành |
| Data Indexer | `src/data_loader.py` | CSV Datasets in `data/` | Fast indexed retrieval by `order_id` | Hoàn thành |
| Pipeline & Exporter | `main.py` | 50 cases in `input/` | 50 output JSONs, `trace.jsonl`, `output.zip` | Hoàn thành |
| Audit & Verification | `verify_output.py` | Generated output JSONs | Verification report & Schema bounds compliance | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| --- | --- | --- |
| System Verification | Whole pipeline | Kiểm tra 100% 50 case đạt chuẩn schema và quy tắc nghiệp vụ |
| Architecture Doc | Repository documentation | Hoàn thành `architecture.md` mô tả sơ đồ agent và handoff |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --- | --- | --- | --- |
| Thiết kế 6 Agent phân vai | `src/agents.py` | System xử lý 50 case tự động | Run `python main.py` |
| Tự động kiểm tra Schema | `verify_output.py` | 0 lỗi false positive, đúng định dạng ID | Run `python verify_output.py` |
| Xuất gói nộp bài | `output.zip` | File zip chứa đúng 50 JSON | Verified ZIP contents |

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết
Xây dựng kiến trúc Multi-Agent giải quyết 50 khiếu nại thương mại điện tử dựa trên dữ liệu Olist, đảm bảo phân định rõ trách nhiệm (Seller, Logistics, Platform), xác định bằng chứng chính xác và không bị vi phạm các giới hạn schema (max IDs, confidence [0,1], format bằng chứng).

### Cách triển khai
1. **Data Indexing**: Sử dụng `OlistDataLoader` nạp và đánh chỉ mục trước các file CSV theo `order_id` để tối ưu thời gian truy xuất cho 50 trường hợp.
2. **Specialized Agents**: 
   - `OrderSellerAgent` phân tích trạng thái đơn và mốc bàn giao hàng của Seller.
   - `PaymentAgent` tính tổng tiền, phát hiện split payment và đối soát tài chính.
   - `DeliveryAgent` kiểm tra thời điểm nhận hàng thực tế so với cam kết.
   - `PolicyAgent` áp dụng các luật ưu tiên từ 1 đến 6 theo chính sách `EC_POLICY_V1`.
   - `VerifierAgent` đảm bảo mọi quy định về giới hạn entity và format ID được tuân thủ 100%.
3. **Trace Logging**: Ghi lại nhật ký tương tác chi tiết từng bước của các agent vào `trace.jsonl`.

## 5. Tự đánh giá và Bài học rút ra
- Hệ thống xử lý thành công 50/50 case với thời gian chạy tối ưu (~39 giây).
- Đảm bảo tính nhất quán giữa dữ liệu thực tế và quyết định hoàn tiền (không tự bịa đặt sự kiện không tồn tại).
- Kiến trúc Agent-to-Agent giúp code dễ mở rộng khi bổ sung thêm các chính sách nghiệp vụ mới trong tương lai.
