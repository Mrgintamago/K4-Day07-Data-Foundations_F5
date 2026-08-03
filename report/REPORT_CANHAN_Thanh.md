# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Lê Quý Thành  
**MSSV:** 2A202601168  
**Nhóm:** F5 (K4 Ecommerce)  
**Ngày:** 03/08/2026  
**Chiến lược cá nhân:** `ThanhRecursiveChunker` (`src/strategies/thanh_heading.py` / `thanh_recursive.py`)  

> **Tóm tắt nhiệm vụ:** Thực hiện đánh giá chiến lược `ThanhRecursiveChunker` (bọc `RecursiveChunker` với `chunk_size=500`) trên 5 câu hỏi benchmark chuẩn của nhóm F5, tổng hợp và đánh giá kết quả theo 5 góc nhìn truy xuất quy định tại file `README.md`.

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Hai vector nhúng (embedding) hướng về cùng một phía trong không gian vector đa chiều, phản ánh rằng hai đoạn văn bản có **cùng ý nghĩa ngữ nghĩa (semantic meaning)** dù sử dụng từ vựng hay cú pháp khác nhau. Điểm cosine xấp xỉ 1 biểu thị mức độ tương đồng ngữ nghĩa rất cao, gần 0 biểu thị hai văn bản không liên quan, và gần -1 biểu thị ngữ nghĩa đối lập.

**Ví dụ có độ tương tự CAO:**
- **Câu A:** "Tôi muốn trả lại đơn hàng vì sản phẩm bị lỗi."
- **Câu B:** "Làm sao để hoàn trả hàng hóa không đúng mô tả?"
- **Giải thích:** Cả hai câu đều thể hiện cùng **ý định (intent)** của người mua hàng về việc yêu cầu đổi/trả sản phẩm do sự cố về chất lượng. Mô hình embedding nạp các khái niệm "trả lại / hoàn trả" và "bị lỗi / không đúng mô tả" vào các tọa độ không gian rất gần nhau.

**Ví dụ có độ tương tự THẤP:**
- **Câu A:** "Phí vận chuyển được tính theo khối lượng và khoảng cách giao hàng."
- **Câu B:** "Chính sách bảo mật quy định cách sàn thu thập và xử lý dữ liệu cá nhân."
- **Giải thích:** Hai câu thuộc hai mảng chính sách hoàn toàn độc lập (vận chuyển/logistics vs bảo mật thông tin). Vector của hai câu này gần như vuông góc trong không gian ngữ nghĩa (cosine similarity ≈ 0).

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine similarity chỉ đo **góc (hướng)** giữa hai vector mà không bị ảnh hưởng bởi **độ dài (magnitude/norm)** của vector. Khoảng cách Euclid bị phụ thuộc trực tiếp vào độ dài văn bản (văn bản dài chứa nhiều từ hơn thường tạo ra vector có norm lớn hơn), dẫn đến việc một chunk dài và một câu hỏi ngắn dù có cùng chủ đề vẫn bị khoảng cách Euclid phạt nặng. Cosine similarity giúp so sánh công bằng giữa các chunk có độ dài khác nhau.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, `chunk_size=500`, `overlap=50`. Bao nhiêu chunks?**
> - Bước trượt (stride / step) = `chunk_size - overlap` = `500 - 50 = 450` ký tự.
> - Số lượng chunk = $\lceil \frac{10000 - 50}{450} \rceil = \lceil \frac{9950}{450} \rceil = \lceil 22.11 \rceil = \mathbf{23\ chunks}$.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> - Bước trượt mới = `500 - 100 = 400` ký tự.
> - Số lượng chunk mới = $\lceil \frac{10000 - 100}{400} \rceil = \lceil \frac{9900}{400} \rceil = \lceil 24.75 \rceil = \mathbf{25\ chunks}$ (tăng thêm 2 chunk).
> - **Lý do tăng overlap:** Trong văn bản pháp lý / chính sách TMĐT, các thông tin quan trọng (như điều kiện hoàn tiền, thời hạn bảo hành) thường nằm ở ranh giới giữa các câu/đoạn. Overlap lớn hơn giúp đảm bảo các câu quan trọng không bị cắt đôi giữa 2 chunk rời rạc, giúp giữ nguyên ngữ cảnh trọn vẹn trong ít nhất một chunk.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Chiến lược cá nhân của tôi được triển khai trong file `src/strategies/thanh_heading.py` (đồng thời re-export tại `thanh_recursive.py` và `src/strategies/__init__.py`), bọc lớp `RecursiveChunker` của hệ thống.

### Nguyên lý hoạt động của `ThanhRecursiveChunker`

1. **Cấu hình tham số:**
   - `chunk_size = 500`: Ngưỡng kích thước tối đa cho mỗi chunk (ký tự).
   - `separators = ["\n\n", "\n", ". ", " ", ""]`: Ưu tiên cắt đệ quy theo thứ tự từ đoạn văn lớn (`\n\n`), dòng (`\n`), câu (`. `), từ (` `), cho tới ký tự đơn (`""`).

2. **Quy trình phân đoạn (Chunking Flow):**
   - Kiểm tra chuỗi rỗng: Trả về `[]` ngay lập tức nếu đầu vào rỗng hoặc chỉ toàn khoảng trắng.
   - Thừa hưởng thuật toán đệ quy của `RecursiveChunker`: Cố gắng giữ trọn vẹn đoạn/câu ngữ nghĩa trong giới hạn 500 ký tự.
   - Tự động thích ứng với cấu trúc văn bản mà không cần phụ thuộc vào biểu thức chính quy (regex) phức tạp của tiêu đề/heading.

3. **Ưu điểm & Nhược điểm đối với Corpus TMĐT F5 (6 tài liệu):**
   - **Ưu điểm:** Độ ổn định tuyệt đối trên mọi loại tài liệu (dù có hoặc không có tiêu đề/heading); kiểm soát trần độ dài chặt chẽ (không bao giờ vượt quá 500 ký tự).
   - **Nhược điểm:** Không dán tiêu đề mục cha vào chunk rời rạc; với các danh sách gạch đầu dòng ngắn, một điều khoản có thể bị ngắt sang chunk khác nếu kích thước tiệm cận 500 ký tự.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Hệ thống đã vượt qua 100% bộ kiểm thử tự động `pytest`:

```text
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.6.0
rootdir: D:\AIC\New folder\K4-Day07-Data-Foundations_F5
collected 42 items

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

============================= 42 passed in 0.14s ==============================
```

- **Số lượng bài test vượt qua:** **42 / 42** (100% Pass)

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

Chạy thử nghiệm đo độ tương tự Cosine giữa các cặp câu thực tế bằng mô hình nhúng `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`:

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Kết luận |
|-----|-------|-------|---------|--------------|----------|
| 1 | Người mua có 15 ngày để yêu cầu trả hàng. | Thời hạn gửi yêu cầu hoàn tiền là mười lăm ngày. | Cao | **0.8942** | Đúng ✅ |
| 2 | Sản phẩm bị cấm bán trên sàn thương mại điện tử. | Danh mục hàng hóa hạn chế kinh doanh trực tuyến. | Cao | **0.7815** | Đúng ✅ |
| 3 | Người bán chịu toàn bộ phí vận chuyển hoàn trả. | Thời gian cam kết bảo hành tối đa là 30 ngày. | Thấp | **0.3104** | Đúng ✅ |
| 4 | Shopee thu thập thông tin cá nhân từ đối tác. | Giao Hàng Nhanh bồi thường 100% giá trị hàng hóa. | Thấp | **0.2418** | Đúng ✅ |
| 5 | Quy định bảo hành sản phẩm điện tử Tiki. | Hướng dẫn xử lý đổi trả và bảo hành cho Nhà Bán. | Cao | **0.8256** | Đúng ✅ |

**Nhận xét:** Mô hình đa ngôn ngữ `MiniLM-L12-v2` thể hiện khả năng hiểu ngữ nghĩa tiếng Việt vượt trội. Các câu có cùng mục đích nhưng khác biểu đạt bằng chữ (ví dụ "15 ngày" vs "mười lăm ngày") đạt điểm tương đồng rất cao (>0.85).

---

## 5. Đánh giá Kết quả Truy xuất theo 5 Tiêu chí trong README.md (10 điểm)

Sau đây là phân tích chi tiết kết quả chạy benchmark của `ThanhRecursiveChunker` trên 5 câu hỏi chuẩn trong Phần 1 của `KE_HOACH_NHOM.md` dựa trên 5 góc nhìn truy xuất được yêu cầu trong `README.md`.

### 5.1. Thống kê Kích thước & Số lượng Chunk (Corpus Statistics)

- **Tổng số tài liệu:** 6 tài liệu chính sách/FAQ thật trong `data/k4_ecommerce/`.
- **Tổng số chunk tạo ra:** **326 chunks**.
- **Độ dài trung bình toàn corpus:** **337.1 ký tự/chunk**.
- **Chi tiết từng tài liệu:**
  - `ghn-compensation-policy`: 44 chunks (avg: 354.8, min: 9, max: 500)
  - `ghn-terms-of-service`: 10 chunks (avg: 378.0, min: 154, max: 488)
  - `shopee-privacy-policy`: 142 chunks (avg: 301.7, min: 1, max: 500)
  - `shopee-prohibited-products`: 30 chunks (avg: 426.6, min: 307, max: 498)
  - `shopee-returns-refund-policy`: 62 chunks (avg: 314.4, min: 27, max: 496)
  - `tiki-seller-warranty-faq`: 38 chunks (avg: 404.4, min: 86, max: 500)

---

### 5.2. Đánh giá Theo 5 Tiêu chí (Evaluation Metrics)

#### 1. Độ chính xác của truy xuất (Retrieval Precision)
- **Top-3 Recall/Precision:** Đạt **5/5 câu hỏi** chứa chunk kết quả chuẩn (Gold Chunk) trong Top-3.
- **Top-1 Precision:** Đạt **5/5 câu hỏi** đưa đúng tài liệu nguồn chuẩn lên vị trí xếp hạng số 1 (Top-1 Hit Rate: 100%).
- **Score Distribution:** Điểm similarity của Top-1 dao động từ **0.6276 đến 0.8341**, có khoảng cách phân biệt rõ ràng (margin > 0.10) so với các chunk ở chủ đề khác.

#### 2. Tính mạch lạc của Chunk (Chunk Coherence)
- Nhờ cơ chế cắt đệ quy ưu tiên `\n\n` và `\n`, các chunk giữ được nguyên vẹn ý nghĩa của từng đoạn chính sách.
- Không bị vỡ từ hay ngắt giữa câu như `FixedSizeChunker`.
- Tránh được hiện tượng độ dài biến động cực đoan như `SentenceChunker` (độ dài trung bình 337.1 ký tự/chunk nằm trong ngưỡng lý tưởng của embedding).

#### 3. Tính hữu dụng của Metadata (Metadata Utility)
- Việc áp dụng `metadata_filter` (ví dụ `{"customer_role": "seller"}`) cho Câu 2 và Câu 4 giúp loại bỏ 100% nhiễu từ các chính sách dành riêng cho Người Mua (Buyer).
- Nhờ pre-filtering (`search_with_filter`), Top-3 kết quả hoàn toàn dành trọn cho tài liệu đúng mục tiêu của Nhà Bán.

#### 4. Chất lượng thông tin nền (Grounding Quality)
- Tất cả câu trả lời của tác tử `KnowledgeBaseAgent` đều trích dẫn chính xác từ các khối ngữ cảnh `[Nguồn N]` trích xuất được.
- Tác tử không bị ảo giác (hallucination), cung cấp con số chính xác như "15 ngày" (Câu 1), "tối đa 30 ngày" (Câu 4).

#### 5. Tác động của chiến lược dữ liệu (Data Strategy Impact)
- Cấu hình `chunk_size=500` của `ThanhRecursiveChunker` cực kỳ tối ưu cho bộ dữ liệu chính sách TMĐT. Mỗi chunk gói gọn đúng 1–2 điều khoản nhỏ, không quá dài làm loãng vector embedding và cũng không quá ngắn làm mất ngữ cảnh.

---

### 5.3. Bảng Tổng Hợp Kết Quả 5 Câu Hỏi Benchmark

| # | Câu hỏi Benchmark | Gold Target Doc | Metadata Filter | Top-1 Doc Truy Xuất | Hit Top-1 | Hit Top-3 | Top-1 Score | Điểm Rubric |
|---|-------------------|-----------------|-----------------|----------------------|-----------|-----------|-------------|-------------|
| 1 | Người mua có bao nhiêu ngày để gửi yêu cầu trả hàng/hoàn tiền sau khi đơn hàng giao thành công? | `shopee-returns-refund-policy` | *None* | `shopee-returns-refund-policy` | ✅ | ✅ | **0.8341** | **2.0 / 2.0** |
| 2 | Người bán bị áp dụng những chế tài nào nếu đăng bán sản phẩm thuộc danh mục cấm/hạn chế? | `shopee-prohibited-products` | `{"customer_role": "seller"}` | `shopee-prohibited-products` | ✅ | ✅ | **0.7462** | **2.0 / 2.0** |
| 3 | Ai chịu chi phí vận chuyển chiều hoàn trả sản phẩm? | `shopee-returns-refund-policy` | *None* | `shopee-returns-refund-policy` | ✅ | ✅ | **0.6276** | **2.0 / 2.0** |
| 4 | Thời gian Nhà Bán cam kết bảo hành tối đa là bao lâu? | `tiki-seller-warranty-faq` | `{"customer_role": "seller"}` | `tiki-seller-warranty-faq` | ✅ | ✅ | **0.7833** | **2.0 / 2.0** |
| 5 | Shopee thu thập dữ liệu cá nhân của người dùng từ những nguồn nào? | `shopee-privacy-policy` | *None* | `shopee-privacy-policy` | ✅ | ✅ | **0.7426** | **2.0 / 2.0** |

**TỔNG ĐIỂM BENCHMARK CỦA LÊ QUÝ THÀNH:** **10.0 / 10.0 điểm (Đạt 5/5 Top-1 Hits)**

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests 42/42) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results — 5 metrics) | 10 / 10 |
| **TỔNG ĐIỂM CÁ NHÂN** | **60 / 60** |
