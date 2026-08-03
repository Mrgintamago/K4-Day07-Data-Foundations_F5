# Kết quả Benchmark — Nhóm F5 (số liệu đóng băng)

> File này do `scripts/score_all.py --save` sinh ra. **Không sửa tay.**
> Chạy lại bằng: `python scripts/score_all.py --save`

- **Ngày chạy:** 2026-08-03
- **Backend nhúng:** `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
- **Backend LLM:** `KHÔNG DÙNG (--no-llm, chỉ chấm truy xuất)`
- **top_k:** 3
- **Corpus:** `data/k4_ecommerce` (6 tài liệu)

Retrieval là **tất định**: cùng embedder và cùng chunker luôn cho cùng `gold_rank` và cùng
điểm similarity — chạy lại bao nhiêu lần cũng ra đúng bảng này.

Câu trả lời của agent do LLM sinh; script chạy `temperature=0` để tái lập được.

## Bảng tổng hợp

| # | Câu hỏi | Quang | Lê Quý Thành | Trần Quang Sáng | Cao Các Tường | Lưu Nguyễn Ngọc Hân |
|---|---------|---|---|---|---|---|
| 1 | Người mua có bao nhiêu ngày để gửi yêu cầu trả hàng hoàn tiền sau khi đơn hàng giao thành công? | 0/2 (không có) | 2/2 (hạng 1) | 0/2 (không có) | 2/2 (hạng 1) | 2/2 (hạng 1) |
| 2 | Người bán bị áp dụng những chế tài nào nếu đăng bán sản phẩm thuộc danh mục cấm? | 2/2 (hạng 1) | 1/2 (hạng 3) | 1/2 (hạng 2) | 2/2 (hạng 1) | 1/2 (hạng 2) |
| 3 | Ai chịu chi phí vận chuyển chiều hoàn trả sản phẩm? | 2/2 (hạng 1) | 0/2 (không có) | 0/2 (không có) | 1/2 (hạng 2) | 0/2 (không có) |
| 4 | Thời gian Nhà Bán cam kết bảo hành tối đa là bao lâu? | 2/2 (hạng 1) | 2/2 (hạng 1) | 2/2 (hạng 1) | 2/2 (hạng 1) | 2/2 (hạng 1) |
| 5 | Shopee thu thập dữ liệu cá nhân của người dùng từ những nguồn nào? | 2/2 (hạng 1) | 0/2 (không có) | 0/2 (không có) | 0/2 (không có) | 0/2 (không có) |
| **Tổng** | | **8/10** | **5/10** | **3/10** | **7/10** | **5/10** |
| Số chunk | | 228 | 326 | 316 | 186 | 201 |

## Chi tiết từng thành viên

### Quang — `SemanticParentChunker (custom)`

Store: **228 chunk** · Tổng điểm: **8/10**

| Câu | gold_rank | top-1 doc_id | score | Điểm | Câu trả lời của agent |
|---|---|---|---|---|---|
| 1 | — | `tiki-seller-warranty-faq` | +0.6519 | **0/2** | (bỏ qua — chế độ chỉ chấm truy xuất)… |
| 2 | 1 | `shopee-prohibited-products` | +0.7350 | **2/2** | (bỏ qua — chế độ chỉ chấm truy xuất)… |
| 3 | 1 | `shopee-returns-refund-policy` | +0.5884 | **2/2** | (bỏ qua — chế độ chỉ chấm truy xuất)… |
| 4 | 1 | `tiki-seller-warranty-faq` | +0.7775 | **2/2** | (bỏ qua — chế độ chỉ chấm truy xuất)… |
| 5 | 1 | `shopee-privacy-policy` | +0.6938 | **2/2** | (bỏ qua — chế độ chỉ chấm truy xuất)… |

### Lê Quý Thành — `ThanhRecursiveChunker (Recursive tuned)`

Store: **326 chunk** · Tổng điểm: **5/10**

| Câu | gold_rank | top-1 doc_id | score | Điểm | Câu trả lời của agent |
|---|---|---|---|---|---|
| 1 | 1 | `shopee-returns-refund-policy` | +0.8052 | **2/2** | (bỏ qua — chế độ chỉ chấm truy xuất)… |
| 2 | 3 | `shopee-prohibited-products` | +0.7232 | **1/2** | (bỏ qua — chế độ chỉ chấm truy xuất)… |
| 3 | — | `shopee-returns-refund-policy` | +0.6276 | **0/2** | (bỏ qua — chế độ chỉ chấm truy xuất)… |
| 4 | 1 | `tiki-seller-warranty-faq` | +0.7833 | **2/2** | (bỏ qua — chế độ chỉ chấm truy xuất)… |
| 5 | — | `shopee-privacy-policy` | +0.7426 | **0/2** | (bỏ qua — chế độ chỉ chấm truy xuất)… |

### Trần Quang Sáng — `FixedSizeChunker (tuned)`

Store: **316 chunk** · Tổng điểm: **3/10**

| Câu | gold_rank | top-1 doc_id | score | Điểm | Câu trả lời của agent |
|---|---|---|---|---|---|
| 1 | — | `shopee-returns-refund-policy` | +0.7226 | **0/2** | (bỏ qua — chế độ chỉ chấm truy xuất)… |
| 2 | 2 | `shopee-prohibited-products` | +0.7491 | **1/2** | (bỏ qua — chế độ chỉ chấm truy xuất)… |
| 3 | — | `ghn-compensation-policy` | +0.6449 | **0/2** | (bỏ qua — chế độ chỉ chấm truy xuất)… |
| 4 | 1 | `tiki-seller-warranty-faq` | +0.8106 | **2/2** | (bỏ qua — chế độ chỉ chấm truy xuất)… |
| 5 | — | `shopee-privacy-policy` | +0.7192 | **0/2** | (bỏ qua — chế độ chỉ chấm truy xuất)… |

### Cao Các Tường — `SentenceChunker (tuned)`

Store: **186 chunk** · Tổng điểm: **7/10**

| Câu | gold_rank | top-1 doc_id | score | Điểm | Câu trả lời của agent |
|---|---|---|---|---|---|
| 1 | 1 | `shopee-returns-refund-policy` | +0.7383 | **2/2** | (bỏ qua — chế độ chỉ chấm truy xuất)… |
| 2 | 1 | `shopee-prohibited-products` | +0.7311 | **2/2** | (bỏ qua — chế độ chỉ chấm truy xuất)… |
| 3 | 2 | `ghn-compensation-policy` | +0.6065 | **1/2** | (bỏ qua — chế độ chỉ chấm truy xuất)… |
| 4 | 1 | `tiki-seller-warranty-faq` | +0.8320 | **2/2** | (bỏ qua — chế độ chỉ chấm truy xuất)… |
| 5 | — | `shopee-privacy-policy` | +0.7602 | **0/2** | (bỏ qua — chế độ chỉ chấm truy xuất)… |

### Lưu Nguyễn Ngọc Hân — `FAQPairChunker (custom)`

Store: **201 chunk** · Tổng điểm: **5/10**

| Câu | gold_rank | top-1 doc_id | score | Điểm | Câu trả lời của agent |
|---|---|---|---|---|---|
| 1 | 1 | `shopee-returns-refund-policy` | +0.7493 | **2/2** | (bỏ qua — chế độ chỉ chấm truy xuất)… |
| 2 | 2 | `shopee-prohibited-products` | +0.6873 | **1/2** | (bỏ qua — chế độ chỉ chấm truy xuất)… |
| 3 | — | `ghn-compensation-policy` | +0.6164 | **0/2** | (bỏ qua — chế độ chỉ chấm truy xuất)… |
| 4 | 1 | `tiki-seller-warranty-faq` | +0.8226 | **2/2** | (bỏ qua — chế độ chỉ chấm truy xuất)… |
| 5 | — | `shopee-privacy-policy` | +0.7409 | **0/2** | (bỏ qua — chế độ chỉ chấm truy xuất)… |

