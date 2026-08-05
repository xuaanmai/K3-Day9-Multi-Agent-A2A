# Kiến trúc Multi-Agent — E-Commerce Dispute Resolution (A2A)

Tài liệu này mô tả sơ đồ kiến trúc hệ thống multi-agent, phân định vai trò, quyền truy cập dữ liệu và quy trình giao tiếp (handoff) giữa các agent trong bài lab giải quyết khiếu nại thương mại điện tử Olist.

---

## 1. Sơ đồ Kiến trúc Multi-Agent & Luồng Handoff

```mermaid
flowchart TD
    Input[Input Case JSON: EC_xxx.json] --> Coordinator[Coordinator Agent]
    
    subgraph Data Layer
        Repo[DataRepository - Olist CSVs]
    end

    subgraph Domain Investigation Agents
        Coordinator -->|Handoff 1: Raw Facts & Order ID| OrderSellerAgent[Order & Seller Agent]
        OrderSellerAgent -->|Facts: Status, Items, Freight, Limits| PaymentAgent[Payment Agent]
        PaymentAgent -->|Facts: Payments, Reconciled Totals| DeliveryAgent[Delivery Agent]
    end

    subgraph Resolution & Quality Assurance Agents
        DeliveryAgent -->|Facts: Timelines & Handoff Flags| PolicyAgent[Policy Agent]
        PolicyAgent -->|Draft Resolution & Refund| VerifierAgent[Verifier Agent]
    end

    subgraph Logging & Tracing
        Coordinator -.->|Write trace events| TraceWriter[TraceWriter: trace.jsonl]
        Domain Investigation Agents -.->|Write handoff step log| TraceWriter
    end

    VerifierAgent -->|Verified Output JSON| Output[Output JSON: output/EC_xxx.json]
```

---

## 2. Danh sách Agent & Vai trò

| Tên Agent | Module File | Vai trò & Quyền hạn | Input nhận vào | Output bàn giao |
| :--- | :--- | :--- | :--- | :--- |
| **Coordinator Agent** | `src/coordinator.py` | Điều phối toàn bộ pipeline, kiểm soát state `CaseContext`, quản lý log trace và khởi tạo luồng agent. | Raw `case` JSON từ `input/` | Struct output JSON cho case hoặc báo lỗi |
| **Order & Seller Agent** | `src/agents/order_seller_agent.py` | Tra cứu trạng thái đơn hàng (`orders`), các mặt hàng (`order_items`), người bán (`sellers`), tính tổng tiền hàng, tiền vận chuyển và kiểm tra mốc `shipping_limit_date`. | `CaseContext` | `OrderSellerAnalysis` bổ sung vào Context |
| **Payment Agent** | `src/agents/payment_agent.py` | Đọc bảng giao dịch thanh toán (`order_payments`), đối soát thanh toán nhiều đợt (split payment) với tổng đơn hàng trong sai số $\le 0.10$ BRL. | `CaseContext` (có `OrderSellerAnalysis`) | `PaymentAnalysis` bổ sung vào Context |
| **Delivery Agent** | `src/agents/delivery_agent.py` | So sánh thời gian giao thực tế (`order_delivered_customer_date`) với thời hạn ước tính (`order_estimated_delivery_date`) và thời gian carrier nhận hàng. | `CaseContext` | `DeliveryAnalysis` bổ sung vào Context |
| **Policy Agent** | `src/agents/policy_agent.py` | Áp dụng chính sách `EC_POLICY_V1` theo thứ tự ưu tiên nghiệp vụ, xác định `primary_issue`, bên chịu trách nhiệm, khoản hoàn đề xuất và danh sách `evidence_ids`. | `CaseContext` với đầy đủ kết quả từ 3 domain agents | `PolicyResolution` bổ sung vào Context |
| **Verifier Agent** | `src/agents/verifier_agent.py` | Kiểm tra tính hợp lệ của tất cả entity ID, số lượng giới hạn (tối đa 5 IDs/entity, 10 evidence IDs), format evidence, tính nhất quán tài chính và đóng gói JSON cuối cùng. | `CaseContext` có draft resolution từ Policy Agent | Struct output JSON đạt chuẩn hoặc thông báo lỗi audit |

---

## 3. Luồng Handoff (Agent-to-Agent Handoff Workflow)

1. **Khởi tạo (Initialization)**:
   - `Coordinator` nhận dữ liệu đầu vào `EC_xxx.json`.
   - `Coordinator` gọi `DataRepository` để tra cứu các bản ghi Olist liên quan đến `claimed_order_id`.
   - Tạo đối tượng `CaseContext` lưu giữ trạng thái shared state giữa các agent.
   - Ghi event `case_start` vào `trace.jsonl`.

2. **Giai đoạn Phân tích Domain (Domain Analysis Phase)**:
   - **Handoff 1**: `Coordinator` chuyển `CaseContext` sang `OrderSellerAgent`. Agent phân tích items, sellers, mốc giao hàng của seller và tính tổng `item_total_brl`, `freight_total_brl`.
   - **Handoff 2**: Context tiếp tục chuyển sang `PaymentAgent`. Agent đối soát tổng thanh toán `payment_total_brl` với tổng đơn hàng (`item + freight`) và xác nhận logic split payment.
   - **Handoff 3**: Context tiếp tục chuyển sang `DeliveryAgent`. Agent xác định tình trạng trễ hạn giao thực tế so với estimated delivery date.

3. **Giai đoạn Ra quyết định Chính sách (Policy Decision Phase)**:
   - **Handoff 4**: Context chứa đầy đủ bằng chứng từ 3 domain agent được handoff cho `PolicyAgent`.
   - `PolicyAgent` đánh giá quy tắc ưu tiên trong `EC_POLICY_V1` (Canceled order paid > Unavailable order paid > Late delivery seller > Late delivery logistics > Valid split payment > Unsupported late claim).
   - Xác định `primary_issue`, `case_status`, `recommended_refund_brl`, `ranked_causes`, `responsible_parties` và xây dựng `evidence_ids`.

4. **Giai đoạn Kiểm tra & Xác minh (Verification Phase)**:
   - **Handoff 5**: Context được handoff cho `VerifierAgent`.
   - `VerifierAgent` thực hiện audit hard bounds (cap giới hạn 5 entity IDs, 10 evidence IDs, 3 root causes, 3 responsible parties, 5 actions), kiểm tra định dạng evidence ID (`order:`, `item:`, `payment:`, `seller:`, `policy:`).
   - Trả về payload JSON kết quả cuối cùng.

5. **Ghi vết & Hoàn tất (Trace Logging & Finish)**:
   - `Coordinator` ghi log event `case_finish` vào `trace.jsonl`.
   - Kết quả được ghi ra file `output/EC_xxx.json`.

---

## 4. Quyền Truy Cập Dữ Liệu (Data Access Permissions)

- Tất cả các agent đều hoạt động theo nguyên tắc **Read-Only** trên dữ liệu Olist CSV via `DataRepository`.
- Mỗi agent chỉ cập nhật đúng sub-key tương ứng trong `CaseContext`:
  - `OrderSellerAgent` $\rightarrow$ `context.order_seller`
  - `PaymentAgent` $\rightarrow$ `context.payment`
  - `DeliveryAgent` $\rightarrow$ `context.delivery`
  - `PolicyAgent` $\rightarrow$ `context.policy`
  - `VerifierAgent` $\rightarrow$ `context.verification_errors`
- `TraceWriter` là module duy nhất ghi đè/append dữ liệu vào `trace.jsonl`.
