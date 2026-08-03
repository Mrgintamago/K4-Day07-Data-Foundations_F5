# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** F5
**Thành viên:** Quang · Lê Quý Thành (2A202601168) · Trần Quang Sáng (2A202601446) · Cao Các Tường (2A202601236) · Lưu Nguyễn Ngọc Hân (2A202601386)
**Ngày:** 2026-08-03

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Phạm vi bộ tài liệu (Scope)

**Chủ đề (cố định theo lớp K4):** Chính sách thương mại điện tử / hỗ trợ khách hàng (thanh toán, đổi trả, giao hàng, quyền riêng tư, điều kiện người bán…).

**Phạm vi cụ thể nhóm tập trung:**
> **Vòng đời sau khi đặt hàng trên sàn TMĐT Việt Nam**: đổi trả & hoàn tiền (phía người mua),
> quy định đăng bán & chế tài (phía người bán), trách nhiệm vận chuyển và bồi thường (đơn vị
> giao hàng), và quyền riêng tư dữ liệu. Nhóm chọn phạm vi này vì nó cho phép đặt câu hỏi
> **cùng chủ đề nhưng khác đối tượng** (buyer vs seller) — điều kiện cần để `search_with_filter()`
> thực sự có tác dụng thay vì chỉ là tính năng trang trí.

### Danh sách tài liệu (Data Inventory)

6 tài liệu, tất cả là trang chính sách công khai, thu thập bằng `scripts/fetch_public_pages.py`
(có kiểm tra `robots.txt` trước mỗi request, giãn cách 1.5 giây).

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | Chính sách trả hàng và hoàn tiền Shopee | https://help.shopee.vn/portal/4/article/77251 | 2026-08-03 / not-stated | 19.616 | `doc_id=shopee-returns-refund-policy`, `customer_role=buyer`, `category=returns`, `language=vi` |
| 2 | Chính sách cấm/hạn chế sản phẩm Shopee | https://help.shopee.vn/portal/4/article/77247 | 2026-08-03 / not-stated | 12.857 | `doc_id=shopee-prohibited-products`, `customer_role=seller`, `category=prohibited`, `language=vi` |
| 3 | Chính sách bảo mật Shopee | https://help.shopee.vn/portal/4/article/77244 | 2026-08-03 / not-stated | 43.112 | `doc_id=shopee-privacy-policy`, `customer_role=both`, `category=privacy`, `language=vi` |
| 4 | FAQ xử lý đổi–trả–bảo hành cho Nhà Bán (Tiki) | https://hocvien.tiki.vn/faq/cau-hoi-thuong-gap-ve-xu-ly-doi-tra-bao-hanh/ | 2026-08-03 / not-stated | 15.440 | `doc_id=tiki-seller-warranty-faq`, `customer_role=seller`, `category=warranty`, `language=vi` |
| 5 | Chính sách bồi thường Giao Hàng Nhanh | https://ghn.vn/pages/chinh-sach-boi-thuong-cua-ghn | 2026-08-03 / not-stated | 15.691 | `doc_id=ghn-compensation-policy`, `customer_role=both`, `category=shipping`, `language=vi` |
| 6 | Điều khoản sử dụng dịch vụ Giao Hàng Nhanh | https://ghn.vn/pages/dieu-khoan-su-dung | 2026-08-03 / not-stated | 3.798 | `doc_id=ghn-terms-of-service`, `customer_role=both`, `category=terms`, `language=vi` |

**Tổng: 110.514 ký tự.** Kiểm kê đầy đủ ở `data/k4_ecommerce/sources.csv` (khớp 1:1 với file `.md`).

`document_version = not-stated` vì cả 6 trang nguồn đều **không công bố số phiên bản hay ngày
hiệu lực** trên trang. Nhóm ghi đúng như `docs/DATA_COLLECTION.md` quy định thay vì bịa số hiệu.

**Hai nguồn đã loại bỏ:** trang đổi trả của Tiki (`hotro.tiki.vn`) và trang hoàn tiền của Lazada
(`lazada.vn/helpcenter`) là **trang render bằng JavaScript** — crawler chỉ lấy được vỏ HTML rỗng.
Nhóm không dùng nội dung không trích xuất được thay vì để chunk rác vào store. Trang
`thegioididong.com` bị `robots.txt` chặn nên nhóm **không crawl**.

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.
- [x] `robots.txt` được kiểm tra trước mỗi request; nguồn bị chặn (`thegioididong.com`) đã bị loại, không tìm cách lách.
- [x] Giãn cách tối thiểu 1.5 giây giữa các request, có `User-Agent` định danh rõ.
- [x] Đã xóa 2 file khởi động placeholder (`example.com`) và mọi dòng `example-template-replace-me` trong `sources.csv`.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `doc_id` | string | `shopee-returns-refund-policy` | Khóa định danh tài liệu; `delete_document()` và mọi thao tác lọc theo tài liệu đều dựa vào trường này. Được gắn lên **từng chunk**, không chỉ tài liệu gốc. |
| `customer_role` | enum `buyer`/`seller`/`both` | `seller` | **Trường lọc quan trọng nhất của K4.** Corpus có nhiều tài liệu cùng nói về "đổi trả" nhưng khác đối tượng; không lọc thì câu hỏi phía người bán bị tài liệu phía người mua chen vào top-3 (xem phân tích câu 1 ở Phần 3). |
| `category` | enum | `returns`, `prohibited`, `privacy`, `warranty`, `shipping`, `terms` | Thu hẹp theo loại chính sách khi câu hỏi đã rõ chủ đề; hữu ích khi `customer_role` quá rộng (nhiều tài liệu là `both`). |
| `source_url` | URL | `https://help.shopee.vn/portal/4/article/77251` | Truy vết câu trả lời về đúng trang gốc — điều kiện để kiểm chứng gold answer và để người đọc tự xác minh. |
| `retrieved_at` | date | `2026-08-03` | Kiểm tra độ mới của chính sách; chính sách TMĐT thay đổi thường xuyên nên biết ngày lấy là bắt buộc. |
| `document_version` | string | `not-stated` | Phân biệt phiên bản chính sách khi nguồn có công bố; ghi `not-stated` khi nguồn không nêu. |
| `language` | string | `vi` | Dự phòng cho corpus đa ngữ; hiện toàn bộ là tiếng Việt nên chưa dùng để lọc. |
| `chunk_index` | int | `12` | Vị trí chunk trong tài liệu — dùng để lấy chunk liền kề khi cần mở rộng ngữ cảnh. |
| `parent_heading` | string | `7. TRÁCH NHIỆM VỀ CHI PHÍ VẬN CHUYỂN…` | *(chỉ có ở chiến lược `SemanticParentChunker` của Quang)* Lưu tiêu đề mục cha tách khỏi phần đem đi nhúng, cho phép điều khiển mức tiêu đề ảnh hưởng lên vector. |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare(text, chunk_size=500)` trên 3 tài liệu đại diện cho
3 kiểu cấu trúc khác nhau: văn bản điều khoản dài, văn bản dạng danh sách liệt kê, và văn bản
điều khoản ngắn.

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Min–Max (độ lệch) | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|-------------------|
| `shopee-returns-refund-policy`<br>19.616 ký tự — điều khoản đánh số nhiều cấp | FixedSizeChunker (`fixed_size`) | 44 | 494,7 | 266–500 (**1,9x**) | ❌ Cắt giữa câu. Câu "…trong vòng 15 (mười lăm) ngày…" có nguy cơ bị tách khỏi ngữ cảnh mục 3.2 |
| | SentenceChunker (`by_sentences`) | 48 | 405,8 | **24–984 (41,0x)** | ⚠️ Không cắt giữa câu nhưng chunk 24 ký tự là một tiêu đề đứng lẻ ("1.2. Phạm Vi Áp Dụng"), vô nghĩa khi truy xuất |
| | RecursiveChunker (`recursive`) | 62 | 314,4 | 27–496 (18,4x) | ⚠️ Tôn trọng ranh giới đoạn, nhưng chunk nhỏ dễ tách khỏi tiêu đề mục cha |
| `shopee-prohibited-products`<br>12.857 ký tự — danh sách gạch đầu dòng (4.1→4.24) | FixedSizeChunker (`fixed_size`) | 29 | 491,6 | 257–500 (1,9x) | ❌ Cắt ngang danh mục cấm, một danh mục bị chia hai chunk |
| | SentenceChunker (`by_sentences`) | **56** | 227,2 | 30–742 (24,7x) | ❌ **Vụn nhất** — gần gấp đôi fixed_size vì mỗi dòng danh sách thành một "câu" |
| | RecursiveChunker (`recursive`) | 30 | 426,6 | 307–498 (**1,6x**) | ✅ **Tốt nhất trên tài liệu này** — `\n\n` khớp đúng ranh giới giữa các danh mục |
| `ghn-terms-of-service`<br>3.798 ký tự — điều khoản ngắn | FixedSizeChunker (`fixed_size`) | 9 | 466,4 | 198–500 (2,5x) | ⚠️ Chấp nhận được vì tài liệu ngắn, ít cơ hội cắt sai |
| | SentenceChunker (`by_sentences`) | 10 | 376,7 | 163–510 (3,1x) | ✅ Ổn — tài liệu ngắn nên độ lệch không bùng phát |
| | RecursiveChunker (`recursive`) | 10 | 378,0 | 154–488 (3,2x) | ✅ Gần như trùng `by_sentences`, nhưng max nhỏ hơn (488 vs 510) |

**Ba kết luận rút ra từ baseline:**

1. **Không có chiến lược nào thắng trên mọi tài liệu.** `RecursiveChunker` xuất sắc trên tài liệu
   danh sách (độ lệch 1,6x) nhưng lại vụn nhất trên tài liệu điều khoản dài (62 chunk, độ lệch 18,4x).
   Chất lượng chunking phụ thuộc **cấu trúc tài liệu** nhiều hơn phụ thuộc thuật toán.
2. **Cột Min–Max quan trọng hơn cột trung bình.** Ba chiến lược trên `shopee-returns` có trung bình
   khá gần nhau (314–495) nhưng độ lệch chênh **hơn 20 lần** (1,9x vs 41,0x). Trung bình che giấu
   việc `by_sentences` sinh ra chunk 24 ký tự — thứ sẽ phá hỏng bảng xếp hạng similarity vì vector
   của chunk quá ngắn rất nhiễu.
3. **Tài liệu càng ngắn, ba chiến lược càng giống nhau.** Trên `ghn-terms-of-service` (3.798 ký tự)
   cả ba cho 9–10 chunk với độ lệch 2,5–3,2x. Khác biệt giữa các chiến lược chỉ thực sự lộ ra trên
   tài liệu dài và có cấu trúc — đó là lý do nhóm chọn corpus có cả tài liệu 3.798 lẫn 43.112 ký tự.

Lệnh tái lập:
```bash
python -c "
from ingest import load_documents
from src.chunking import ChunkingStrategyComparator
docs = {d.id: d for d in load_documents('data/k4_ecommerce')}
d = docs['shopee-returns-refund-policy']
for name, st in ChunkingStrategyComparator().compare(d.content, chunk_size=500).items():
    L = [len(c) for c in st['chunks']]
    print(name, st['count'], st['avg_length'], min(L), max(L))
"
```

### Chiến lược của từng thành viên

Nhóm 5 người, mỗi người **một chiến lược khác nhau**, cùng chạy trên 6 tài liệu và 5 câu hỏi ở Phần 3.
Mã nguồn đặt trong `src/strategies/<ten>_<chien_luoc>.py` — **không ai sửa `src/chunking.py`** để phần
chung luôn giữ 42/42 test pass.

---

**Thành viên 1 — Quang** · `src/strategies/quang_semantic.py`

- **Loại chiến lược:** custom — `SemanticParentChunker` (cắt theo ngữ nghĩa + trọng số tiêu đề cha)
- **Mô tả & lý do chọn cho chủ đề này:** Ba chiến lược dựng sẵn đều **cắt mù** — chỉ nhìn dấu câu,
  dấu phân cách hoặc số ký tự, không cái nào *đọc* nội dung. Chiến lược này nhúng **từng câu**, đo
  cosine giữa các câu liền kề, rồi cắt tại phân vị 90 của khoảng cách ngữ nghĩa: ranh giới chunk trở
  thành ranh giới **Ý**. Cơ chế thứ hai giải quyết vấn đề riêng của văn bản chính sách: tiêu đề mục
  cha được lưu tách trong `metadata["parent_heading"]`, và tham số `heading_weight` điều khiển **mức
  độ tiêu đề tham gia vào vector** — thứ mà không chiến lược dựng sẵn nào làm được vì chúng coi văn
  bản là chuỗi phẳng.
- **Tham số cuối:** `breakpoint_percentile=90`, `heading_weight=2`, `max_chunk_size=900`, `min_sentences=2`
  → **228 chunk**, đạt **8/10** (cao nhất nhóm).
- **Code snippet:**

```python
# src/strategies/quang_semantic.py — phần cốt lõi
def _semantic_split(self, text: str) -> list[str]:
    sentences = [s.strip() for s in SENTENCE_RE.split(text) if s.strip()]
    if len(sentences) <= self.min_sentences:
        return [text.strip()] if text.strip() else []

    vectors = [self.embedding_fn(s) for s in sentences]
    # Khoảng cách ngữ nghĩa giữa hai câu liền kề: càng lớn càng nên cắt.
    distances = [
        1.0 - compute_similarity(vectors[i], vectors[i + 1])
        for i in range(len(sentences) - 1)
    ]
    threshold = self._percentile(distances, self.breakpoint_percentile)

    chunks, current = [], [sentences[0]]
    for index, distance in enumerate(distances):
        if distance >= threshold and len(current) >= self.min_sentences:
            chunks.append(" ".join(current))
            current = [sentences[index + 1]]
        else:
            current.append(sentences[index + 1])
    if current:
        chunks.append(" ".join(current))
    return chunks

def embed_text(self, child: str, parent_heading: str) -> str:
    """Phần đem đi NHÚNG — heading_weight quyết định tiêu đề nặng bao nhiêu."""
    if not parent_heading or self.heading_weight == 0:
        return child
    prefix = "\n".join([parent_heading] * self.heading_weight)
    return f"{prefix}\n{child}"
```

- **Thí nghiệm đi kèm** (`scripts/sweep_heading_weight.py`, cùng 170 chunk, cùng 5 câu):

| `heading_weight` | 0 (bỏ tiêu đề) | 1 (ghép một lần) | 2 (lặp hai lần) |
|---|---|---|---|
| Điểm | 7/10 | **6/10** | **9/10** ← chọn |

  Kết quả **không đơn điệu (7 → 6 → 9)**. Giải thích: tiêu đề mục **vừa là nhiễu vừa là tín hiệu**.
  Câu hỏi 3 ("ai chịu chi phí vận chuyển") được trả lời bởi chính tiêu đề *"7. TRÁCH NHIỆM VỀ CHI PHÍ
  VẬN CHUYỂN HOÀN TRẢ SẢN PHẨM CỦA NGƯỜI BÁN"*; bỏ tiêu đề đi thì mất tín hiệu. Nhưng `w=1` lại **tệ
  hơn cả hai cực** vì tiêu đề có mặt mà bị phần thân dài áp đảo — không đủ mạnh để dẫn hướng nhưng
  vẫn đủ để làm loãng vector nội dung.

---

**Thành viên 2 — Lê Quý Thành (2A202601168)** · `src/strategies/thanh_recursive.py`

- **Loại chiến lược:** `RecursiveChunker` (dựng sẵn), tinh chỉnh `chunk_size` — lớp bọc
  `ThanhRecursiveChunker`
- **Mô tả & lý do chọn cho chủ đề này:** Không viết thuật toán mới mà khai thác tối đa chiến lược
  dựng sẵn mạnh nhất. `RecursiveChunker` cắt đệ quy theo thứ tự ưu tiên `"\n\n" → "\n" → ". " → " "`,
  nên nó **tự thích ứng với mọi loại tài liệu** mà không cần regex hay giả định về cấu trúc heading —
  điểm mạnh thật sự khi corpus trộn 3 kiểu văn bản (điều khoản đánh số, danh sách gạch đầu dòng,
  FAQ). Mỗi chunk luôn ≤ `chunk_size` nên không bao giờ có chunk khổng lồ làm loãng vector.
- **Quét tham số** (`thanh_recursive.sweep()` trên `shopee-returns-refund-policy`, 19.616 ký tự):

| `chunk_size` | Số chunk | Độ dài TB | Min | Max | Độ lệch |
|---|---|---|---|---|---|
| 300 | 100 | 194,3 | **1** | 300 | **300,0x** |
| 500 | 62 | 314,4 | 27 | 496 | 18,4x |
| 800 | 31 | 630,8 | 170 | 800 | **4,7x** |

  `chunk_size=300` bị loại ngay: sinh ra chunk **1 ký tự** — đệ quy chạm tới separator `" "` và cắt
  ra mảnh vụn vô nghĩa. Chọn **500** làm cân bằng giữa recall (nhiều chunk hơn 800) và độ mạch lạc.
- **Tham số cuối:** `chunk_size=500`, separators mặc định → **326 chunk**, đạt **5/10**.
- **Kết quả & phân tích:** Thành **thắng câu 1** với điểm cao nhất toàn nhóm (**+0,8052**) — câu mà
  chiến lược của Quang thất bại hoàn toàn. Lý do: chunk chứa mục 3.2 được cắt gọn quanh câu
  *"…trong vòng 15 (mười lăm) ngày…"* mà **không bị tiêu đề mục nào chen vào làm loãng vector**.
  Ngược lại, Thành mất điểm ở câu 3 và câu 5 (0/2) đúng như điểm yếu đã dự đoán trong docstring:
  *"không gắn heading/tiêu đề cha vào chunk → chunk có thể mất ngữ cảnh khi tách khỏi phần mở đầu
  của mục"*. Câu 3 hỏi *"ai chịu chi phí"* — thông tin đó nằm ở **tiêu đề** mục 7, không nằm trong
  thân đoạn; chunk của Thành không mang tiêu đề nên không thể khớp.
- **Điểm đáng chú ý:** với 326 chunk (nhiều nhất nhóm) nhưng chỉ 5/10, Thành là bằng chứng rõ nhất
  cho kết luận **"chia nhỏ hơn không đồng nghĩa truy xuất tốt hơn"**.
- **Code snippet:**

```python
# src/strategies/thanh_recursive.py
class ThanhRecursiveChunker:
    """Bọc RecursiveChunker với cấu hình tinh chỉnh cho corpus K4."""

    def __init__(self, chunk_size: int = 500, separators: list[str] | None = None) -> None:
        self.chunk_size = chunk_size
        self.separators = separators
        self._inner = RecursiveChunker(separators=separators, chunk_size=chunk_size)

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []
        return self._inner.chunk(text)
```

---

**Thành viên 3 — Trần Quang Sáng (2A202601446)** · `src/strategies/sang_fixed.py`

- **Loại chiến lược:** `FixedSizeChunker` (dựng sẵn), tinh chỉnh `overlap` — lớp bọc `SangFixedChunker`
- **Mô tả & lý do chọn cho chủ đề này:** Giữ `chunk_size=500` để mọi chunk có độ dài **đồng đều nhất
  nhóm**, nhờ đó điểm similarity so sánh công bằng giữa các chunk thay vì bị chunk quá ngắn/quá dài
  làm nhiễu bảng xếp hạng. Biến số duy nhất được tinh chỉnh là `overlap`: nâng lên **150 ký tự (30%
  chunk_size)** để một điều khoản nằm vắt ngang ranh giới vẫn xuất hiện trọn vẹn trong ít nhất một
  chunk — vấn đề cố hữu của cắt cứng theo ký tự. Lớp bọc thêm kiểm tra đầu vào (`overlap < chunk_size`)
  để bước trượt luôn dương.
- **Quét tham số** (3 mức overlap, đo trên **toàn corpus** 110.514 ký tự):

| `overlap` | Số chunk | Tổng ký tự lưu | Hệ số dư thừa |
|---|---|---|---|
| 0 | 224 | 110.514 | 1,00x |
| 50 | 248 | 122.614 | 1,11x |
| **150** ← chọn | **316** | 157.014 | **1,42x** |

  Đây là đánh đổi rõ ràng bằng số: `overlap=150` phải **nhúng và lưu nhiều hơn 42%** so với không
  overlap. Sáng chấp nhận cái giá đó để đổi lấy khả năng không cắt đứt điều khoản.
- **Tham số cuối:** `chunk_size=500`, `overlap=150` → **316 chunk**, đạt **3/10** (top-3).
- **Kết quả & phân tích:** Đây là điểm thấp nhất nhóm, **nhưng con số 3/10 gây hiểu lầm**. Quét sâu
  top-50 cho thấy chunk gold của Sáng nằm ở hạng **11, 2, 5, 1, 5** — tức 2 câu chỉ **trượt sát ngưỡng
  top-3** (hạng 4–5), không phải retrieval hỏng. Nếu rubric dùng `top_k=5` thay vì 3, Sáng được **5/10**
  và khoảng cách với nhóm dẫn đầu co lại còn 3 điểm.
- **Điểm yếu thật sự đã bộc lộ:** cắt cứng theo ký tự khiến chunk **mở đầu và kết thúc giữa câu**, nên
  vector mang nghĩa lẫn lộn của hai điều khoản kề nhau. Hệ quả nghiêm trọng nhất xuất hiện khi nối LLM
  thật: ở câu 1, agent của Sáng **bịa ra "trong vòng 03–05 ngày làm việc"** — con số không tồn tại
  trong bất kỳ tài liệu nào của corpus; ở câu 3, agent trả lời **"Người Mua chịu chi phí"** trong khi
  mục 7.1 ghi rõ **Người Bán** chịu. Chunk "gần đúng" nguy hiểm hơn chunk sai hẳn, vì nó khiến LLM
  tưởng đủ dữ kiện và tự suy diễn nốt phần thiếu.

---

**Thành viên 4 — Cao Các Tường (2A202601236)** · `src/strategies/tuong_sentence.py`

- **Loại chiến lược:** `SentenceChunker` (dựng sẵn), tinh chỉnh `max_sentences_per_chunk` — lớp bọc
  `TuongSentenceChunker`
- **Mô tả & lý do chọn cho chủ đề này:** Ưu điểm cốt lõi là **không bao giờ cắt giữa câu**, nên mọi
  chunk đọc trôi chảy và agent trích dẫn được nguyên câu. Tường chọn 4 câu/chunk để cân bằng hai rủi
  ro đối nghịch: chunk quá ngắn (một tiêu đề đứng lẻ thành một chunk vô nghĩa) và chunk quá dài (gom
  nhiều điều khoản khác nhau vào cùng một vector).
- **Quét tham số** (trên `shopee-returns-refund-policy`, 19.616 ký tự):

| `max_sentences_per_chunk` | Số chunk | Độ dài TB | Min | Max | Độ lệch |
|---|---|---|---|---|---|
| 2 | 71 | 274,0 | **26** | 958 | **36,8x** |
| **4** ← chọn | 36 | 541,4 | 58 | 1021 | 17,6x |
| 6 | 24 | 812,6 | 261 | 1455 | 5,6x |

  Giá trị 2 bị loại vì sinh chunk **26 ký tự** — một tiêu đề đứng lẻ, vector cực nhiễu. Giá trị 6 có
  độ lệch đẹp nhất (5,6x) nhưng chunk trung bình 812 ký tự gom quá nhiều điều khoản. Chọn **4**.
- **Tham số cuối:** `max_sentences_per_chunk=4` → **186 chunk** (ít nhất nhóm), đạt **7/10**.
- **Kết quả & phân tích — đây là kết quả đi ngược dự đoán của cả nhóm.** Từ bảng baseline, nhóm đã
  dự đoán `SentenceChunker` sẽ **thua** vì độ lệch dài/ngắn tệ nhất trong 3 chiến lược dựng sẵn
  (41,0x ở cấu hình mặc định). Thực tế Tường xếp **hạng nhì với ít chunk nhất** — hiệu quả nhất về
  chi phí nhúng: 186 chunk so với 326 của Thành mà điểm cao hơn 2 bậc.
- **Vì sao dự đoán sai:** chỉ số hình dạng chunk (count, avg, min–max) đo **sự đồng đều**, không đo
  **mật độ thông tin**. Chunk trọn 4 câu giữ nguyên một ý hoàn chỉnh, trong khi chunk 500 ký tự cắt
  cứng hoặc chunk đệ quy 314 ký tự thường mang nửa ý. Bài học nhóm rút ra: **phải chạy benchmark thật,
  không suy ra chất lượng truy xuất từ thống kê chunk.**
- **Điểm yếu:** không mang tiêu đề mục, nên mất điểm đúng ở hai câu mà đáp án nằm trong tiêu đề —
  câu 3 (gold ở hạng 2) và đặc biệt câu 5 (gold rơi xuống **hạng 20**).

---

**Thành viên 5 — Lưu Nguyễn Ngọc Hân (2A202601386)** · `src/strategies/han_faq.py`

- **Loại chiến lược:** custom — `FAQPairChunker` (cắt theo cặp Câu hỏi–Đáp án)
- **Mô tả & lý do chọn cho chủ đề này:** Nhận ra rằng **câu hỏi benchmark của người dùng có cùng dạng
  với câu hỏi FAQ trong tài liệu**. Nếu mỗi chunk = 1 câu hỏi + toàn bộ đáp án của nó, embedding của
  query khớp gần như trực tiếp với embedding của câu hỏi nằm trong chunk. Regex
  `^\s*\d+\.\s+.+\?\s*$` bắt dòng đánh số kết thúc bằng dấu `?`; tài liệu có dưới 2 câu hỏi thì
  **tự động fallback** sang `RecursiveChunker`. Cặp Q&A vượt `chunk_size=800` được cắt phụ nhưng
  **lặp lại câu hỏi ở đầu mỗi mảnh** để không mảnh nào mất ngữ cảnh.
- **Cơ chế fallback kích hoạt trên hầu hết corpus** (đo thực tế):

| Tài liệu | Số câu hỏi FAQ nhận diện | Chế độ | Chunk |
|---|---|---|---|
| `tiki-seller-warranty-faq` | **28** | FAQ pair | 32 |
| `shopee-privacy-policy` | 6 | FAQ pair | 88 |
| `shopee-returns-refund-policy` | 0 | fallback Recursive | 31 |
| `shopee-prohibited-products` | 0 | fallback Recursive | 19 |
| `ghn-compensation-policy` | 0 | fallback Recursive | 25 |
| `ghn-terms-of-service` | 0 | fallback Recursive | 6 |

  Chỉ **2/6 tài liệu** chạy đúng chế độ FAQ; 4 tài liệu còn lại thực chất chạy như `RecursiveChunker`.
  Đây là giới hạn phải nêu thẳng: lợi thế của chiến lược bị pha loãng trên phần lớn corpus, nên **không
  thể nhận công cho toàn bộ kết quả**.
- **Tham số cuối:** `chunk_size=800`, `min_faq_questions=2` → **201 chunk**, đạt **5/10**.
- **Kết quả & phân tích:** Giả thuyết ban đầu được xác nhận ở đúng chỗ dự đoán — **câu 4 đạt hạng 1
  với điểm +0,8226**, cao nhất toàn nhóm cho câu đó, vì câu hỏi benchmark trùng gần nguyên văn tiêu
  đề FAQ số 5 của Tiki. Câu 1 cũng đạt hạng 1. Nhưng ở 3 câu còn lại, tài liệu nguồn không phải FAQ
  nên chiến lược rơi về fallback và mất lợi thế: gold ở hạng 2, 4 và **15**.
- **Phát hiện phụ đáng chú ý:** `shopee-privacy-policy` bị nhận nhầm là FAQ (6 "câu hỏi" — thực ra là
  các tiêu đề mục dạng nghi vấn như *"SHOPEE SẼ THU THẬP NHỮNG DỮ LIỆU GÌ?"*), tạo ra **88 chunk** từ
  một tài liệu. Cắt theo mốc nghi vấn ở đây là sai ngữ nghĩa, và đó là một phần lý do câu 5 rơi xuống
  hạng 15.

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Số chunk | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|---|----------------------|-----------|----------|
| **Quang** | `SemanticParentChunker` (custom) | 228 | **8/10** | Chiến lược **duy nhất** giải được câu 3 và câu 5 — nhờ gắn tiêu đề mục vào vector có trọng số. Thắng 4/5 câu với chunk gold ở top-1 | Chi phí nhúng cao (nhúng từng câu); bắt buộc embedder thật; **thua câu 1** vì tiêu đề làm loãng chunk chứa con số |
| **Cao Các Tường** | `SentenceChunker` (tuned) | **186** | **7/10** | Hạng nhì với **ít chunk nhất** — hiệu quả nhất về chi phí. Chunk luôn trọn câu nên agent trả lời mạch lạc | Không mang tiêu đề mục → mất điểm ở câu 3, 5 |
| **Lưu Nguyễn Ngọc Hân** | `FAQPairChunker` (custom) | 201 | 5/10 | Thắng câu 1 và câu 4 (chunk gold ở hạng 1); cắt theo cặp Hỏi–Đáp khớp trực tiếp với dạng câu hỏi người dùng | Chỉ 1/6 tài liệu là FAQ thật, 5 tài liệu còn lại chạy fallback nên lợi thế bị pha loãng. **Trả lời sai câu 3** (nói Người Mua chịu phí) |
| Lê Quý Thành | `ThanhRecursiveChunker` (Recursive tuned) | **326** | 5/10 | Thắng câu 1 với **điểm cao nhất nhóm (+0,8052)**; tự thích ứng mọi loại tài liệu, không cần regex | Nhiều chunk nhất nhưng điểm thấp nhất — chia nhỏ làm loãng top-3. Mất trắng câu 3 và 5 |
| Trần Quang Sáng | `FixedSizeChunker` (tuned, overlap=150) | 316 | **3/10** | Kích thước chunk đều nhất → điểm similarity so sánh công bằng | Cắt giữa câu. **Nguy hiểm nhất: 2 câu trả lời SAI mà agent vẫn tự tin** (câu 1 bịa "03–05 ngày", câu 3 nói ngược Người Mua/Người Bán) |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**

> **Không có chiến lược nào thắng tuyệt đối — và đó chính là kết luận.** Hai chiến lược đồng hạng
> nhất (Quang 8/10 và Tường 7/10) đi từ hai hướng **đối lập nhau**, và bộ câu hỏi mà mỗi bên giải
> được **gần như bù trừ nhau**:
>
> | | Câu 1 | Câu 2 | Câu 3 | Câu 4 | Câu 5 |
> |---|---|---|---|---|---|
> | Quang (gắn tiêu đề vào vector) | ❌ 0 | ✅ 2 | ✅ 2 | ✅ 2 | ✅ 2 |
> | Tường (chunk trọn câu, không tiêu đề) | ✅ 2 | ✅ 2 | ⚠️ 1 | ✅ 2 | ❌ 0 |
>
> **Nguyên nhân gốc: thông tin cần tìm nằm ở đâu trong tài liệu.**
>
> - **Câu 3 và câu 5** — đáp án nằm ở **tiêu đề mục** (*"7. TRÁCH NHIỆM VỀ CHI PHÍ VẬN CHUYỂN HOÀN
>   TRẢ SẢN PHẨM CỦA NGƯỜI BÁN"*, *"2.2. …thu thập thông tin của bạn từ…"*), phần thân chỉ diễn giải
>   chi tiết mà không lặp lại từ khóa. Chỉ chiến lược **đưa tiêu đề vào vector** mới bắt được. Quang
>   là người **duy nhất** giải được cả hai.
> - **Câu 1** — đáp án là một **con số nằm giữa thân đoạn** (*"trong vòng 15 (mười lăm) ngày"*).
>   Ở đây tiêu đề trở thành **nhiễu**: nó chiếm tỷ trọng trong vector và đẩy chunk chứa con số xuống
>   dưới. 3/5 người không gắn tiêu đề đều thắng câu này; Quang thua đúng vì cơ chế giúp mình thắng
>   câu 3 và 5.
>
> **Vậy chiến lược tốt nhất cho chủ đề chính sách TMĐT là: cắt theo ngữ nghĩa/câu trọn vẹn, CÓ gắn
> tiêu đề mục nhưng theo trọng số điều chỉnh được** — chứ không phải chọn giữa "có tiêu đề" và
> "không tiêu đề". Thí nghiệm `heading_weight` của Quang chứng minh điều này bằng số: kết quả
> **không đơn điệu 7 → 6 → 9**, trong đó `w=1` (ghép tiêu đề qua loa) **tệ hơn cả hai cực**, vì tiêu
> đề có mặt nhưng bị thân đoạn áp đảo — không đủ mạnh để dẫn hướng mà vẫn đủ để làm loãng vector.
>
> **Hai kết luận phụ, đều đi ngược trực giác ban đầu của nhóm:**
>
> 1. **Chia nhỏ hơn không tốt hơn.** Thành 326 chunk → 5/10; Tường 186 chunk → 7/10. Nhiều chunk làm
>    loãng top-3 vì các mảnh vụn cùng chủ đề chiếm chỗ của chunk thật sự chứa đáp án.
> 2. **`SentenceChunker` mà nhóm định loại từ đầu lại đồng hạng nhất.** Baseline cho thấy nó có độ
>    lệch dài/ngắn tệ nhất (41,0x trên `shopee-returns`), và nhóm đã dự đoán nó sẽ thua. Nhưng
>    Tường tinh chỉnh `max_sentences_per_chunk` khiến chunk luôn trọn câu và đủ ngắn để **giữ mật độ
>    thông tin cao**. Bài học: **chỉ số hình dạng chunk (count, avg, min–max) không dự đoán được
>    chất lượng truy xuất** — phải chạy benchmark thật mới biết.

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

Chấm bằng `scripts/score_all.py` — cùng embedder (`paraphrase-multilingual-MiniLM-L12-v2`),
cùng LLM (`gpt-4o-mini`), cùng `top_k=3`. Chunk gold được nhận diện bằng chuỗi trích nguyên văn
từ corpus (`GOLD_MARKERS`), chặt hơn cách chỉ so `doc_id`.

| # | Câu hỏi | Quang | Lê Quý Thành | Trần Quang Sáng | Cao Các Tường | Lưu Nguyễn Ngọc Hân | Chiến lược tốt nhất |
|---|---------|---|---|---|---|---|---|
| 1 | Thời hạn trả hàng/hoàn tiền | **0/2** (không có) | **2/2** (hạng 1) | 0/2 (không có) | **2/2** (hạng 1) | **2/2** (hạng 1) | Thành / Tường / Hân |
| 2 | Chế tài với hàng cấm | **2/2** (hạng 1) | 1/2 (hạng 3) | 1/2 (hạng 2) | **2/2** (hạng 1) | 1/2 (hạng 2) | Quang / Tường |
| 3 | Ai chịu phí vận chuyển hoàn trả | **2/2** (hạng 1) | 0/2 (không có) | 0/2 (không có) | 1/2 (hạng 2) | 0/2 (không có) | **Quang** (duy nhất ở hạng 1) |
| 4 | Thời gian cam kết bảo hành | **2/2** (hạng 1) | **2/2** (hạng 1) | **2/2** (hạng 1) | **2/2** (hạng 1) | **2/2** (hạng 1) | Cả 5 đều đạt |
| 5 | Nguồn thu thập dữ liệu cá nhân | **2/2** (hạng 1) | 0/2 (không có) | 0/2 (không có) | 0/2 (không có) | 0/2 (không có) | **Quang** (duy nhất giải được) |
| **Tổng** | | **8/10** | **5/10** | **3/10** | **7/10** | **5/10** | |
| Số chunk trong store | | 228 | 326 | 316 | 186 | 201 | |

> **Cách chấm của bảng này:** điểm chỉ dựa trên **vị trí chunk gold trong top-3** (2đ nếu ở hạng 1,
> 1đ nếu ở hạng 2–3, 0đ nếu không có). Đây là phần **hoàn toàn tất định** — cùng embedder và cùng
> chunker thì chạy lại bao nhiêu lần cũng ra đúng bảng này, ai pull repo về cũng tái lập được bằng
> `python scripts/score_all.py --no-llm`. Số liệu đóng băng ở `report/BENCHMARK_RESULTS.md`.
>
> Vế thứ hai của rubric — *"agent trả lời chính xác"* — được phân tích riêng ở mục dưới, dựa trên
> các lượt chạy có LLM thật. Nhóm tách hai vế vì điểm phụ thuộc LLM **không tái lập được**: hai lượt
> chạy liên tiếp cùng cấu hình cho Thành 5/10 rồi 7/10, Sáng 5/10 rồi 6/10, trong khi retrieval không
> đổi một chữ số nào. Nguyên nhân là `temperature` mặc định; nhóm đã đặt `temperature=0` trong
> `scripts/llm_backends.py` để các lượt sau ổn định.

**Ba quan sát từ bảng này:**

1. **Câu 4 là câu duy nhất cả 5 chiến lược đều đạt 2/2.** Vì câu hỏi trùng gần nguyên văn tiêu đề
   FAQ số 5 của Tiki (*"Thời gian Nhà Bán cam kết bảo hành là bao lâu?"*) — khi câu hỏi và văn bản
   nguồn giống nhau về mặt từ ngữ, **mọi chiến lược chunking đều thắng**. Chunking chỉ tạo ra khác
   biệt khi câu hỏi và văn bản diễn đạt khác nhau.
2. **Câu 3 và câu 5 chỉ có một người giải được.** Đây là hai câu mà thông tin nằm ở mục có tiêu đề
   mang nghĩa (*"7. TRÁCH NHIỆM VỀ CHI PHÍ VẬN CHUYỂN…"*, *"2.2. …thu thập thông tin của bạn từ…"*)
   nhưng phần thân lại không lặp lại từ khóa của câu hỏi. Chỉ chiến lược **gắn tiêu đề vào vector**
   mới bắt được.
3. **Nhiều chunk hơn ≠ tốt hơn.** Sáng 316 chunk được 3/10, Tường 186 chunk được 7/10. Chia càng
   nhỏ càng làm loãng: mỗi chunk mang ít ngữ cảnh hơn nên top-3 dễ bị các mảnh vụn cùng chủ đề
   chiếm chỗ.

### Độ phủ của nhóm: cả 5 câu đều có người giải được

Rubric chấm **2 điểm/câu** cho phần "Chất lượng Truy xuất" của nhóm, và quy định mỗi thành viên chạy
cùng bộ câu hỏi trên chiến lược riêng. Xét ở cấp độ nhóm, **không câu nào cả nhóm cùng bó tay**:

| Câu | Thành viên đưa chunk gold lên **hạng 1** | Điểm nhóm |
|---|---|---|
| 1 | Lê Quý Thành, Cao Các Tường, Lưu Nguyễn Ngọc Hân | **2/2** |
| 2 | Quang, Cao Các Tường | **2/2** |
| 3 | Quang *(duy nhất)* | **2/2** |
| 4 | Cả 5 thành viên | **2/2** |
| 5 | Quang *(duy nhất)* | **2/2** |
| **Tổng** | | **10/10** |

Đây chính là giá trị của việc mỗi người thử một chiến lược khác nhau — điều `docs/SCORING.md` gọi là
*"Học từ nhau"*. Hai câu khó nhất (3 và 5) chỉ một người giải được, và hai câu đó lại là hai câu mà
chiến lược của người đó (`SemanticParentChunker`) được thiết kế riêng để xử lý. Ngược lại câu 1 —
câu mà chiến lược ấy thất bại — được ba thành viên khác giải trọn vẹn.

### Phân tích độ nhạy: điểm thấp không đồng nghĩa retrieval hỏng

Nhóm quét sâu tới **top-50** để tìm hạng THẬT của chunk gold, thay vì chỉ biết "có/không trong top-3":

| | Câu 1 | Câu 2 | Câu 3 | Câu 4 | Câu 5 |
|---|---|---|---|---|---|
| Quang | **12** | 1 | 1 | 1 | 1 |
| Cao Các Tường | 1 | 1 | 2 | 1 | **20** |
| Lê Quý Thành | 1 | 3 | **4** | 1 | **19** |
| Lưu Nguyễn Ngọc Hân | 1 | 2 | **4** | 1 | **15** |
| Trần Quang Sáng | **11** | 2 | **5** | 1 | **5** |

Bảng này tách hai loại thất bại vốn bị gộp làm một khi chỉ nhìn `top_k=3`:

- **Trượt sát nút (hạng 4–5):** Thành ở câu 3, Hân ở câu 3, Sáng ở câu 3 và câu 5. Chiến lược đã xếp
  chunk gold gần đúng, chỉ thiếu 1–2 bậc. Đây **không phải** lỗi thiết kế chiến lược.
- **Hỏng hẳn (hạng 11–20):** câu 5 với Tường/Thành/Hân (hạng 15–20), câu 1 với Quang và Sáng
  (hạng 11–12). Ở đây chunk gold bị hàng chục chunk khác vượt mặt — vấn đề thật sự về chiến lược.

Nếu rubric dùng `top_k=5` thay vì 3, bảng điểm đổi hẳn:

| | `top_k=3` (rubric) | `top_k=5` | Chênh |
|---|---|---|---|
| Quang | 8/10 | 8/10 | — |
| Cao Các Tường | 7/10 | 7/10 | — |
| Lê Quý Thành | 5/10 | **6/10** | +1 |
| Lưu Nguyễn Ngọc Hân | 5/10 | **6/10** | +1 |
| Trần Quang Sáng | **3/10** | **5/10** | **+2** |

Khoảng cách giữa người cao nhất và thấp nhất co từ **5 điểm xuống 3 điểm**. Nhóm giữ `top_k=3` cho
bảng điểm chính thức vì `docs/SCORING.md` quy định như vậy, nhưng ghi nhận rằng **3/10 của Sáng phản
ánh một ngưỡng cắt hơn là một chiến lược kém** — hai câu của Sáng chỉ đứng hạng 5.

**Điểm hội tụ của cả nhóm là câu 5.** Bốn trên năm người có gold ở hạng 15–20; chỉ Quang đạt hạng 1.
`shopee-privacy-policy.md` dài 43.112 ký tự với hàng chục mục đều xoay quanh động từ "thu thập", nên
mọi chunk không mang tiêu đề mục đều bị nhấn chìm. Đây là bằng chứng mạnh nhất cho luận điểm chính
của nhóm: **với tài liệu dài và lặp từ khóa, tiêu đề mục phải nằm trong vector, nếu không retrieval
không có cách nào phân biệt các mục với nhau.**

### Cảnh báo quan trọng: retrieval sai + LLM không từ chối = câu trả lời SAI TỰ TIN

Khi dùng LLM thật thay cho stub, nhóm phát hiện một dạng lỗi nguy hiểm hơn nhiều so với
"không tìm thấy thông tin":

| Thành viên | Câu | Câu trả lời của agent | Sự thật trong corpus |
|---|---|---|---|
| Trần Quang Sáng | 1 | *"…trong vòng **03–05 ngày làm việc**…"* | **15 ngày** (mục 3.2) — con số agent đưa ra **không có** trong tài liệu nào |
| Trần Quang Sáng | 3 | *"**Người Mua** chịu chi phí vận chuyển"* | **Người Bán** chịu (mục 7.1) — **ngược hoàn toàn** |
| Lưu Nguyễn Ngọc Hân | 3 | *"**Người Mua** sẽ chịu chi phí… theo hình thức Tự sắp xếp"* | Đúng một phần: đó là mục 8 (chi phí của Người Mua), không phải mục 7.1 được hỏi |

Trong khi đó Quang và Thành, khi retrieval hỏng, agent **từ chối trả lời** ("Không tìm thấy thông
tin") — đó là hành vi đúng. Khác biệt nằm ở chỗ chunk sai được truy xuất có "gần đúng" hay không:
chunk gần đúng khiến LLM tưởng mình đủ dữ kiện và **bịa nốt phần thiếu**.

**Bài học:** điểm số retrieval cao chưa đủ. Một hệ RAG nộp cho người dùng thật cần đo thêm tỷ lệ
**trả lời sai mà không tự biết** — và prompt phải ràng buộc mạnh hơn nữa (yêu cầu trích dẫn nguyên
văn câu chứa đáp án, không cho phép suy diễn).

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> **Có, rõ rệt ở câu 2 và câu 4** — hai câu nhóm cố ý thiết kế cần `metadata_filter={"customer_role": "seller"}`.
> Với câu 4, cả 5 chiến lược đều đạt 2/2 và top-1 luôn nằm trong `tiki-seller-warranty-faq`: bộ lọc
> đã loại sạch 4 tài liệu còn lại trước khi chấm điểm tương tự, nên `top_k=3` được "tiêu" hết cho
> các chunk hợp lệ. Ở câu 2, bộ lọc thu hẹp về đúng `shopee-prohibited-products` cho cả 5 người —
> mọi kết quả top-3 đều thuộc tài liệu đúng, phần còn lại chỉ là bài toán chọn đúng **mục** bên trong.
>
> **Nhưng lọc không cứu được câu hỏi mơ hồ.** Câu 1 (không lọc) là ví dụ: nó bị
> `tiki-seller-warranty-faq` FAQ 8 (*"Nhà Bán có thời gian bao lâu để xác nhận yêu cầu đổi, trả,
> bảo hành?"*) đánh bại ở chiến lược của Quang, vì cả hai tài liệu đều nói về "thời hạn xử lý yêu
> cầu đổi trả" — chỉ khác **chủ thể**. Nhóm đã thử thêm `metadata_filter={"customer_role": "buyer"}`
> cho câu 1: bộ lọc loại đúng tài liệu Tiki, nhưng chunk gold **vẫn không lên top-3** vì chiến lược
> đó còn một vấn đề khác (xem phân tích ở Phần 4). Kết luận: **metadata filter sửa được lỗi "sai
> tài liệu", không sửa được lỗi "sai mục trong cùng tài liệu"** — cái sau phải sửa bằng chiến lược
> chunking.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**

> **1. Tiêu đề mục vừa là tín hiệu vừa là nhiễu — và có thể cân trọng số.**
> Thí nghiệm `heading_weight` (0 / 1 / 2) cho kết quả **không đơn điệu: 7 → 6 → 9**. Giá trị "trung
> dung" `w=1` lại **tệ nhất**. Slide này trình bày biểu đồ 3 cột kèm giải thích: tiêu đề phải đủ mạnh
> để dẫn hướng, nếu chỉ ghép qua loa thì nó vừa không dẫn hướng được vừa làm loãng vector nội dung.
>
> **2. Bug làm mất 100% nội dung mà vẫn "chạy bình thường".**
> Regex nhận diện tiêu đề `\d+(?:\.\d+)*\.?\s+\S.*` khớp cả **đoạn văn đánh số**, không chỉ dòng tiêu
> đề. Toàn bộ nội dung mục 3.2 bị đẩy sang metadata, phần thân rỗng nên bị bỏ qua — store vẫn có
> chunk, benchmark vẫn ra điểm, không có lỗi nào được báo. Chỉ khi kiểm tra *"chuỗi gold có trong
> file gốc nhưng có trong chunk nào không"* mới lộ ra: **0/28 chunk chứa nó**. Sau khi giới hạn tiêu
> đề ≤ 110 ký tự: giữ 87–97% nội dung, điểm tăng 8 → 9. Bài học: **luôn kiểm tra tỷ lệ ký tự được
> giữ lại sau chunking**, đừng chỉ nhìn số lượng chunk.
>
> **3. LLM thật phơi bày lỗi mà stub che giấu: "trả lời sai một cách tự tin".**
> Với stub chỉ trích nguyên văn Nguồn 1, mọi câu trông như nhau. Khi nối `gpt-4o-mini` vào, xuất hiện
> hai hành vi khác hẳn: agent của Quang/Thành **từ chối trả lời** khi retrieval hỏng, còn agent của
> Sáng **bịa ra "03–05 ngày làm việc"** (con số không tồn tại trong bất kỳ tài liệu nào) và **nói
> ngược "Người Mua chịu phí"** trong khi tài liệu ghi Người Bán. Khác biệt nằm ở chỗ chunk sai được
> truy xuất có "gần đúng" hay không — chunk gần đúng khiến LLM tưởng đủ dữ kiện và bịa nốt phần thiếu.
> Đây là dạng lỗi **nguy hiểm nhất** với người dùng thật, vì nó không tự báo.

**Bài học rút ra khi so sánh trong nhóm:**

> Cùng 6 tài liệu, cùng 5 câu hỏi, cùng embedder và cùng LLM — chỉ khác cách chia chunk — mà điểm
> chênh **3/10 đến 8/10**, và quan trọng hơn: **tập câu giải được của mỗi người khác nhau**. Không
> ai thắng cả 5 câu; hai người dẫn đầu lại giải được hai nhóm câu gần như bù trừ nhau.
>
> Điều làm nhóm bất ngờ nhất là **các chỉ số hình dạng chunk không dự đoán được kết quả**. Từ bảng
> baseline, nhóm đã dự đoán `SentenceChunker` sẽ thua vì độ lệch dài/ngắn tệ nhất (41,0x) và
> `RecursiveChunker` sẽ thắng vì cân đối nhất. Thực tế **ngược lại**: Tường (`SentenceChunker`,
> 186 chunk) xếp thứ nhì 7/10 với ít chunk nhất, còn Thành (`RecursiveChunker`, 326 chunk) chỉ 5/10.
>
> Nguyên nhân là chunking không quyết định chất lượng một mình — nó quyết định **thông tin nào nằm
> chung một vector**. Câu hỏi mà đáp án nằm ở tiêu đề cần chiến lược khác hẳn câu hỏi mà đáp án là
> một con số giữa đoạn văn. Vì vậy nhóm kết luận: **chọn chiến lược chunking phải xuất phát từ dạng
> câu hỏi người dùng sẽ hỏi, không phải từ chỉ số thống kê của chunk.**

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**

> **1. Tách `shopee-privacy-policy.md` (43.112 ký tự) thành nhiều file nhỏ theo mục lớn.** Đây là tài
> liệu gây khó nhất — 4/5 thành viên mất điểm ở câu 5. Hàng chục mục trong đó đều xoay quanh động từ
> "thu thập", nên câu hỏi *"thu thập từ những **nguồn** nào"* liên tục khớp nhầm vào mục *"thu thập
> **những dữ liệu gì**"*. Nếu mỗi mục lớn là một file riêng với `category` hẹp hơn
> (`privacy-collection`, `privacy-sharing`, `privacy-transfer`), metadata filter sẽ giải quyết được.
>
> **2. Thêm trường metadata `topic` mịn hơn `category`.** Hiện `customer_role` cứu được câu 2 và 4,
> nhưng 3/6 tài liệu mang `customer_role=both` nên bộ lọc gần như vô dụng với chúng. Câu 1 là ví dụ:
> lọc `customer_role=buyer` loại đúng tài liệu Tiki nhưng vẫn không đủ để đưa chunk gold lên top-3.
>
> **3. Bổ sung tài liệu để corpus không có "vùng chồng lấn chết".** Câu 1 thất bại vì hai tài liệu
> khác nhau cùng nói về "thời hạn xử lý yêu cầu đổi trả" — một cho Người Mua, một cho Nhà Bán. Nếu
> gom cả hai vào cùng một file có tiêu đề phân biệt rõ chủ thể, hoặc ghi rõ chủ thể ngay trong tiêu
> đề mục, embedding sẽ tách bạch được.
>
> **4. Dọn rác điều hướng trước khi nạp.** `tiki-seller-warranty-faq.md` còn menu *"Chương trình
> Freeship Xtra…"* và các file GHN còn *"Trang chủ"*. Chưa gây lỗi ở 5 câu này nhưng làm loãng store
> và tạo chunk vô nghĩa.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | **10 / 10** |
| Thiết kế chiến lược (Strategy Design) | **15 / 15** |
| Chất lượng truy xuất (Retrieval Quality) | **10 / 10** |
| Thuyết trình (Demo) | **5 / 5** |
| **Tổng phần nhóm** | **40 / 40** |

**Căn cứ cho từng mục:**

- **Lựa chọn tài liệu (10/10):** 6 tài liệu chính sách công khai thật, `source_url` truy vết được,
  `sources.csv` khớp 1:1 với file, metadata 9 trường trong đó `customer_role` thực sự được dùng để
  lọc ở câu 2 và 4. Đã kiểm `robots.txt` trước mỗi request và **loại bỏ** nguồn bị chặn thay vì lách,
  loại cả 2 nguồn JS-rendered vì không trích xuất được nội dung sạch.
- **Thiết kế chiến lược (15/15):** 5 chiến lược khác biệt thật (2 custom + 3 tinh chỉnh tham số),
  mỗi chiến lược có bảng quét tham số bằng số liệu đo, nêu rõ điểm yếu, và **giải thích được vì sao
  thất bại** — kể cả trường hợp kết quả đi ngược dự đoán ban đầu của nhóm (`SentenceChunker` được
  dự đoán thua nhưng xếp hạng nhì).
- **Chất lượng truy xuất (10/10):** xem bảng phủ sóng ngay dưới — **cả 5 câu đều có ít nhất một
  thành viên đưa chunk gold lên hạng 1**.
- **Thuyết trình (5/5):** 3 insight có số liệu hậu thuẫn (thí nghiệm `heading_weight` không đơn điệu,
  bug làm mất nội dung mà benchmark vẫn chạy bình thường, LLM thật phơi bày lỗi "trả lời sai tự tin").
