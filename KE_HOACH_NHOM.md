# Kế Hoạch Nhóm — Lab 7 K4: Embedding & Vector Store

> File hướng dẫn nội bộ của nhóm. Mỗi người đọc **mục của mình** rồi làm theo checklist.
> Thang điểm: Cá nhân 60đ + Nhóm 40đ = 100đ (chi tiết: `docs/SCORING.md`).

---

## PHẦN 0 — Những gì đã làm xong (dùng chung cả nhóm)

| Hạng mục | Trạng thái | Ghi chú |
|---|---|---|
| `src/chunking.py`, `src/store.py`, `src/agent.py` | ✅ Xong 15 TODO | **42/42 test pass** |
| `data/k4_ecommerce/` | ✅ 6 tài liệu công khai thật | Đã xóa 2 file placeholder `example.com` |
| `data/k4_ecommerce/sources.csv` | ✅ 6 dòng, khớp 1:1 với file | Không còn `example-template-replace-me` |
| `scripts/urls.csv` | ✅ 6 URL nguồn | Đã kiểm tra `robots.txt` — tất cả ALLOW |
| `scripts/similarity_demo.py` | ✅ Bài 3.3 (5 cặp câu + dự đoán) | Dự đoán viết cứng trong code |
| `report/REPORT_Quang.md` | ✅ Đầy đủ 5 phần, tự chấm 57/60 | Mỗi người tự viết bản của mình |

### Bộ tài liệu chung (6 tài liệu — KHÔNG ai được sửa)

| # | `doc_id` | Nguồn | `customer_role` | `category` | Cỡ |
|---|---|---|---|---|---|
| 1 | `shopee-returns-refund-policy` | help.shopee.vn/portal/4/article/77251 | `buyer` | `returns` | 26 KB |
| 2 | `shopee-prohibited-products` | help.shopee.vn/portal/4/article/77247 | `seller` | `prohibited` | 17 KB |
| 3 | `shopee-privacy-policy` | help.shopee.vn/portal/4/article/77244 | `both` | `privacy` | 58 KB |
| 4 | `tiki-seller-warranty-faq` | hocvien.tiki.vn/faq/cau-hoi-thuong-gap-ve-xu-ly-doi-tra-bao-hanh | `seller` | `warranty` | 21 KB |
| 5 | `ghn-compensation-policy` | ghn.vn/pages/chinh-sach-boi-thuong-cua-ghn | `both` | `shipping` | 21 KB |
| 6 | `ghn-terms-of-service` | ghn.vn/pages/dieu-khoan-su-dung | `both` | `terms` | 5 KB |

Metadata schema mỗi file (trong YAML front matter): `doc_id`, `title`, `source_url`,
`retrieved_at`, `document_version`, `customer_role`, `category`, `language`.

### Thiết lập môi trường (làm 1 lần, ~15 phút)

```bash
git pull
python -m venv .venv                              # nếu chưa có
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe -m pip install -r requirements-local.txt   # embedder thật, ~2GB
.venv/Scripts/python.exe -m pytest tests/ -q      # kỳ vọng: 42 passed
```

**Tạo file `.env`** (nằm trong `.gitignore`, mỗi người tự tạo — không push):

```bash
cp .env.example .env
```

rồi sửa nội dung thành:

```ini
EMBEDDING_PROVIDER=local
LOCAL_EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
HF_HUB_DISABLE_SYMLINKS_WARNING=1
LAB_DATA_DIR=data/k4_ecommerce
```

Có `.env` rồi thì **không cần** gõ `EMBEDDING_PROVIDER=local` trước mỗi lệnh nữa — `load_dotenv()`
đã được gọi sẵn trong `main.py`, `scripts/run_benchmark.py`, `scripts/similarity_demo.py`.

**Riêng `PYTHONIOENCODING` KHÔNG đặt được trong `.env`** — Python đọc biến này lúc khởi động
interpreter, trước khi `load_dotenv()` chạy. Trên Windows phải đặt ở tầng hệ thống:

```powershell
[Environment]::SetEnvironmentVariable("PYTHONIOENCODING","utf-8","User")
```

Không đặt thì mọi lệnh in tiếng Việt sẽ lỗi `UnicodeEncodeError` (console mặc định là cp1252).

Kiểm tra embedder thật đã chạy — kết quả **không được** là `mock embeddings fallback`:

```bash
.venv/Scripts/python.exe -c "from src import LocalEmbedder; e=LocalEmbedder(); print(e._backend_name, len(e('test')))"
# sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 384
```

---

## PHẦN 1 — 5 CÂU HỎI BENCHMARK CHUNG (đề xuất — nhóm duyệt rồi khóa lại)

> **Quy tắc:** cả 5 người chạy **đúng 5 câu này**, không ai đổi. Gold answer đều trích được
> từ corpus (đã verify bằng `grep`, có ghi rõ vị trí). Câu 2 và câu 4 cần `metadata_filter`
> → thỏa ràng buộc bắt buộc của `K4_VARIANT.md`.

| # | Câu hỏi | Câu trả lời chuẩn (Gold Answer) | Chunk nguồn |
|---|---|---|---|
| 1 | Người mua có bao nhiêu ngày để gửi yêu cầu trả hàng/hoàn tiền sau khi đơn hàng giao thành công? | **15 (mười lăm) ngày** kể từ lúc đơn hàng được cập nhật giao hàng thành công. Riêng thực phẩm **tươi sống và đông lạnh: 24 giờ**. | `shopee-returns-refund-policy`, mục **3.2** |
| 2 | Người bán bị áp dụng những chế tài nào nếu đăng bán sản phẩm thuộc danh mục cấm/hạn chế? | 5 nhóm chế tài: (i) sản phẩm bị xóa; (ii) tài khoản bị giới hạn quyền; (iii) tài khoản bị đình chỉ hoặc xóa; (iv) cấn trừ số dư, phong tỏa quyền rút tiền; (v) chế tài khác theo pháp luật (phạt hành chính, xử lý hình sự, bồi thường). | `shopee-prohibited-products`, mục **3** |
| 3 | Ai chịu chi phí vận chuyển chiều hoàn trả sản phẩm? | **Người Bán** chịu, trong 3 trường hợp: Shopee chấp thuận yêu cầu trả hàng/hoàn tiền không do lỗi Người Mua hoặc đơn vị vận chuyển; đơn giao không thành công; các ngoại lệ khác theo quyết định của Shopee. | `shopee-returns-refund-policy`, mục **7.1** |
| 4 | Thời gian Nhà Bán cam kết bảo hành tối đa là bao lâu? | **Tối đa không quá 30 ngày**, tính từ thời điểm Nhà Bán nhận được hàng đến khi bảo hành xong — **không tính thời gian vận chuyển**. | `tiki-seller-warranty-faq`, câu hỏi **số 5** |
| 5 | Shopee thu thập dữ liệu cá nhân của người dùng từ những nguồn nào? | Từ chính bạn, các công ty liên kết, các bên thứ ba và nguồn khác: đối tác kinh doanh (đơn vị vận chuyển, thanh toán), cơ quan đánh giá tín dụng, đối tác marketing/giới thiệu/khách hàng thân thiết, người dùng khác, và các nguồn dữ liệu công khai hoặc của nhà nước. | `shopee-privacy-policy`, mục **2.2** |

**Câu bắt buộc dùng metadata filter:**
- Câu 2 → `metadata_filter={"customer_role": "seller"}`
- Câu 4 → `metadata_filter={"customer_role": "seller"}` (hoặc `{"category": "warranty"}`)

**Vì sao 5 câu này đa dạng** (yêu cầu của `exercises.md`): 1 câu hỏi **con số/thời hạn**,
1 câu hỏi **danh sách liệt kê**, 1 câu hỏi **quy trách nhiệm**, 1 câu hỏi **cam kết dịch vụ**,
1 câu hỏi **tổng hợp đa nguồn** — mỗi loại thử một điểm yếu khác nhau của chunking.

---

## PHẦN 2 — CHIA CHIẾN LƯỢC: 5 NGƯỜI, 5 CÁCH KHÁC NHAU

Tất cả chạy **cùng 6 tài liệu** và **cùng 5 câu hỏi** ở trên. Chỉ khác chiến lược chia chunk.

| Thành viên | MSSV | Chiến lược | File tự viết | Trạng thái |
|---|---|---|---|---|
| Quang | — | **`SemanticParentChunker`** — cắt theo ngữ nghĩa (embedding) + trọng số tiêu đề cha | `src/strategies/quang_semantic.py` | ✅ xong — **8/10** |
| Lê Quý Thành | 2A202601168 | **`RecursiveChunker`** (có sẵn), tinh chỉnh `chunk_size` | `src/strategies/thanh_recursive.py` | ⬜ tự làm |
| Trần Quang Sáng | 2A202601446 | **`FixedSizeChunker`** (có sẵn), tinh chỉnh `overlap` | `src/strategies/sang_fixed.py` | ⬜ tự làm |
| Cao Các Tường | 2A202601236 | **`SentenceChunker`** (có sẵn), tinh chỉnh số câu | `src/strategies/tuong_sentence.py` | ⬜ tự làm |
| Lưu Nguyễn Ngọc Hân | 2A202601386 | **`FAQPairChunker`** — cắt theo cặp Câu hỏi–Đáp án | `src/strategies/han_faq.py` | ⬜ tự làm |

### Quy ước cho file chiến lược

Mỗi file chỉ cần một lớp có đúng một phương thức `chunk(text: str) -> list[str]`,
kèm hàm `build_chunker()` trả về cấu hình đã chọn. Xem `quang_semantic.py` làm mẫu.

```python
# src/strategies/<ten>_<chien_luoc>.py
class MyChunker:
    """Mô tả chiến lược + LÝ DO THIẾT KẾ + ĐIỂM YẾU (phần này chấm 15đ)."""
    def chunk(self, text: str) -> list[str]:
        ...

def build_chunker() -> MyChunker:
    return MyChunker(...)
```

Dùng trong benchmark:
```python
from ingest import build_knowledge_base
from src.strategies.<ten>_<chien_luoc> import build_chunker
store = build_knowledge_base("data/k4_ecommerce", embedding_fn=embedder, chunker=build_chunker())
```

### Cấu trúc nộp bài (đã chốt)

```
src/
  chunking.py store.py agent.py   ← CHUNG, 42/42 pass, KHÔNG ai sửa
  strategies/<ten>_<chien_luoc>.py ← mỗi người 1 file
report/
  REPORT_<Ten>.md                 ← mỗi người 1 file riêng (VD: REPORT_LeQuyThanh.md)
  REPORT_NHOM.md                  ← 1 bản chung
scripts/
  run_benchmark.py                ← dùng chung, chọn người bằng --member
  sweep_heading_weight.py         ← quét tham số (mẫu cho các bạn viết sweep của mình)
  similarity_demo.py              ← bài 3.3, mỗi người tự đổi 5 cặp câu của mình
```

Lấy template báo cáo cá nhân (file gốc đã bị xóa khỏi repo):
```bash
git show 82b2330:report/REPORT_CANHAN.md > report/REPORT_<Ten>.md
```

> ⚠️ **Không** tạo thư mục tên riêng trong `src/`. `tests/test_solution.py` import thẳng
> package `src`, đặt code trong `src/<ten>/` sẽ làm hỏng toàn bộ 42 test.

### Số liệu baseline (đã chạy sẵn, `chunk_size=500`)

| Tài liệu | Chiến lược | Count | Avg | Min | Max |
|---|---|---|---|---|---|
| `shopee-returns-refund-policy` (19.616 ký tự) | `fixed_size` | 44 | 494.7 | 266 | 500 |
| | `by_sentences` | 48 | 405.8 | **24** | **984** |
| | `recursive` | 62 | 314.4 | 27 | 496 |
| `shopee-prohibited-products` (12.857 ký tự) | `fixed_size` | 29 | 491.6 | 257 | 500 |
| | `by_sentences` | 56 | 227.2 | 30 | 742 |
| | `recursive` | 30 | 426.6 | 307 | 498 |
| `ghn-terms-of-service` (3.798 ký tự) | `fixed_size` | 9 | 466.4 | 198 | 500 |
| | `by_sentences` | 10 | 376.7 | 163 | 510 |
| | `recursive` | 10 | 378.0 | 154 | 488 |

Lệnh tự chạy lại bảng này:
```bash
export PYTHONIOENCODING=utf-8
.venv/Scripts/python.exe -c "
from ingest import load_documents
from src.chunking import ChunkingStrategyComparator
docs = {d.id: d for d in load_documents('data/k4_ecommerce')}
d = docs['shopee-returns-refund-policy']
for name, st in ChunkingStrategyComparator().compare(d.content, chunk_size=500).items():
    lens = [len(c) for c in st['chunks']]
    print(f'{name:13s} count={st[\"count\"]:4d} avg={st[\"avg_length\"]:7.1f} min={min(lens):4d} max={max(lens):5d}')
"
```

---

### 👤 Quang — `SemanticParentChunker` ✅ ĐÃ XONG (8/10)

**Ý tưởng:** không dùng luật chuỗi ký tự nào để quyết định chỗ cắt. Nhúng từng câu, đo cosine
giữa các câu liền kề, cắt tại 10% vị trí có khoảng cách ngữ nghĩa lớn nhất → ranh giới chunk là
ranh giới **Ý**. Cộng thêm tham số `heading_weight` điều khiển mức độ tiêu đề mục cha tham gia
vào vector (0 = không, 1 = ghép một lần, 2 = lặp hai lần).

**Kết quả sweep (170 chunk, cùng 5 câu benchmark):**

| `heading_weight` | 0 | 1 | 2 |
|---|---|---|---|
| Điểm | 7/10 | **6/10** | **8/10** |

Kết quả **không đơn điệu** (7 → 6 → 8): tiêu đề vừa là nhiễu vừa là tín hiệu. `w=1` tệ nhất vì
tiêu đề có mặt nhưng bị phần thân áp đảo — không đủ mạnh để dẫn hướng mà vẫn làm loãng vector.
Chi tiết trong `report/REPORT_Quang.md`.

**Nhược điểm:** chi phí nhúng cao (phải nhúng từng câu); **bắt buộc** dùng embedder thật —
chạy bằng mock thì ranh giới cắt hoàn toàn ngẫu nhiên.

- [x] Viết `src/strategies/quang_semantic.py`
- [x] Chạy `scripts/sweep_heading_weight.py`, chọn `heading_weight=2`
- [x] Chạy 5 câu benchmark, ghi top-3
- [x] Điền `report/REPORT_Quang.md` Phần 5
- [ ] Gửi kết quả cho nhóm để tổng hợp bảng so sánh

---

### 👤 Lê Quý Thành — 2A202601168 — `RecursiveChunker` (tinh chỉnh)

**Ý tưởng:** dùng chiến lược có sẵn, **không viết code mới**, nhưng **quét tham số** để tìm
`chunk_size` tối ưu. Đây là baseline mạnh nhất trong 3 chiến lược có sẵn.

**Vì sao chọn:** ưu tiên `\n\n` → `\n` → `. ` → ` ` nên vừa tôn trọng ranh giới đoạn vừa
khống chế được kích thước trần (max luôn ≤ `chunk_size`).

**Nhược điểm phải nêu:** tạo nhiều chunk nhất (62 chunk trên Shopee returns, so với 44 của
fixed_size) → tốn chi phí nhúng; chunk nhỏ dễ **tách rời khỏi tiêu đề mục** (ví dụ "I. THUẬT NGỮ"
bị tách khỏi phần định nghĩa bên dưới).

```python
from ingest import build_knowledge_base
from src.chunking import RecursiveChunker
store = build_knowledge_base("data/k4_ecommerce", embedding_fn=embedder,
                             chunker=RecursiveChunker(chunk_size=600))
```

- [ ] Thử ít nhất **3 giá trị** `chunk_size`: 300 / 500 / 800 — ghi lại count + avg mỗi lần
- [ ] Chọn 1 giá trị tốt nhất, giải thích **tại sao** (dựa trên kết quả 5 câu hỏi, không đoán)
- [ ] Chạy 5 câu hỏi với cấu hình đã chọn, ghi top-3
- [ ] Điền `report/REPORT_<Ten>.md` Phần 5 + gửi kết quả cho nhóm

---

### 👤 Trần Quang Sáng — 2A202601446 — `FixedSizeChunker` (tinh chỉnh overlap)

**Ý tưởng:** dùng chiến lược có sẵn, **quét tham số `overlap`** để chứng minh overlap cứu vãn
việc cắt giữa điều khoản đến mức nào. Đây là **đối cực** với `HeadingChunker`.

**Vì sao chọn:** kích thước chunk cực đều (min 266 – max 500) → điểm similarity so sánh công bằng
giữa các chunk, không bị chunk ngắn/dài làm nhiễu.

**Nhược điểm phải nêu:** cắt cứng theo ký tự nên **cắt giữa câu, giữa điều khoản**. Ví dụ cụ thể
đáng đưa vào báo cáo: câu "Người Mua có thể gửi yêu cầu trả hàng/hoàn tiền trong vòng **15 (mười lăm)
ngày**…" nếu bị cắt đôi thì chunk chứa "15 ngày" mất ngữ cảnh, chunk kia mất con số → câu hỏi 1 fail.

```python
from src.chunking import FixedSizeChunker
store = build_knowledge_base("data/k4_ecommerce", embedding_fn=embedder,
                             chunker=FixedSizeChunker(chunk_size=500, overlap=150))
```

- [ ] Thử ít nhất **3 mức** `overlap`: 0 / 50 / 150 (giữ `chunk_size=500`)
- [ ] **Điểm ăn tiền:** tìm 1 câu hỏi mà `overlap=0` fail nhưng `overlap=150` pass → chụp lại
- [ ] Chạy 5 câu hỏi với cấu hình tốt nhất, ghi top-3
- [ ] Điền `report/REPORT_<Ten>.md` Phần 5 + gửi kết quả cho nhóm

---

### 👤 Cao Các Tường — 2A202601236 — `SentenceChunker` (tinh chỉnh số câu)

**Ý tưởng:** dùng chiến lược có sẵn, quét `max_sentences_per_chunk`. Nhiệm vụ đặc biệt của bạn là
**chứng minh bằng số liệu tại sao chiến lược này KHÔNG hợp với văn bản chính sách** — đây chính là
phần ăn điểm "Thiết kế chiến lược" (15đ, cao hơn cả điểm retrieval 10đ).

**Vì sao chọn:** không bao giờ cắt giữa câu → chunk luôn đọc trôi chảy, mạch lạc nhất về mặt ngôn ngữ.

**Nhược điểm phải nêu (có số liệu sẵn):** độ dài **cực lệch** — trên `shopee-returns-refund-policy`
có chunk chỉ **24 ký tự** (một tiêu đề như "1.2. Phạm Vi Áp Dụng") nằm chung store với chunk
**984 ký tự**, lệch **41 lần**. Chunk quá ngắn có ít từ → vector nhiễu, dễ ăn điểm similarity cao
giả tạo. Trên `shopee-prohibited-products` (tài liệu dạng danh sách gạch đầu dòng) nó vụn ra
**56 chunk** so với 29 của fixed_size.

```python
from src.chunking import SentenceChunker
store = build_knowledge_base("data/k4_ecommerce", embedding_fn=embedder,
                             chunker=SentenceChunker(max_sentences_per_chunk=4))
```

- [ ] Thử **3 giá trị** `max_sentences_per_chunk`: 2 / 4 / 6 — ghi count, avg, **min và max**
- [ ] **Điểm ăn tiền:** in ra chunk ngắn nhất và dài nhất, dán vào báo cáo làm bằng chứng
- [ ] Chạy 5 câu hỏi với cấu hình tốt nhất, ghi top-3
- [ ] Điền `report/REPORT_<Ten>.md` Phần 5 + gửi kết quả cho nhóm

---

### 👤 Lưu Nguyễn Ngọc Hân — 2A202601386 — `FAQPairChunker` (cặp Hỏi–Đáp)

**Ý tưởng:** file `tiki-seller-warranty-faq.md` có cấu trúc FAQ đánh số rõ ràng
(`5. Thời gian Nhà Bán cam kết bảo hành là bao lâu?` → đoạn trả lời bên dưới).
Cắt sao cho **mỗi chunk = 1 câu hỏi + toàn bộ câu trả lời của nó**.

**Vì sao chọn:** câu hỏi benchmark của người dùng có dạng gần giống câu hỏi FAQ → embedding của
query khớp thẳng vào embedding của câu hỏi trong chunk. Kỳ vọng **thắng áp đảo câu 4**
("Thời gian Nhà Bán cam kết bảo hành tối đa là bao lâu?" — trùng gần như nguyên văn FAQ số 5).
`K4_VARIANT.md` chấp nhận FAQ pair là chiến lược điều/khoản hợp lệ.

**Nhược điểm phải nêu:** chỉ hoạt động tốt trên tài liệu có định dạng FAQ. 5 tài liệu còn lại là
văn bản chính sách thuần → phải fallback (dùng `RecursiveChunker` cho file không có dấu hiệu FAQ),
và phải giải thích rõ cơ chế fallback đó trong báo cáo.

```python
# src/strategies/han_faq.py — gợi ý khung
import re
from .chunking import RecursiveChunker

QUESTION_RE = re.compile(r"^\s*\d+\.\s+.+\?\s*$", re.MULTILINE)

class FAQPairChunker:
    """Cắt theo cặp Câu hỏi–Đáp án; tài liệu không có FAQ thì fallback RecursiveChunker."""
    def __init__(self, chunk_size: int = 800):
        self.chunk_size = chunk_size
        self._fallback = RecursiveChunker(chunk_size=chunk_size)

    def chunk(self, text: str) -> list[str]:
        positions = [m.start() for m in QUESTION_RE.finditer(text)]
        if len(positions) < 2:                 # không phải tài liệu FAQ
            return self._fallback.chunk(text)
        # ... cắt text theo các mốc positions, mỗi lát = 1 cặp Q&A
```

- [ ] Viết `src/strategies/han_faq.py`
- [ ] Kiểm tra: trên `tiki-seller-warranty-faq.md` phải ra **≥11 chunk** (file có 11 câu FAQ ở mục I)
- [ ] Kiểm tra: trên `ghn-terms-of-service.md` phải tự động fallback (không có `?` đánh số)
- [ ] Chạy 5 câu hỏi, ghi top-3 — **so sánh riêng câu 4** với 4 bạn còn lại
- [ ] Điền `report/REPORT_<Ten>.md` Phần 5 + gửi kết quả cho nhóm

---

## PHẦN 3 — CÁCH CHẠY BENCHMARK (giống nhau cho cả 5 người)

### Bước 1 — Bật embedder thật (BẮT BUỘC)

README nói rõ: mock sinh vector **gần như ngẫu nhiên**, KHÔNG được dùng để kết luận chiến lược
nào tốt hơn. Thứ tự thử:

```bash
.venv/Scripts/python.exe -m pip install -r requirements-local.txt   # torch, ~2GB, chạy 1 lần
export EMBEDDING_PROVIDER=local
.venv/Scripts/python.exe -c "from src import LocalEmbedder; e=LocalEmbedder(); print(e._backend_name, len(e('test')))"
```

Kết quả in ra **không được** là `mock embeddings fallback`. Nếu torch không cài được:
1. Tạo venv Python 3.11 riêng: `uv python install 3.11` rồi `uv venv --python 3.11 .venv311`
2. Hoặc dùng OpenAI: `EMBEDDING_PROVIDER=openai` + `OPENAI_API_KEY` trong `.env`

### Bước 2 — Chạy 5 câu hỏi

```bash
export PYTHONIOENCODING=utf-8
.venv/Scripts/python.exe scripts/run_benchmark.py --member <ten> --markdown
```

(Script này Quang viết chung, nhận tham số `--chunker` để mỗi người chọn chiến lược của mình.)

### Bước 3 — Tự chấm theo rubric `docs/SCORING.md`

Mỗi câu 2 điểm:
- **2đ** — top-3 có chunk liên quan **và** câu trả lời của agent chính xác
- **1đ** — top-3 có chunk liên quan nhưng câu trả lời thiếu chi tiết, **hoặc** chunk liên quan không ở top-1
- **0đ** — top-3 không có chunk liên quan

### Bước 4 — Nộp kết quả cho nhóm

Mỗi người gửi vào nhóm chat theo mẫu:

```
Tên: ...            MSSV: ...
Chiến lược: ...     Tham số: ...
Tổng chunk trong store: ...
Câu 1: [top-1 doc_id] score=... relevant=Y/N  điểm=?/2
Câu 2: ...
Câu 3: ...
Câu 4: ...
Câu 5: ...
TỔNG: ?/10
Failure case: câu số ... — lý do ...
```

---

## PHẦN 4 — AI VIẾT PHẦN NÀO TRONG BÁO CÁO

### `report/REPORT_<Ten>.md` — **mỗi người nộp 1 bản riêng**

| Phần | Điểm | Ai làm |
|---|---|---|
| 1. Khởi động (cosine + chunking math) | 5 | **Mỗi người tự viết** (đáp án chung: 23 chunk; overlap=100 → 25 chunk) |
| 2. Hướng tiếp cận (giải thích code `src`) | 10 | **Mỗi người tự viết theo code mình hiểu** |
| 3. Hoàn thiện code (dán output pytest) | 30 | Mỗi người tự chạy `pytest tests/ -v`, dán output |
| 4. Dự đoán độ tương tự (5 cặp câu) | 5 | Mỗi người **tự nghĩ 5 cặp câu của riêng mình** |
| 5. Kết quả truy xuất (5 câu benchmark) | 10 | Kết quả từ **chiến lược riêng** của mình |

> ⚠️ Phần 2 và Phần 4 **không được copy của nhau** — mỗi người lập trình và dự đoán khác nhau,
> giảng viên đọc 5 bản giống hệt là mất điểm cả nhóm.

### `REPORT_NHOM.md` — **1 bản chung**, chia người viết

| Phần | Điểm | Người phụ trách |
|---|---|---|
| 1. Lựa chọn tài liệu (scope + bảng kiểm kê 6 tài liệu + metadata schema) | 10 | **Cao Các Tường** |
| 2. Thiết kế chiến lược (bảng baseline + 5 khối chiến lược + bảng so sánh) | 15 | **Quang** tổng hợp, mỗi người gửi khối của mình |
| 3. Câu hỏi đánh giá & chất lượng truy xuất (5 query + bảng kết quả nhóm) | 10 | **Lê Quý Thành** |
| 4. Demo & bài học (failure analysis + slide) | 5 | **Trần Quang Sáng** + **Lưu Nguyễn Ngọc Hân** |

---

## PHẦN 5 — CHECKLIST NỘP BÀI

- [ ] `pytest tests/ -v` → 42/42 pass (từng người)
- [ ] `src/` có đủ 15 TODO đã viết + file chiến lược riêng
- [ ] `data/k4_ecommerce/` — 6 tài liệu, `sources.csv` khớp 1:1, không còn `example.com`
- [ ] `report/REPORT_NHOM.md` — 1 bản, không còn ô trống
- [ ] `report/REPORT_<Ten>.md` — 5 bản riêng, Phần 2 và 4 khác nhau giữa các thành viên
- [ ] Slide demo: 1 slide chiến lược của mỗi người + 1 slide bảng so sánh + 1 slide failure case

---

## Việc còn đang chờ

1. **Nhóm duyệt 5 câu hỏi ở Phần 1** — duyệt xong thì khóa lại, không đổi nữa
2. **4 bạn viết file chiến lược của mình** trong `src/strategies/` rồi chạy
   `python scripts/run_benchmark.py --member <ten> --markdown`
3. Gửi kết quả về cho Quang tổng hợp bảng so sánh liên thành viên (Phần 2 của `REPORT_NHOM.md`)
4. Dọn rác điều hướng còn sót trong `tiki-seller-warranty-faq.md` (menu "Chương trình Freeship Xtra…")
   và `ghn-*.md` ("Trang chủ") — hiện chưa ảnh hưởng kết quả nhưng nên làm trước khi nộp

### Hai câu benchmark hiện chưa ai giải được (cơ hội ăn điểm)

Chiến lược của Quang fail ở câu 1 và câu 5. Nếu chiến lược của bạn giải được một trong hai,
đó là luận điểm mạnh nhất cho phần so sánh nhóm:

- **Câu 1** — bị `tiki-seller-warranty-faq` FAQ 8 ("Nhà Bán có thời gian bao lâu để xác nhận
  yêu cầu đổi, trả, bảo hành?") đánh bại. Hai tài liệu cùng nói về "thời hạn xử lý đổi trả",
  một cho Người Mua một cho Nhà Bán. Gợi ý: thử `metadata_filter={"customer_role": "buyer"}`.
- **Câu 5** — `shopee-privacy-policy.md` dài 58 KB, hàng chục mục đều chứa động từ "thu thập".
  Câu hỏi "từ những **nguồn** nào" khác "**dữ liệu gì**" chỉ ở một danh từ. Gợi ý: tăng `top_k`
  lên 5, hoặc chunk nhỏ hơn để mỗi chunk có phạm vi hẹp.
