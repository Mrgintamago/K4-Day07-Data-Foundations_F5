# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Trần Quang Sáng  
**MSSV:** 2A202601446  
**Nhóm:** F5  
**Ngày:** 2026-08-03  
**Chiến lược cá nhân:** `SangFixedChunker` — `src/strategies/sang_fixed.py`

> **Nộp 1 bản / sinh viên.** Phần nhóm nộp chung trong `REPORT_NHOM.md`. Báo cáo này tập trung vào cách tôi triển khai, chạy thử và đánh giá chiến lược chunking cá nhân.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity)

**Độ tương tự cosine cao nghĩa là gì?**
> Hai vector embedding có cosine similarity cao khi chúng gần cùng hướng trong không gian vector. Với văn bản, điều này thường nghĩa là hai câu hoặc hai đoạn đang nói về cùng một ý, dù có thể dùng từ khác nhau. Điểm càng gần 1 thì càng gần nghĩa; gần 0 là ít liên quan; âm là có xu hướng khác hướng.

**Ví dụ có độ tương tự cao:**
- Câu A: "Tôi muốn trả lại đơn hàng vì sản phẩm bị lỗi."
- Câu B: "Làm sao để hoàn trả hàng hóa không đúng mô tả?"
- Lý do: hai câu đều nói về nhu cầu trả hàng/hoàn tiền vì sản phẩm có vấn đề.

**Ví dụ có độ tương tự thấp:**
- Câu A: "Phí vận chuyển được tính theo khối lượng và khoảng cách."
- Câu B: "Chính sách bảo mật quy định cách sàn xử lý dữ liệu cá nhân."
- Lý do: một câu nói về vận chuyển, câu còn lại nói về dữ liệu cá nhân; hai chủ đề không liên quan trực tiếp.

**Tại sao cosine similarity thường được ưu tiên hơn Euclidean distance cho text embeddings?**
> Cosine similarity tập trung vào hướng của vector, nên phù hợp hơn với ý nghĩa ngữ nghĩa. Với văn bản, một đoạn dài và một câu ngắn vẫn có thể cùng ý; nếu dùng Euclidean distance, độ dài/norm của vector có thể làm nhiễu kết quả. Cosine giúp so sánh "đang nói về điều gì" tốt hơn là so sánh độ lớn tuyệt đối.

### Bài toán tính toán Chunking

**Tài liệu 10,000 ký tự, `chunk_size=500`, `overlap=50`. Bao nhiêu chunks?**
> Bước trượt `step = chunk_size - overlap = 500 - 50 = 450`.  
> Số chunk xấp xỉ `ceil((10000 - 50) / 450) = ceil(9950 / 450) = 23`.  
> **Đáp án:** 23 chunks.

**Nếu overlap tăng lên 100, số lượng chunk thay đổi thế nào?**
> Khi `overlap=100`, bước trượt còn `500 - 100 = 400`.  
> Số chunk xấp xỉ `ceil((10000 - 100) / 400) = ceil(9900 / 400) = 25`.  
> Số chunk tăng vì mỗi chunk mới tiến ít hơn so với chunk trước. Đổi lại, overlap cao giúp giữ lại ngữ cảnh ở ranh giới chunk, đặc biệt khi một điều khoản quan trọng bị cắt giữa câu.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

### Các hàm chia nhỏ (Chunking Functions)

**`FixedSizeChunker.chunk` — hướng tiếp cận:**
> Tôi chọn `FixedSizeChunker` vì đây là chiến lược ổn định, dễ kiểm soát và tạo các chunk có độ dài gần đều nhau. Điều này giúp điểm similarity giữa các chunk công bằng hơn, vì không có chunk quá dài hoặc quá ngắn chiếm ưu thế bất thường. Điểm yếu của cách này là nó cắt theo số ký tự, không hiểu ranh giới câu hay điều khoản, nên có thể cắt ngang một ý quan trọng.

**Chiến lược riêng của tôi — `SangFixedChunker`:**
> Tôi giữ cố định `chunk_size=500` và chỉ quét tham số `overlap` ở ba mức `0 / 50 / 150`. Ý tưởng là kiểm tra overlap có thật sự cứu được các trường hợp bị cắt giữa câu hay không. `overlap=0` là baseline rẻ nhất; `overlap=50` là mức vừa phải; `overlap=150` giữ nhiều ngữ cảnh nhất nhưng tạo thêm nhiều chunk và tốn chi phí embedding hơn.

### Lớp EmbeddingStore

**`add_documents` + `search` — hướng tiếp cận:**
> Store lưu mỗi chunk dưới dạng record gồm `id`, `content`, `metadata` và `embedding`. Embedding được tính một lần khi nạp tài liệu, sau đó khi tìm kiếm thì chỉ embedding câu hỏi và so cosine với các vector đã lưu. Cách này đơn giản, dễ kiểm thử và phù hợp với quy mô lab.

**`search_with_filter` — hướng tiếp cận:**
> Với các câu cần lọc metadata như câu 2 và câu 4, store lọc trước theo metadata rồi mới tính similarity. Đây là điểm quan trọng vì corpus có nhiều tài liệu cùng nói về trả hàng/bảo hành nhưng khác vai trò người mua/người bán. Nếu không lọc, top-k có thể bị chiếm bởi tài liệu đúng chủ đề nhưng sai đối tượng.

### Tác tử KnowledgeBaseAgent

**`answer` — hướng tiếp cận:**
> Agent làm theo pipeline RAG cơ bản: retrieve top-k chunk, ghép thành ngữ cảnh, rồi gọi LLM để trả lời. Trong benchmark, tôi dùng OpenAI chat model để đánh giá câu trả lời thay vì stub, vì rubric yêu cầu không chỉ lấy được chunk liên quan mà câu trả lời của agent cũng phải chính xác.

### Chiến lược riêng cho Giai đoạn 2

**`SangFixedChunker` (`src/strategies/sang_fixed.py`) — lý do thiết kế:**
> Tôi chọn chiến lược fixed-size vì muốn có một baseline "cơ học nhưng sạch": cùng `chunk_size=500`, chỉ thay đổi overlap để quan sát tác động. Đây là cách tốt để trả lời câu hỏi: overlap cao hơn có luôn tốt hơn không? Kết quả cho thấy không hẳn. `overlap=150` giúp câu 3 lấy đúng đoạn về trách nhiệm chi phí vận chuyển của Người Bán, nhưng lại làm câu 2 bị kéo về phần danh sách hàng cấm thay vì phần chế tài. Mức `overlap=50` cân bằng nhất trong thí nghiệm này.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử

```bash
$ .venv/Scripts/python.exe -m pytest tests -q
..........................................                               [100%]
42 passed in 0.07s
```

**Số lượng bài test vượt qua:** **42 / 42**

Kiểm chứng bổ sung:
- `scripts/run_benchmark.py` đã hỗ trợ `--member sang --overlap N`.
- `scripts/run_benchmark.py` đã hỗ trợ `--member sang --sweep-overlap` để chạy đủ `overlap=0/50/150`.
- Benchmark dùng backend nhúng thật: `text-embedding-3-small`, không dùng mock.

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

Backend nhúng: `text-embedding-3-small` (1536 chiều).  
Ngưỡng phân loại CAO/THẤP lấy bằng trung bình 5 cặp = **+0.4514**.

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|---|---|---|---|---|---|
| 1 | Tôi muốn trả lại đơn hàng vì sản phẩm bị lỗi. | Làm sao để hoàn trả hàng hóa không đúng mô tả? | CAO | **+0.4914** | Có |
| 2 | Người bán phải cung cấp hóa đơn hợp lệ cho mọi đơn hàng. | Người bán có nghĩa vụ xuất chứng từ mua bán cho khách. | CAO | **+0.5683** | Có |
| 3 | Phí vận chuyển được tính theo khối lượng và khoảng cách. | Chính sách bảo mật quy định cách sàn xử lý dữ liệu cá nhân. | THẤP | **+0.3117** | Có |
| 4 | Đơn hàng sẽ được giao trong vòng 3 ngày làm việc. | Thời gian giao hàng dự kiến là 72 giờ kể từ khi xác nhận. | CAO | **+0.6360** | Có |
| 5 | Hôm nay trời Hà Nội mưa rất to. | Điều kiện để sản phẩm được chấp nhận bảo hành là còn tem niêm phong. | THẤP | **+0.2496** | Có |

**Dự đoán đúng:** **5 / 5**

Lệnh tái lập:

```powershell
$env:PYTHONIOENCODING="utf-8"
$env:EMBEDDING_PROVIDER="openai"
.\.venv\Scripts\python.exe scripts\similarity_demo.py
```

**Kết quả bất ngờ nhất:**
> Cặp 3 và cặp 5 đều không liên quan rõ ràng nhưng điểm vẫn dương, lần lượt là +0.3117 và +0.2496. Điều này nhắc tôi rằng cosine score tuyệt đối không nên được hiểu cứng là "liên quan" hay "không liên quan". Trong retrieval, thứ hạng top-k quan trọng hơn một ngưỡng cố định, vì mọi chunk trong cùng corpus đều có thể chia sẻ một số từ hoặc ngữ cảnh chung về thương mại điện tử.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi benchmark chung của nhóm** trên chiến lược cá nhân `SangFixedChunker`.

**Chiến lược của tôi:** `FixedSizeChunker` bọc bởi `SangFixedChunker` (`src/strategies/sang_fixed.py`)  
**Backend nhúng:** `text-embedding-3-small` — không dùng mock  
**Backend LLM:** `openai/gpt-4o-mini`  
**Tham số quét:** `chunk_size=500`, `overlap=0/50/150`  
**Cấu hình chọn để báo cáo:** `chunk_size=500`, `overlap=50`

Lệnh chạy:

```powershell
$env:PYTHONIOENCODING="utf-8"
$env:LLM_PROVIDER="openai"
.\.venv\Scripts\python.exe scripts\run_benchmark.py --member sang --sweep-overlap --top-k 3 --markdown
```

### Kết quả sweep overlap

| Cấu hình | Số chunk | Top-3 có đúng `doc_id` | Tự chấm | Nhận xét |
|---|---:|---:|---:|---|
| `overlap=0` | 224 | 5/5 | 6/10 | Rẻ nhất nhưng câu 2 và 3 lấy đúng tài liệu mà sai đoạn quan trọng. |
| `overlap=50` | 248 | 5/5 | **8/10** | Cân bằng tốt nhất; câu 1, 2, 4 trả lời đúng; câu 3 và 5 còn nhiễu. |
| `overlap=150` | 316 | 5/5 | 7/10 | Giữ ngữ cảnh tốt cho câu 3, nhưng câu 2 bị kéo sang phần danh sách hàng cấm. |

### Bảng kết quả cấu hình tốt nhất: `overlap=50`

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? | Câu trả lời của Agent (tóm tắt) |
|---|---|---|---:|---|---|
| 1 | Người mua có bao nhiêu ngày để gửi yêu cầu trả hàng hoàn tiền sau khi đơn hàng giao thành công? | `shopee-returns-refund-policy` — mục 3.2, nêu 15 ngày và 24 giờ với thực phẩm tươi sống/đông lạnh | +0.5979 | Có | Trả lời đúng: 15 ngày; thực phẩm tươi sống và đông lạnh là 24 giờ. |
| 2 | Người bán bị áp dụng những chế tài nào nếu đăng bán sản phẩm thuộc danh mục cấm? | `shopee-prohibited-products` — phần chế tài với các nhóm xử lý vi phạm | +0.5523 | Có | Liệt kê đúng các chế tài: xóa sản phẩm, giới hạn tài khoản, đình chỉ/xóa tài khoản, cấn trừ số dư/phong tỏa rút tiền, chế tài khác. |
| 3 | Ai chịu chi phí vận chuyển chiều hoàn trả sản phẩm? | `shopee-returns-refund-policy` — phần chi phí hoàn trả nhưng top-1 nghiêng về chi phí của Người Mua | +0.5907 | Có một phần | Agent trả lời lệch sang trường hợp Người Mua/Shopee hỗ trợ, chưa nêu đúng trọng tâm Người Bán chịu ở mục 7.1. |
| 4 | Thời gian Nhà Bán cam kết bảo hành tối đa là bao lâu? | `tiki-seller-warranty-faq` — FAQ 5 về thời gian cam kết bảo hành | +0.7527 | Có | Trả lời đúng: tối đa 30 ngày. |
| 5 | Shopee thu thập dữ liệu cá nhân của người dùng từ những nguồn nào? | `shopee-privacy-policy` — đúng tài liệu nhưng top-1 rơi vào phần loại dữ liệu/chia sẻ dữ liệu, chưa phải mục nguồn thu thập 2.2 | +0.6775 | Có một phần | Agent nói không tìm thấy nguồn cụ thể; chưa trả lời được danh sách nguồn trong gold answer. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** **5 / 5** nếu tính theo `doc_id`; **3 / 5** nếu tính nghiêm ngặt theo đúng mục chứa gold answer.

### Tự chấm theo `docs/SCORING.md`

| Câu | Điểm | Lý do |
|---|---:|---|
| 1 | 2/2 | Top-1 chứa đúng mục 3.2, agent trả lời đúng 15 ngày và ngoại lệ 24 giờ. |
| 2 | 2/2 | Với `overlap=50`, top-3 lấy được phần chế tài và agent liệt kê đúng các nhóm xử lý. |
| 3 | 1/2 | Có đúng tài liệu về chi phí hoàn trả, nhưng top-1 chưa phải mục 7.1 nên agent trả lời lệch trọng tâm. |
| 4 | 2/2 | Top-1 đúng FAQ bảo hành, agent trả lời đúng tối đa 30 ngày. |
| 5 | 1/2 | Đúng tài liệu privacy nhưng sai mục: trả về loại dữ liệu/chia sẻ dữ liệu thay vì nguồn thu thập. |
| **Tổng** | **8/10** | |

### Phân tích: overlap cao hơn có luôn tốt hơn không?

Kết quả của tôi cho thấy **không**. Tăng overlap giúp giảm rủi ro cắt đứt một điều khoản, nhưng cũng làm số chunk tăng và tạo thêm nhiều chunk gần giống nhau. Khi nhiều chunk trùng nội dung cạnh tranh trong top-k, hệ thống có thể lấy đúng tài liệu nhưng sai đoạn.

Với `overlap=0`, store chỉ có 224 chunk nên rẻ nhất, nhưng các câu hỏi dài có nhiều điều kiện dễ bị mất ngữ cảnh ở ranh giới chunk. Câu 2 và câu 3 là ví dụ: retrieval nhận ra đúng tài liệu Shopee, nhưng chunk trả về không chứa đủ phần chế tài hoặc phần trách nhiệm của Người Bán.

Với `overlap=150`, store tăng lên 316 chunk, tức tăng khoảng 41% so với `overlap=0`. Cấu hình này cứu câu 3 vì mục "TRÁCH NHIỆM VỀ CHI PHÍ VẬN CHUYỂN HOÀN TRẢ SẢN PHẨM CỦA NGƯỜI BÁN" xuất hiện rõ hơn trong top-3. Tuy nhiên, câu 2 lại bị kéo về các chunk liệt kê mặt hàng bị cấm ở mục 4, không phải phần chế tài ở mục 3.

Với `overlap=50`, số chunk là 248, chỉ tăng khoảng 10.7% so với không overlap nhưng cải thiện rõ câu 1, 2 và 4. Vì vậy đây là cấu hình tôi chọn: đủ overlap để giữ ngữ cảnh ngắn quanh ranh giới, nhưng chưa tạo quá nhiều chunk trùng lặp gây nhiễu.

### Hai failure case còn lại

**Câu 3 — nhầm giữa chi phí của Người Bán và Người Mua.**  
Trong tài liệu `shopee-returns-refund-policy`, mục 7 nói về trách nhiệm chi phí của Người Bán, còn mục 8 nói về chi phí hoàn trả của Người Mua. Hai mục rất gần nhau về từ khóa: "chi phí", "vận chuyển", "hoàn trả", "sản phẩm". Fixed-size chunking không hiểu cấu trúc mục nên dễ đưa mục 8 lên trước mục 7. Cách cải thiện là thêm metadata theo heading/mục hoặc dùng rerank để ưu tiên chunk có tiêu đề khớp câu hỏi.

**Câu 5 — đúng tài liệu nhưng sai sắc thái câu hỏi.**  
Câu hỏi hỏi "từ những nguồn nào", nhưng các chunk top đầu thường nói về "Shopee thu thập những dữ liệu gì" hoặc "chia sẻ dữ liệu với ai". Đây là lỗi semantic retrieval khá điển hình: embedding thấy cùng chủ đề dữ liệu cá nhân nhưng chưa phân biệt tốt giữa nguồn dữ liệu và loại dữ liệu. Cách cải thiện là chunk theo heading lớn của policy privacy hoặc tăng `top_k` rồi rerank theo keyword "nguồn", "bên thứ ba", "công ty liên kết".

**Điều tôi học được từ chiến lược của mình:**
> Fixed-size chunking không yếu vì nó đơn giản; nó yếu khi tài liệu có cấu trúc pháp lý nhiều mục nhỏ mà mình không đưa cấu trúc đó vào metadata. Overlap giúp giữ câu không bị cắt, nhưng overlap không thay thế được hiểu biết về heading. Với corpus chính sách thương mại điện tử, cấu hình vừa phải như `overlap=50` là điểm cân bằng tốt hơn việc tăng overlap thật cao.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|---|---:|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 9 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 8 / 10 |
| **Tổng phần cá nhân** | **57 / 60** |
