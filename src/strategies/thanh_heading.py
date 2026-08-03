"""
Chiến lược của Thành — `ThanhRecursiveChunker`: bọc `RecursiveChunker` với cấu hình
được tinh chỉnh cho corpus pháp lý / chính sách thương mại điện tử.

LÝ DO THIẾT KẾ
--------------
`RecursiveChunker` (đã có sẵn trong `src/chunking.py`) cắt đệ quy theo thứ tự ưu tiên
các dấu phân cách:  ``["\\n\\n", "\\n", ". ", " ", ""]``.

Ưu điểm:
- Tự thích ứng với mọi loại tài liệu — không phụ thuộc vào cấu trúc heading.
- Mỗi chunk luôn ≤ `chunk_size` ký tự, giữ nguyên ranh giới câu/đoạn khi có thể.
- Với `chunk_size=500` (mặc định) và corpus ~6 tài liệu, mỗi chunk vừa đủ chứa
  1–2 đoạn ngữ nghĩa → phù hợp cho embedding-based retrieval.

Điểm yếu (phải nêu trong báo cáo):
- Không gắn heading/tiêu đề cha vào chunk → chunk có thể mất ngữ cảnh khi
  tách khỏi phần mở đầu của mục.
- Với các mục đánh số dày đặc (ví dụ danh mục hàng cấm), ranh giới chunk
  có thể rơi vào giữa một mục con → giảm chất lượng truy xuất cho câu hỏi
  cần toàn bộ mục con.

Cấu hình đã chọn:
- `chunk_size = 500`  — cân bằng giữa ngữ cảnh đủ dài và recall cao.
- `separators`        — giữ mặc định (đoạn → dòng → câu → từ → ký tự).
"""
from __future__ import annotations

from ..chunking import RecursiveChunker


class ThanhRecursiveChunker:
    """Bọc `RecursiveChunker` với cấu hình tinh chỉnh cho corpus K4.

    Interface:
        chunker.chunk(text: str) -> list[str]

    Có thể truyền thẳng vào `ingest.build_knowledge_base(..., chunker=...)`.
    """

    def __init__(
        self,
        chunk_size: int = 500,
        separators: list[str] | None = None,
    ) -> None:
        self.chunk_size = chunk_size
        self.separators = separators
        self._inner = RecursiveChunker(
            separators=separators,
            chunk_size=chunk_size,
        )

    def chunk(self, text: str) -> list[str]:
        """Chia `text` thành các chunk ≤ `chunk_size` ký tự."""
        if not text or not text.strip():
            return []
        return self._inner.chunk(text)


def build_chunker() -> ThanhRecursiveChunker:
    """Cấu hình Thành dùng để chạy benchmark."""
    return ThanhRecursiveChunker(chunk_size=500)
