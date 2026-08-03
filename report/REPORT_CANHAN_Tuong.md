# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Cao Các Tường  
**MSSV:** 2A202601236  
**Nhóm:** K4 Lab 7  
**Ngày:** 2026-08-03

> Nộp 1 bản / sinh viên. Phần nhóm được nộp chung trong [report/REPORT_NHOM.md](report/REPORT_NHOM.md).

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity)
**Độ tương tự cosine cao nghĩa là gì?**  
Hai vector nhúng (embedding) chỉ về cùng một hướng trong không gian ngữ nghĩa. Nếu hai đoạn văn bản nói về cùng một ý, cosine gần $1$. Nếu không liên quan, cosine gần $0$ hoặc âm.

**Ví dụ có độ tương tự CAO:**
- Câu A: “Tôi muốn trả lại đơn hàng vì sản phẩm bị lỗi.”
- Câu B: “Làm sao để hoàn trả hàng hóa không đúng mô tả?”
- Vì cả hai cùng về ý định đổi trả hàng của người mua.

**Ví dụ có độ tương tự THẤP:**
- Câu A: “Phí vận chuyển được tính theo khối lượng và khoảng cách.”
- Câu B: “Chính sách bảo mật quy định cách sàn xử lý dữ liệu cá nhân.”
- Vì hai chủ đề này hoàn toàn khác nhau.

**Tại sao cosine được ưu tiên hơn khoảng cách Euclid?**  
Cosine đo hướng, không bị ảnh hưởng nhiều bởi độ dài đoạn văn. Với chunking, điều này rất quan trọng vì một chunk dài và một chunk ngắn vẫn có thể cùng ý nghĩa.

### Bài toán tính toán Chunking
**Tài liệu 10,000 ký tự, chunk_size = 500, overlap = 50. Bao nhiêu chunks?**  
- Step = `500 - 50 = 450`
- Số chunk = `ceil((10000 - 50)/450) = ceil(22.11) = 23`
- **Đáp án: 23 chunks**

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

### Chiến lược `SentenceChunker`
Tôi chọn chiến lược `SentenceChunker` để giữ ranh giới câu và tránh cắt giữa câu. Điều này giúp chunk đọc trôi chảy hơn, phù hợp với các tài liệu có cấu trúc câu rõ ràng.

File triển khai nằm ở [src/strategies/tuong_sentence.py](src/strategies/tuong_sentence.py). Cấu trúc chính như sau:

```python
class TuongSentenceChunker:
    def __init__(self, max_sentences_per_chunk: int = 4) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)
        self._chunker = SentenceChunker(
            max_sentences_per_chunk=self.max_sentences_per_chunk
        )

    def chunk(self, text: str) -> list[str]:
        return self._chunker.chunk(text)


def build_chunker() -> TuongSentenceChunker:
    return TuongSentenceChunker(max_sentences_per_chunk=4)
```

### Điểm mạnh / điểm yếu
- **Điểm mạnh:** giữ được tính mạch lạc ngôn ngữ, không cắt giữa câu.
- **Điểm yếu:** không hiểu heading/điều khoản, nên chunk có thể quá ngắn hoặc quá dài trên văn bản pháp lý.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Tôi đã chạy kiểm thử toàn bộ repo:

```bash
python -m pytest tests/ -v
```

Kết quả:

```text
============================= 42 passed in 0.21s ==============================
```

### Ghi chú môi trường
Do `LocalEmbedder` chưa sẵn sàng trong môi trường hiện tại (thiếu `sentence_transformers`), phần benchmark dùng **mock embedding fallback**. Vì vậy các kết quả similarity và retrieval dưới đây là kết quả thực tế đã chạy trên mock embedding.

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
