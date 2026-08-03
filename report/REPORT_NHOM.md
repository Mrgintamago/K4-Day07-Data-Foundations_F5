# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** [Tên nhóm]
**Thành viên:** [Họ tên từng thành viên]
**Ngày:** [Ngày nộp]

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Phạm vi bộ tài liệu (Scope)

**Chủ đề (cố định theo lớp K4):** Chính sách thương mại điện tử / hỗ trợ khách hàng (thanh toán, đổi trả, giao hàng, quyền riêng tư, điều kiện người bán…).

**Phạm vi cụ thể nhóm tập trung:**
> *1 câu — ví dụ: đổi trả + điều kiện người bán.*

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [ ] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [ ] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| | | | |
| | | | |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| | FixedSizeChunker (`fixed_size`) | | | |
| | SentenceChunker (`by_sentences`) | | | |
| | RecursiveChunker (`recursive`) | | | |

### Chiến lược của từng thành viên

> Mỗi thành viên điền một khối dưới đây (copy thêm nếu nhóm có nhiều hơn 3 người).

**Thành viên 1 — [Tên]**
- **Loại chiến lược:** [FixedSize / Sentence / Recursive / custom]
- **Mô tả & lý do chọn cho chủ đề này:** *(2-3 câu)*
- **Code snippet (nếu custom):**
```python
# Dán mã nguồn (implementation) vào đây
```

**Thành viên 2 — [Tên]**
- **Loại chiến lược:**
- **Mô tả & lý do chọn:**
- **Code snippet (nếu custom):**

**Thành viên 3 — [Tên]**
- **Loại chiến lược:**
- **Mô tả & lý do chọn:**
- **Code snippet (nếu custom):**

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| | | | | |
| | | | | |
| | | | | |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> *Viết 2-3 câu — đây là phần được đánh giá cao nhất (khả năng suy nghĩ & giải thích):*

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

Bộ câu hỏi này được khóa trong mã nguồn tại `scripts/run_benchmark.py` (hằng `QUERIES`) để
đảm bảo cả 5 thành viên chạy **đúng cùng một bộ**, không ai sửa lệch.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Người mua có bao nhiêu ngày để gửi yêu cầu trả hàng/hoàn tiền sau khi đơn hàng giao thành công? | **15 (mười lăm) ngày** kể từ lúc đơn hàng được cập nhật giao hàng thành công. Riêng thực phẩm **tươi sống và đông lạnh: 24 giờ**. | `shopee-returns-refund-policy` — **mục 3.2** |
| 2 | Người bán bị áp dụng những chế tài nào nếu đăng bán sản phẩm thuộc danh mục cấm/hạn chế? | 5 nhóm chế tài: (i) sản phẩm bị xóa; (ii) tài khoản bị giới hạn quyền; (iii) tài khoản bị đình chỉ hoặc xóa; (iv) cấn trừ số dư, phong tỏa quyền rút tiền; (v) chế tài khác theo pháp luật (phạt hành chính, xử lý hình sự, bồi thường thiệt hại). | `shopee-prohibited-products` — **mục 3** |
| 3 | Ai chịu chi phí vận chuyển chiều hoàn trả sản phẩm? | **Người Bán** chịu, trong 3 trường hợp: Shopee chấp thuận yêu cầu trả hàng/hoàn tiền không do lỗi Người Mua hoặc đơn vị vận chuyển; đơn giao không thành công; các ngoại lệ khác theo quyết định của Shopee. | `shopee-returns-refund-policy` — **mục 7.1** |
| 4 | Thời gian Nhà Bán cam kết bảo hành tối đa là bao lâu? | **Tối đa không quá 30 ngày**, tính từ thời điểm Nhà Bán nhận được hàng đến khi bảo hành xong — **không tính thời gian vận chuyển**. | `tiki-seller-warranty-faq` — **câu hỏi số 5** |
| 5 | Shopee thu thập dữ liệu cá nhân của người dùng từ những nguồn nào? | Từ chính bạn, các công ty liên kết, các bên thứ ba và nguồn khác: đối tác kinh doanh (đơn vị vận chuyển, thanh toán), cơ quan đánh giá tín dụng, đối tác marketing/giới thiệu/khách hàng thân thiết, người dùng khác, và các nguồn dữ liệu công khai hoặc của nhà nước. | `shopee-privacy-policy` — **mục 2.2** |

**Câu bắt buộc dùng metadata filter** (theo `K4_VARIANT.md`):

| # | `metadata_filter` | Vì sao cần |
|---|---|---|
| 2 | `{"customer_role": "seller"}` | Chế tài chỉ áp dụng cho Người Bán; không lọc thì tài liệu phía người mua chen vào top-3 |
| 4 | `{"customer_role": "seller"}` | "Nhà Bán cam kết bảo hành" là nghĩa vụ của người bán, nằm trong tài liệu dành riêng cho seller |

**Vì sao 5 câu này đa dạng** (yêu cầu của `exercises.md` bài 3.2): mỗi câu thử một điểm yếu
khác nhau của chunking —

| # | Dạng câu hỏi | Thử điểm yếu nào |
|---|---|---|
| 1 | Con số / thời hạn cụ thể | Chunk bị cắt giữa câu chứa con số |
| 2 | Danh sách liệt kê nhiều mục | Chunk quá nhỏ làm đứt danh sách |
| 3 | Quy trách nhiệm (ai chịu gì) | Tiêu đề mục mang thông tin, thân mục thiếu ngữ cảnh |
| 4 | Cam kết dịch vụ dạng FAQ | Lợi thế của chunking theo cặp Hỏi–Đáp |
| 5 | Tổng hợp nguồn, tài liệu rất dài | Nhiều mục cùng chủ đề cạnh tranh nhau |

**Kiểm chứng gold answer:** cả 5 câu trả lời chuẩn đều được trích nguyên văn từ corpus của nhóm
(không dùng nguồn ngoài), có thể kiểm tra lại bằng:

```bash
grep -n "15 (mười lăm) ngày"            data/k4_ecommerce/shopee-returns-refund-policy.md
grep -n "(i) Sản phẩm bị xóa"            data/k4_ecommerce/shopee-prohibited-products.md
grep -n "Người Bán sẽ chịu chi phí"      data/k4_ecommerce/shopee-returns-refund-policy.md
grep -n "tối đa không quá 30 ngày"       data/k4_ecommerce/tiki-seller-warranty-faq.md
grep -n "cơ quan đánh giá tín dụng"      data/k4_ecommerce/shopee-privacy-policy.md
```

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |
| 5 | | | | |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> *Viết 2-3 câu:*

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> *Liệt kê 2-3 ý:*

**Bài học rút ra khi so sánh trong nhóm:**
> *Viết 2-3 câu — cùng tài liệu nhưng chiến lược khác nhau dẫn tới khác biệt gì?*

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> *Viết 2-3 câu:*

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | / 10 |
| Thiết kế chiến lược (Strategy Design) | / 15 |
| Chất lượng truy xuất (Retrieval Quality) | / 10 |
| Thuyết trình (Demo) | / 5 |
| **Tổng phần nhóm** | **/ 40** |
