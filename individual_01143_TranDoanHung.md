# Báo cáo cá nhân — Trần Doãn Hưng

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
|---|---|
| Họ và tên | Trần Doãn Hưng |
| MSSV | 2A202601143 |
| Khóa/Lớp | K3 |
| Vai trò chính | Role 5 — Verifier + QA |
| Ngày hoàn thành | 2026-08-05 |

## 2. Vai trò và phạm vi công việc

| Module/deliverable | File/hàm phụ trách | Input | Output | Trạng thái |
|---|---|---|---|---|
| Shared schema | `src/schemas.py` | Contract đề bài | Pydantic models | Hoàn thành |
| Evidence validation | `src/evidence_validator.py` | Evidence ID | Kết quả format validation | Hoàn thành |
| Verifier Agent | `src/agents/verifier_agent.py` | Draft output + repository | Verified output hoặc lỗi | Hoàn thành |
| Batch validators | `src/output_validator.py`, `src/trace_validator.py` | 50 output và trace | Validation reports | Hoàn thành |
| QA tests | `tests/test_verifier.py`, `tests/test_stage3_validation.py`, `tests/test_end_to_end.py` | Fixtures/pipeline | Regression và E2E results | Hoàn thành |

Việc hỗ trợ: nối Verifier với Coordinator, kiểm tra output/trace cuối; chuẩn bị output sẵn sàng để nhóm tự đóng gói ZIP.

## 3. Kết quả theo vai trò

| Nhiệm vụ | Artifact | Kết quả | Cách xác minh |
|---|---|---|---|
| Kiểm tra schema và limits | `CaseOutput` | Chặn confidence/list/action/evidence sai | `python -m pytest tests/test_verifier.py -q` |
| Kiểm tra CSV-backed facts | `VerifierAgent` | Kiểm tra entity, totals và refund | `python scripts\validate_outputs.py` |
| Kiểm tra trace | `validate_trace_file` | 50 case × 6 agent, invocation thật | `python scripts\validate_trace.py` |
| E2E/regression | `tests/` | 73 test pass | `python -m pytest -q` |

Kết quả cụ thể: 50/50 output hợp lệ, trace 300/300 dòng hợp lệ, không có error.

## 4. Giải thích kỹ thuật

### Vấn đề cần giải quyết

Output có thể đúng schema nhưng vẫn chứa ID không tồn tại, tổng tiền sai hoặc refund không đúng policy. Verifier cần kiểm tra cả cấu trúc lẫn tính đúng theo CSV.

### Cách triển khai

Pydantic kiểm tra type, enum và giới hạn. Evidence validator chỉ cho phép năm định dạng đề bài. Verifier sử dụng `DataRepository` để kiểm tra order/item/seller/payment, tính lại item/freight/payment bằng `Decimal`, suy ra expected refund và case status. Batch validator kiểm tra đủ đúng 50 file; trace validator kiểm tra đúng 300 event và thứ tự sáu agent.

### Input, output và contract

| Thành phần | Mô tả |
|---|---|
| Input | Candidate `CaseOutput`, `DataRepository` |
| Output | `VerificationResult(valid, errors, warnings)` |
| Module phụ thuộc | schemas, repository, policies |
| Module sử dụng output | Coordinator và CLI |
| Lỗi cần xử lý | Evidence giả, entity không tồn tại, total/refund sai, trace thiếu |

### Cách xác minh

```powershell
python -m pytest -q
python scripts\validate_outputs.py
python scripts\validate_trace.py
```

- Kết quả mong đợi: 73 test pass; 50 output và 300 trace event hợp lệ.
- Kết quả thực tế: đạt toàn bộ điều kiện trên.
- Artifact: `output/`, `trace.jsonl` và validation scripts.

## 5. Quyết định kỹ thuật quan trọng

- Bối cảnh: Verifier cũ tự cắt list hoặc sửa confidence/status.
- Phương án cân nhắc: tự sửa output; hoặc báo lỗi và dừng pipeline.
- Phương án chọn: báo lỗi, không sửa âm thầm.
- Lý do: tránh che lỗi của agent trước và giữ auditability.
- Bằng chứng: fixture invalid tạo mã lỗi rõ ràng; output chỉ được ghi sau khi pass.

## 6. Lỗi hoặc blocker đã xử lý

- Triệu chứng: output đúng format nhưng evidence/entity có thể không tồn tại trong CSV.
- Nguyên nhân gốc: schema chỉ kiểm tra hình dạng, không kiểm tra nguồn dữ liệu.
- Cách xử lý: thêm semantic validation bằng DataRepository và test từng mã lỗi.
- Xác minh: `validate_outputs.py` báo 50/50 valid, error count 0.
- Bài học: schema validation và source-of-truth validation là hai lớp khác nhau.

## 7. Hiểu biết luồng end-to-end

Coordinator tạo shared context; các domain agent bổ sung facts; Policy tạo draft resolution. Verifier là hard gate cuối: nếu schema, evidence, entity, totals hoặc refund sai thì pipeline dừng. Chỉ output pass mới được ghi và trace ghi invocation thật của sáu vai trò.

## 8. Cam kết

- [x] Báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi hiểu luồng end-to-end.
- [x] Chỉ ghi kết quả đã kiểm chứng.
- [x] Không chứa secret.
- [x] Không sao chép báo cáo thành viên khác.

**Họ và tên:** Trần Doãn Hưng  
**Ngày xác nhận:** 2026-08-05
