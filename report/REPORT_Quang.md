# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Quang
**Nhóm:** F5
**Ngày:** 2026-08-03
**Chiến lược cá nhân:** `SemanticParentChunker` — `src/strategies/quang_semantic.py`

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

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

### Bài toán tính toán Chunking (Bài tập 1.2)

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
> Dùng regex **lookbehind** `re.split(r"(?<=[.!?])\s+", text)`: cắt tại khoảng trắng *đứng sau* dấu `.`, `!`, `?` nên dấu câu được **giữ lại ở cuối câu** thay vì bị nuốt mất. Cách này phủ luôn cả `". "` lẫn `".\n"` vì `\s+` khớp mọi loại khoảng trắng. Edge case đã xử lý: text rỗng hoặc chỉ có khoảng trắng → trả `[]`; mỗi câu được `.strip()` và các câu rỗng bị loại trước khi gom nhóm theo `max_sentences_per_chunk`.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> `_split` là hàm đệ quy với **2 base case**: (1) `len(text) <= chunk_size` → trả `[text]`; (2) hết separator (hoặc gặp separator `""`) → **cắt cứng** theo `chunk_size`. Ở bước đệ quy, tôi tách theo separator ưu tiên cao nhất rồi **gộp các mảnh lại** cho sát `chunk_size` (giữ nguyên separator khi nối) để không tạo ra hàng loạt chunk vụn; mảnh nào tự nó vẫn quá dài thì gọi lại `_split` với danh sách separator còn lại. Nếu separator hiện tại không xuất hiện trong text (`len(pieces) == 1`) thì bỏ qua, thử separator kế tiếp. Base case (2) chính là thứ giúp `RecursiveChunker(separators=[])` vẫn trả list không rỗng thay vì rơi vào đệ quy vô hạn.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Nguồn sự thật là list `self._store` in-memory; mỗi phần tử là record chuẩn hóa do `_make_record()` tạo: `{id, content, metadata, embedding}` với `embedding = self._embedding_fn(content)` (nhúng **một lần** lúc ghi, không nhúng lại lúc tìm). ChromaDB chỉ là lớp phụ: `__init__` chỉ bật cờ `_use_chroma` **sau khi** `get_or_create_collection()` thành công, và mọi lỗi Chroma đều rơi về in-memory nên store không bao giờ ở trạng thái nửa vời. `search()` nhúng câu hỏi rồi gọi `_search_records()` — tính `compute_similarity(q_vec, r["embedding"])` cho từng record, sort giảm dần, cắt `top_k`, trả về dict có `content` + `score` + `metadata`.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> **Lọc TRƯỚC, tìm SAU** (pre-filtering): thu hẹp `self._store` bằng `all(record["metadata"].get(k) == v for k, v in metadata_filter.items())` rồi mới chấm điểm tương tự trên tập đã lọc — nhờ vậy `top_k` được "tiêu" hết cho các chunk hợp lệ thay vì bị chunk ngoài phạm vi chiếm chỗ. `metadata_filter=None` được coi là không lọc, trả đúng bằng `search()`. `delete_document` xóa theo `metadata["doc_id"]` (không phải `id` của chunk), trả `True` chỉ khi thực sự có record bị xóa.
>
> **Điểm mấu chốt tôi phải xử lý:** `Document` có thể được tạo với `metadata={}` rỗng. Vì vậy `_make_record` luôn `metadata.setdefault("doc_id", doc.id)` — nếu không, mọi chunk sẽ không có `doc_id` và `delete_document()` sẽ luôn trả `False`.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Đúng 3 bước RAG: **retrieve → build prompt → generate**. Ngữ cảnh được ghép từ top-k chunk, mỗi chunk gắn nhãn `[Nguồn N] (doc_id=..., score=...)` để khi chấm **grounding quality** tôi chỉ ra được chính xác chunk nào tạo ra câu trả lời. Prompt ràng buộc rõ "chỉ dùng thông tin trong phần NGỮ CẢNH, nếu không đủ thì nói không biết" nhằm giảm bịa đặt (hallucination). Trường hợp store rỗng → trả thẳng một câu thông báo thay vì gọi LLM với ngữ cảnh trống.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
$ pytest tests/ -v
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

**Số lượng bài test vượt qua (pass):** **42** / 42

Kiểm chứng bổ sung ngoài bộ test:
- `python ingest.py` → `ingest self-check OK: parse được 4 khóa metadata, tạo 18 chunk (mỗi chunk giữ doc_id + metadata).`
- `python main.py "Thời hạn đổi trả là bao lâu?"` → chạy hết pipeline: nạp store → `search()` top-3 → `KnowledgeBaseAgent.answer()`.

> Ghi chú môi trường: console Windows mặc định dùng cp1252 nên phải đặt `PYTHONIOENCODING=utf-8` trước khi chạy `main.py` / `ingest.py`, nếu không sẽ gặp `UnicodeEncodeError` khi in tiếng Việt (không phải lỗi logic).

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

Backend nhúng: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (384 chiều).
Dự đoán được viết cứng trong `scripts/similarity_demo.py` **trước khi chạy lần đầu**, nên
không thể sửa hồi tố. Ngưỡng phân loại CAO/THẤP lấy bằng trung bình 5 cặp = **+0.3482**.

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Tôi muốn trả lại đơn hàng vì sản phẩm bị lỗi. | Làm sao để hoàn trả hàng hóa không đúng mô tả? | CAO | **+0.4972** | ✅ |
| 2 | Người bán phải cung cấp hóa đơn hợp lệ cho mọi đơn hàng. | Người bán có nghĩa vụ xuất chứng từ mua bán cho khách. | CAO | **+0.7164** | ✅ |
| 3 | Phí vận chuyển được tính theo khối lượng và khoảng cách. | Chính sách bảo mật quy định cách sàn xử lý dữ liệu cá nhân. | THẤP | **+0.1183** | ✅ |
| 4 | Đơn hàng sẽ được giao trong vòng 3 ngày làm việc. | Thời gian giao hàng dự kiến là 72 giờ kể từ khi xác nhận. | CAO | **+0.5159** | ✅ |
| 5 | Hôm nay trời Hà Nội mưa rất to. | Điều kiện để sản phẩm được chấp nhận bảo hành là còn tem niêm phong. | THẤP | **-0.1069** | ✅ |

**Dự đoán đúng: 5/5** (đúng về thứ hạng CAO/THẤP)

Lệnh tái lập:
```bash
export PYTHONIOENCODING=utf-8
EMBEDDING_PROVIDER=local python scripts/similarity_demo.py
```

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Bất ngờ nhất là **cặp 1 chỉ đạt 0.4972 trong khi cặp 2 đạt 0.7164**, dù trước khi chạy tôi nghĩ cặp 1 mới là cặp giống nhau nhất. Lý do: cặp 2 **trùng chủ ngữ và cấu trúc câu** ("Người bán phải/có nghĩa vụ..."), chỉ khác cặp từ đồng nghĩa "hóa đơn hợp lệ" ↔ "chứng từ mua bán". Cặp 1 tuy cùng **ý định** nhưng một câu là trần thuật ngôi thứ nhất ("Tôi muốn...") còn câu kia là câu hỏi ("Làm sao để...?") — embedding vẫn mã hóa cả **dạng câu**, không chỉ nội dung ngữ nghĩa thuần.
>
> Điều bất ngờ thứ hai: cặp 5 ra **âm** (-0.1069) chứ không phải ~0. Hai câu hoàn toàn không liên quan mà vẫn có hướng đối nghịch nhẹ, cho thấy không gian embedding **không trực giao hoàn hảo** — điểm 0 không phải mốc "không liên quan", nên khi chấm retrieval phải so sánh **thứ hạng tương đối** giữa các chunk chứ đừng đặt một ngưỡng tuyệt đối cứng.
>
> Ý nghĩa cho phần retrieval: khoảng cách giữa "liên quan" (0.50–0.72) và "không liên quan" (-0.11–0.12) rất rộng và tách bạch rõ, nên top-3 hoàn toàn đủ để phân biệt tín hiệu thật với nhiễu — miễn là chunk được cắt sao cho giữ trọn ý.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

**Chiến lược của tôi:** `SemanticParentChunker` (`src/strategies/quang_semantic.py`)
**Backend nhúng:** `paraphrase-multilingual-MiniLM-L12-v2` (384 chiều) — không dùng mock.
**Kích thước store:** 170 chunk từ 6 tài liệu.
**Tham số cuối:** `breakpoint_percentile=90`, `heading_weight=2`, `max_chunk_size=900`, `min_sentences=2`.

Chiến lược này khác hẳn 3 chiến lược dựng sẵn ở chỗ nó **không dùng luật chuỗi ký tự nào để
quyết định chỗ cắt**. Nó nhúng từng câu, đo cosine giữa các câu liền kề, rồi cắt tại 10% vị trí
có khoảng cách ngữ nghĩa lớn nhất — ranh giới chunk là ranh giới **Ý**, không phải ranh giới dấu
chấm (`SentenceChunker`), dấu phân cách (`RecursiveChunker`) hay số ký tự (`FixedSizeChunker`).

Cơ chế thứ hai: tiêu đề mục cha được lưu riêng trong `metadata["parent_heading"]`, và tham số
`heading_weight` điều khiển **mức độ tiêu đề tham gia vào vector** (0 = không, 1 = ghép một lần,
2 = lặp hai lần).

```bash
python scripts/run_benchmark.py --member quang --markdown
python scripts/sweep_heading_weight.py
```

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Người mua có bao nhiêu ngày để gửi yêu cầu trả hàng hoàn tiền? | `tiki-seller-warranty-faq` — FAQ 8 "Nhà Bán có thời gian bao lâu để xác nhận yêu cầu đổi, trả, bảo hành?" | +0.6519 | ⚠️ Đúng chủ đề "thời hạn" nhưng **sai tài liệu** — gold ở `shopee-returns` mục 3.2 | Trả lời về thời hạn xác nhận của Nhà Bán, **không phải** 15 ngày của Người Mua |
| 2 | Người bán bị chế tài nào nếu đăng bán hàng cấm? | `shopee-prohibited-products` — **mục 3 "HÀNH VI VI PHẠM VÀ BIỆN PHÁP XỬ LÝ"** | **+0.7350** | ✅ Đúng chunk gold ở top-1 | Liệt kê đủ 5 chế tài (i)→(v) |
| 3 | Ai chịu chi phí vận chuyển chiều hoàn trả? | `shopee-returns-refund-policy` — **mục 7.1 "Người Bán sẽ chịu chi phí vận chuyển…"** | +0.5884 | ✅ Đúng chunk gold ở top-1 | Trích đúng 7.1, nêu được Người Bán chịu và các trường hợp |
| 4 | Nhà Bán cam kết bảo hành tối đa bao lâu? | `tiki-seller-warranty-faq` — **FAQ 5 "Thời gian Nhà Bán cam kết bảo hành là bao lâu?"** | **+0.7775** | ✅ Đúng chunk gold ở top-1 | Trích đúng "tối đa không quá 30 ngày" |
| 5 | Shopee thu thập dữ liệu cá nhân từ nguồn nào? | `shopee-privacy-policy` — mục 3.1 "dữ liệu cá nhân mà Shopee có thể thu thập bao gồm…" | +0.7277 | ⚠️ Đúng tài liệu, **sai mục** — gold là mục 2.2 | Liệt kê *loại* dữ liệu thu thập, không trả lời *nguồn* thu thập |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** **5** / 5 (tính theo `doc_id`)

**Tự chấm theo `docs/SCORING.md` (2 điểm/câu):**

| Câu | Điểm | Lý do |
|---|---|---|
| 1 | **1/2** | Sai tài liệu ở top-1; chunk gold không có trong top-3 |
| 2 | **2/2** | Top-1 là chunk gold, agent liệt kê đủ 5 chế tài |
| 3 | **2/2** | Top-1 là chunk gold, agent trả lời chính xác |
| 4 | **2/2** | Top-1 là chunk gold, agent trả lời chính xác |
| 5 | **1/2** | Đúng tài liệu nhưng sai mục; agent trả nhầm "loại dữ liệu" thay vì "nguồn dữ liệu" |
| **Tổng** | **8/10** | |

---

### Thí nghiệm chính: tiêu đề mục cha là nhiễu hay là tín hiệu?

Đây là phát hiện quan trọng nhất trong bài của tôi. Ban đầu tôi làm `HeadingChunker` — dán tiêu đề
mục vào đầu mỗi chunk — và được **8/10**, nhưng câu 5 hỏng vì các mục cùng chứa chữ "THU THẬP"
cạnh tranh nhau: tiêu đề chiếm tỷ trọng lớn trong vector và kéo điểm theo tiêu đề thay vì nội dung.

Giả thuyết: **bỏ tiêu đề ra khỏi vector sẽ tốt hơn**. Tôi hiện thực `heading_weight=0`, nhúng phần
thân thuần, tiêu đề chỉ lưu trong metadata. Kết quả **7/10** — câu 2 tốt lên nhưng câu 1 và 3 hỏng.

Tôi quét cả 3 giá trị bằng `scripts/sweep_heading_weight.py` (cùng 170 chunk, cùng 5 câu):

| Câu | `heading_weight=0` | `heading_weight=1` | `heading_weight=2` |
|-----|------------------|------------------|------------------|
| 1 | 1/2 (gold không có trong top-3) | 0/2 (sai cả tài liệu) | 1/2 (gold không có trong top-3) |
| 2 | 2/2 (hạng 1) | 2/2 (hạng 1) | 2/2 (hạng 1) |
| 3 | 1/2 (gold không có trong top-3) | 1/2 (gold không có trong top-3) | **2/2 (hạng 1)** |
| 4 | 2/2 (hạng 1) | 2/2 (hạng 1) | 2/2 (hạng 1) |
| 5 | 1/2 (sai mục) | 1/2 (sai mục) | 1/2 (sai mục) |
| **Tổng** | **7/10** | **6/10** | **8/10** |

**Kết quả KHÔNG đơn điệu: 7 → 6 → 8.** Đây là điều tôi không dự đoán được.

**Giải thích:**
- **Tiêu đề vừa là nhiễu vừa là tín hiệu**, tùy câu hỏi. Câu 3 hỏi "ai chịu chi phí vận chuyển" —
  chính tiêu đề "7. TRÁCH NHIỆM VỀ CHI PHÍ VẬN CHUYỂN HOÀN TRẢ SẢN PHẨM CỦA NGƯỜI BÁN" mới là thứ
  trả lời câu hỏi; phần thân "7.1. Người Bán sẽ chịu chi phí…" thiếu ngữ cảnh. Bỏ tiêu đề (`w=0`)
  → mất tín hiệu, câu 3 hỏng.
- **`heading_weight=1` là vùng tệ nhất**: tiêu đề có mặt nhưng bị phần thân dài áp đảo, nên nó
  không đủ mạnh để dẫn hướng mà vẫn đủ để làm loãng vector nội dung — tệ hơn cả hai cực. Đây là
  bài học đáng giá: một tham số tưởng "trung dung" lại có thể xấu hơn cả hai đầu.
- **`heading_weight=2`** làm tiêu đề đủ mạnh để dẫn hướng ở câu 3 mà chưa nuốt hết nội dung.

**Kết luận cho phần demo:** với văn bản chính sách có đánh số, tiêu đề mục KHÔNG nên bị bỏ đi cũng
không nên chỉ ghép qua loa — nó cần được **cân trọng số như một tham số riêng**. Không có chiến lược
nào trong 3 chiến lược dựng sẵn cho phép làm điều này, vì chúng đều coi văn bản là chuỗi phẳng.

---

### Hai câu vẫn thất bại (failure analysis)

**Câu 1 — sai tài liệu, hỏng ở mọi cấu hình.** Câu hỏi "bao nhiêu ngày để gửi yêu cầu trả hàng
hoàn tiền" bị `tiki-seller-warranty-faq` FAQ 8 ("Nhà Bán có thời gian bao lâu để xác nhận yêu cầu
đổi, trả, bảo hành?") đánh bại. Nguyên nhân **không phải chunking** mà là **corpus**: hai tài liệu
khác nhau cùng nói về "thời hạn xử lý yêu cầu đổi trả", một cho Người Mua một cho Nhà Bán. Câu hỏi
không nêu rõ chủ thể nên embedding không phân biệt được.
→ *Cách sửa:* thêm `metadata_filter={"customer_role": "buyer"}` cho câu 1. Đây chính là bằng chứng
cho thấy **metadata filter không phải tính năng phụ mà là điều kiện cần** khi corpus có nhiều tài
liệu cùng chủ đề nhưng khác đối tượng.

**Câu 5 — sai mục, hỏng ở mọi cấu hình.** Gold nằm ở mục 2.2 ("thu thập thông tin từ bạn, các công
ty liên kết, các bên thứ ba…") nhưng top-1 luôn là mục 3.1 hoặc 6.1. File `shopee-privacy-policy.md`
dài 58 KB với hàng chục mục đều xoay quanh động từ "thu thập"; câu hỏi "từ những **nguồn** nào" khác
với "**những dữ liệu gì**" chỉ ở một danh từ, mà mô hình 384 chiều không tách bạch được sắc thái đó.
→ *Cách sửa:* tăng `top_k` lên 5 và thêm bước rerank, hoặc chia tài liệu privacy thành nhiều file
nhỏ theo mục lớn để mỗi file có phạm vi hẹp hơn.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 9 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 (42/42 test pass) |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 (đúng 5/5, có phản ngẫm) |
| Kết quả truy xuất của tôi (Competition Results) | 8 / 10 (câu 2 và 5 chỉ đạt 1 điểm) |
| **Tổng phần cá nhân** | **57 / 60** |
