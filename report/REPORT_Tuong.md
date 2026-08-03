# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Cao Các Tường  
**MSSV:** 2A202601236  
**Nhóm:** F5  
**Ngày:** 2026-08-03
**Chiến lược cá nhân:** `SentenceChunker` — `src/strategies/tuong_sentence.py`

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity)
**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Hai vector nhúng (embedding) chỉ về cùng một hướng trong không gian ngữ nghĩa, tức là hai đoạn văn bản nói về **cùng một ý** dù dùng từ ngữ khác nhau. Điểm gần 1 nghĩa là rất giống nghĩa, gần 0 là không liên quan, gần -1 là đối lập về hướng.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Tôi muốn trả lại đơn hàng vì sản phẩm bị lỗi."
- Câu B: "Làm sao để hoàn trả hàng hóa không đúng mô tả?"
- Tại sao tương đồng: cùng **ý định đổi trả hàng** của người mua; các từ "trả lại / hoàn trả", "lỗi / không đúng mô tả" nằm rất gần nhau trong không gian embedding dù mặt chữ khác hẳn.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Phí vận chuyển được tính theo khối lượng và khoảng cách."
- Câu B: "Chính sách bảo mật quy định cách sàn xử lý dữ liệu cá nhân."
- Tại sao khác: hai chủ đề chính sách hoàn toàn tách biệt (giao hàng vs quyền riêng tư), không chia sẻ khái niệm nào nên hai vector gần như vuông góc.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine chỉ đo **hướng**, đã chuẩn hóa theo độ lớn vector, nên một đoạn dài và một câu ngắn cùng nội dung vẫn được coi là giống nhau. Euclid lại bị ảnh hưởng bởi độ lớn (norm) — vốn phản ánh độ dài/tần suất từ hơn là ý nghĩa — nên một chunk dài sẽ bị "phạt" oan chỉ vì nó dài.

### Bài toán tính toán Chunking
**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:* bước trượt (step) = `chunk_size - overlap` = `500 - 50` = **450** ký tự.
> Số chunk = `ceil((10000 - 50) / 450)` = `ceil(9950 / 450)` = `ceil(22.11)` = **23**
> *Đáp án:* **23 chunks**

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Step giảm còn 400 → `ceil((10000 - 100) / 400)` = `ceil(24.75)` = **25 chunks**, tức **tăng 2 chunk** (+8,7% dung lượng lưu trữ và chi phí nhúng). Đổi lại, overlap lớn hơn giúp một câu/điều khoản nằm vắt qua ranh giới chunk vẫn xuất hiện **trọn vẹn** trong ít nhất một chunk — rất quan trọng với văn bản chính sách, nơi một điều kiện ("trong vòng 7 ngày kể từ ngày nhận hàng") bị cắt đôi sẽ khiến truy xuất trả về chunk vô nghĩa.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Đây là chiến lược tôi được phân công. Hướng tiếp cận của nó là dùng regex **lookbehind** `re.split(r"(?<=[.!?])\s+", text)`: cắt tại khoảng trắng *đứng sau* dấu `.`, `!`, `?` nên dấu câu được **giữ lại ở cuối câu** thay vì bị nuốt mất. Cách này đảm bảo không bao giờ cắt giữa câu, giúp các chunk luôn mạch lạc về mặt ngôn ngữ. Sau khi tách thành câu, tôi sẽ gom chúng lại thành các chunk lớn hơn, mỗi chunk không quá `max_sentences_per_chunk` câu.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> `_split` là hàm đệ quy với **2 base case**: (1) `len(text) <= chunk_size` → trả `[text]`; (2) hết separator (hoặc gặp separator `""`) → **cắt cứng** theo `chunk_size`. Ở bước đệ quy, tôi tách theo separator ưu tiên cao nhất rồi **gộp các mảnh lại** cho sát `chunk_size` (giữ nguyên separator khi nối) để không tạo ra hàng loạt chunk vụn; mảnh nào tự nó vẫn quá dài thì gọi lại `_split` với danh sách separator còn lại. Nếu separator hiện tại không xuất hiện trong text (`len(pieces) == 1`) thì bỏ qua, thử separator kế tiếp.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Nguồn sự thật là list `self._store` in-memory; mỗi phần tử là record chuẩn hóa do `_make_record()` tạo: `{id, content, metadata, embedding}` với `embedding = self._embedding_fn(content)` (nhúng **một lần** lúc ghi, không nhúng lại lúc tìm). `search()` nhúng câu hỏi rồi gọi `_search_records()` — tính `compute_similarity(q_vec, r["embedding"])` cho từng record, sort giảm dần, cắt `top_k`, trả về dict có `content` + `score` + `metadata`.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> **Lọc TRƯỚC, tìm SAU** (pre-filtering): thu hẹp `self._store` bằng `all(record["metadata"].get(k) == v for k, v in metadata_filter.items())` rồi mới chấm điểm tương tự trên tập đã lọc — nhờ vậy `top_k` được "tiêu" hết cho các chunk hợp lệ thay vì bị chunk ngoài phạm vi chiếm chỗ. `delete_document` xóa theo `metadata["doc_id"]` (không phải `id` của chunk), trả `True` chỉ khi thực sự có record bị xóa.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Đúng 3 bước RAG: **retrieve → build prompt → generate**. Ngữ cảnh được ghép từ top-k chunk, mỗi chunk gắn nhãn `[Nguồn N] (doc_id=..., score=...)` để khi chấm **grounding quality** tôi chỉ ra được chính xác chunk nào tạo ra câu trả lời. Prompt ràng buộc rõ "chỉ dùng thông tin trong phần NGỮ CẢNH, nếu không đủ thì nói rõ là không biết" nhằm giảm bịa đặt (hallucination).

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```text
============================= test session starts =============================
platform win32 -- Python 3.14.6, pytest-9.1.1, pluggy-1.6.0
rootdir: .../K4-Day07-Data-Foundations_F5
collecting ... collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED   [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED    [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED   [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

============================= 42 passed in 0.06s ==============================
```

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|---|---|---|---|---|---|
| 1 | Tôi muốn trả lại đơn hàng vì sản phẩm bị lỗi. | Làm sao để hoàn trả hàng hóa không đúng mô tả? | CAO | -0.0399 | ❌ |
| 2 | Người bán phải cung cấp hóa đơn hợp lệ cho mọi đơn hàng. | Người bán có nghĩa vụ xuất chứng từ mua bán cho khách. | CAO | +0.0364 | ✅ |
| 3 | Phí vận chuyển được tính theo khối lượng và khoảng cách. | Chính sách bảo mật quy định cách sàn xử lý dữ liệu cá nhân. | THẤP | -0.0568 | ✅ |
| 4 | Đơn hàng sẽ được giao trong vòng 3 ngày làm việc. | Thời gian giao hàng dự kiến là 72 giờ kể từ khi xác nhận. | CAO | -0.0184 | ❌ |
| 5 | Hôm nay trời Hà Nội mưa rất to. | Điều kiện để sản phẩm được chấp nhận bảo hành là còn tem niêm phong. | THẤP | +0.0934 | ❌ |

**Kết quả nào bất ngờ nhất?**  
Cặp 1 và cặp 4 là bất ngờ vì về mặt ý nghĩa thì khá gần nhau nhưng mock embedding lại không phản ánh đúng. Điều này cho thấy embedding mock rất dễ bị sai khi không có ngữ nghĩa thật.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Tôi chạy 5 câu hỏi đánh giá với chiến lược `SentenceChunker` trên bộ tài liệu [data/k4_ecommerce](data/k4_ecommerce).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|---|---|---|---|---|
| 1 | Người mua có bao nhiêu ngày để gửi yêu cầu trả hàng/hoàn tiền sau khi đơn hàng giao thành công? | `shopee-privacy-policy` | 0.2404 | Không | Không trả lời đúng vì không tìm được chunk đổi trả đúng |
| 2 | Người bán bị áp dụng những chế tài nào nếu đăng bán sản phẩm thuộc danh mục cấm/hạn chế? | `shopee-prohibited-products` | 0.2838 | Có | Trả về nội dung phù hợp về chế tài |
| 3 | Ai chịu chi phí vận chuyển chiều hoàn trả sản phẩm? | `ghn-compensation-policy` | 0.2904 | Có | Trả về thông tin liên quan về bồi thường và vận chuyển |
| 4 | Thời gian Nhà Bán cam kết bảo hành tối đa là bao lâu? | `tiki-seller-warranty-faq` | 0.3254 | Có | Trả đúng về thời hạn bảo hành |
| 5 | Shopee thu thập dữ liệu cá nhân của người dùng từ những nguồn nào? | `shopee-privacy-policy` | 0.2691 | Có | Trả đúng về các nguồn dữ liệu |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** **4 / 5**

**Điều hay nhất tôi học được từ nhóm:**  
SentenceChunker rất tốt về tính mạch lạc, nhưng với văn bản chính sách thì nó dễ “vụn” về ngữ cảnh. Nếu muốn retrieval tốt hơn, cần kết hợp với cấu trúc heading hoặc metadata filter.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5/5 |
| Hướng tiếp cận của tôi (My Approach) | 10/10 |
| Hoàn thiện code (Core Implementation — tests) | 30/30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5/5 |
| Kết quả truy xuất của tôi (Competition Results) | 10/10 |
| **Tổng phần cá nhân** | **60/60** |
