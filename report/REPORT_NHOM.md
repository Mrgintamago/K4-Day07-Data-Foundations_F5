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
  → **170 chunk**, đạt **8/10**.
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
| Điểm | 7/10 | **6/10** | **8/10** ← chọn |

  Kết quả **không đơn điệu (7 → 6 → 8)**. Giải thích: tiêu đề mục **vừa là nhiễu vừa là tín hiệu**.
  Câu hỏi 3 ("ai chịu chi phí vận chuyển") được trả lời bởi chính tiêu đề *"7. TRÁCH NHIỆM VỀ CHI PHÍ
  VẬN CHUYỂN HOÀN TRẢ SẢN PHẨM CỦA NGƯỜI BÁN"*; bỏ tiêu đề đi thì mất tín hiệu. Nhưng `w=1` lại **tệ
  hơn cả hai cực** vì tiêu đề có mặt mà bị phần thân dài áp đảo — không đủ mạnh để dẫn hướng nhưng
  vẫn đủ để làm loãng vector nội dung.

---

**Thành viên 2 — Lê Quý Thành (2A202601168)** · `src/strategies/thanh_recursive.py`

- **Loại chiến lược:** `RecursiveChunker` (dựng sẵn), tinh chỉnh `chunk_size`
- **Mô tả & lý do chọn:** *(Thành điền — nêu rõ đã quét những giá trị `chunk_size` nào, chọn giá trị
  nào và vì sao, dựa trên kết quả 5 câu benchmark chứ không phải phỏng đoán)*
- **Tham số cuối / số chunk / điểm:** *(chờ)*

---

**Thành viên 3 — Trần Quang Sáng (2A202601446)** · `src/strategies/sang_fixed.py`

- **Loại chiến lược:** `FixedSizeChunker` (dựng sẵn), tinh chỉnh `overlap`
- **Mô tả & lý do chọn:** *(Sáng điền — điểm ăn tiền: tìm một câu hỏi mà `overlap=0` fail nhưng
  `overlap=150` pass, dán top-3 của cả hai lần chạy)*
- **Tham số cuối / số chunk / điểm:** *(chờ)*

---

**Thành viên 4 — Cao Các Tường (2A202601236)** · `src/strategies/tuong_sentence.py`

- **Loại chiến lược:** `SentenceChunker` (dựng sẵn), tinh chỉnh `max_sentences_per_chunk`
- **Mô tả & lý do chọn:** *(Tường điền — nhiệm vụ đặc biệt: chứng minh bằng số liệu vì sao chiến lược
  này KHÔNG hợp văn bản chính sách; in ra chunk ngắn nhất và dài nhất làm bằng chứng cho độ lệch 41x)*
- **Tham số cuối / số chunk / điểm:** *(chờ)*

---

**Thành viên 5 — Lưu Nguyễn Ngọc Hân (2A202601386)** · `src/strategies/han_faq.py`

- **Loại chiến lược:** custom — `FAQPairChunker` (cắt theo cặp Câu hỏi–Đáp án)
- **Mô tả & lý do chọn:** *(Hân điền — kỳ vọng thắng áp đảo câu 4 vì câu hỏi trùng gần nguyên văn
  FAQ số 5 của Tiki; nhớ nêu rõ cơ chế fallback cho 5/6 tài liệu không phải dạng FAQ)*
- **Tham số cuối / số chunk / điểm:** *(chờ)*

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Số chunk | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|---|----------------------|-----------|----------|
| Quang | `SemanticParentChunker` (custom) | 170 | **8/10** | Ranh giới chunk bám theo ý nghĩa; điều khiển được trọng số tiêu đề — thắng câu 2, 3, 4 với chunk gold ở top-1 | Chi phí nhúng cao (nhúng từng câu); bắt buộc embedder thật; fail câu 1 và 5 |
| Lê Quý Thành | `RecursiveChunker` (tuned) | *(chờ)* | *(chờ)* | | |
| Trần Quang Sáng | `FixedSizeChunker` (tuned) | *(chờ)* | *(chờ)* | | |
| Cao Các Tường | `SentenceChunker` (tuned) | *(chờ)* | *(chờ)* | | |
| Lưu Nguyễn Ngọc Hân | `FAQPairChunker` (custom) | *(chờ)* | *(chờ)* | | |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> *(hoàn thiện sau khi đủ 5 kết quả — khung lập luận nhóm đã thống nhất:)*
>
> Baseline cho thấy **không chiến lược nào thắng trên mọi tài liệu**: `RecursiveChunker` tốt nhất trên
> tài liệu dạng danh sách (`shopee-prohibited-products`, độ lệch 1,6x) nhưng vụn nhất trên tài liệu
> điều khoản dài (`shopee-returns`, 62 chunk / độ lệch 18,4x). Vì vậy câu hỏi đúng không phải "chiến
> lược nào tốt nhất" mà là **"chiến lược nào hợp với loại cấu trúc nào"**.
>
> Phát hiện có giá trị nhất tính đến hiện tại là kết quả **không đơn điệu 7 → 6 → 8** của tham số
> `heading_weight`: tiêu đề mục trong văn bản chính sách không nên bị bỏ đi cũng không nên chỉ ghép
> qua loa — nó cần được **cân trọng số như một tham số riêng**. Đây là điều chỉ lộ ra khi tách phần
> đem-đi-nhúng khỏi phần trả-về, thứ mà cả ba chiến lược dựng sẵn không cho phép làm.
>
> *(Bổ sung sau khi có kết quả của Thành/Sáng/Tường/Hân: chiến lược nào giải được câu 1 và câu 5 —
> hai câu hiện chưa ai giải được — sẽ là luận điểm mạnh nhất của phần so sánh.)*

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
