"""
Chiến lược của Quang — `HeadingChunker`: cắt theo điều/khoản và tiêu đề.

LÝ DO THIẾT KẾ
--------------
Cả 6 tài liệu trong `data/k4_ecommerce/` đều là văn bản pháp lý/chính sách đã được
đánh số sẵn theo cấp bậc:

    1. ĐỐI TƯỢNG VÀ PHẠM VI ÁP DỤNG
    1.1. Đối Tượng Áp Dụng
    3.2. Người Mua có thể gửi yêu cầu trả hàng/hoàn tiền trong vòng 15 (mười lăm) ngày...
    I. THUẬT NGỮ

Mỗi mục đánh số là một đơn vị ngữ nghĩa TRỌN VẸN — đúng thứ mà retrieval cần trả về.
Chiến lược này cắt tại ranh giới mục, và **dán tiêu đề mục cha vào đầu mỗi chunk** để
chunk tự mang ngữ cảnh (một chunk lẻ "trong vòng 15 ngày..." vô nghĩa nếu tách khỏi
tiêu đề "3. ĐIỀU KIỆN YÊU CẦU TRẢ HÀNG/HOÀN TIỀN").

Kỳ vọng: thắng các câu hỏi 1, 2, 3 của bộ benchmark vì gold answer nằm gọn trong đúng
một mục đánh số.

ĐIỂM YẾU (phải nêu trong báo cáo)
---------------------------------
- Phụ thuộc hoàn toàn vào chất lượng cấu trúc tài liệu. Tài liệu không đánh số/không có
  heading thì regex không bắt được → fallback về `RecursiveChunker`.
- Một mục có thể rất dài (mục 4 của `shopee-prohibited-products` liệt kê 20 danh mục con)
  → phải cắt phụ, và mỗi mảnh cắt phụ đều được gắn lại tiêu đề để không mất ngữ cảnh.
"""
from __future__ import annotations

import re

from ..chunking import RecursiveChunker

# Bắt 3 dạng tiêu đề xuất hiện trong corpus:
#   "# Tiêu đề" / "## Tiêu đề"      (Markdown)
#   "1." / "1.2." / "4.10."          (điều khoản đánh số nhiều cấp)
#   "I." / "II." / "IV."             (đánh số La Mã)
HEADING_RE = re.compile(
    r"^(?:"
    r"#{1,6}\s+\S.*"           # Markdown heading
    r"|\d+(?:\.\d+)*\.?\s+\S.*"  # 1.  /  1.2.  /  4.10.
    r"|[IVX]+\.\s+\S.*"          # I.  /  II.
    r")$",
    re.MULTILINE,
)


class HeadingChunker:
    """Cắt văn bản theo tiêu đề/điều khoản, giữ tiêu đề ở đầu mỗi chunk.

    Args:
        max_chunk_size: mục dài hơn ngưỡng này sẽ được cắt phụ bằng RecursiveChunker.
        min_chunk_size: mục ngắn hơn ngưỡng này (thường là tiêu đề đứng một mình)
            sẽ được gộp vào mục kế tiếp thay vì tạo thành chunk rời rạc.
    """

    def __init__(self, max_chunk_size: int = 700, min_chunk_size: int = 80) -> None:
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        self._fallback = RecursiveChunker(chunk_size=max_chunk_size)

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        sections = self._split_by_heading(text)
        if len(sections) < 2:
            # Không nhận ra cấu trúc tiêu đề -> dùng chiến lược tổng quát.
            return self._fallback.chunk(text)

        sections = self._merge_tiny_sections(sections)

        chunks: list[str] = []
        for heading, body in sections:
            section_text = f"{heading}\n{body}".strip() if heading else body.strip()
            if not section_text:
                continue
            if len(section_text) <= self.max_chunk_size:
                chunks.append(section_text)
                continue
            # Mục quá dài: cắt phụ nhưng gắn lại tiêu đề vào TỪNG mảnh.
            for piece in self._fallback.chunk(body.strip()):
                chunks.append(f"{heading}\n{piece}".strip() if heading else piece.strip())
        return [c for c in chunks if c]

    def _split_by_heading(self, text: str) -> list[tuple[str, str]]:
        """Trả về danh sách (tiêu_đề, nội_dung). Phần trước tiêu đề đầu tiên có tiêu đề rỗng."""
        matches = list(HEADING_RE.finditer(text))
        if not matches:
            return [("", text)]

        sections: list[tuple[str, str]] = []
        preamble = text[: matches[0].start()].strip()
        if preamble:
            sections.append(("", preamble))

        for index, match in enumerate(matches):
            heading = match.group(0).strip()
            body_start = match.end()
            body_end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            sections.append((heading, text[body_start:body_end].strip()))
        return sections

    def _merge_tiny_sections(self, sections: list[tuple[str, str]]) -> list[tuple[str, str]]:
        """Gộp mục quá ngắn (tiêu đề đứng một mình) vào mục ngay sau nó."""
        merged: list[tuple[str, str]] = []
        carry_heading = ""
        carry_body = ""

        for heading, body in sections:
            combined_len = len(heading) + len(body)
            if combined_len < self.min_chunk_size:
                # Giữ lại, dồn sang mục kế tiếp.
                carry_heading = carry_heading or heading
                carry_body = f"{carry_body}\n{heading}\n{body}".strip()
                continue
            if carry_body:
                merged.append((carry_heading, f"{carry_body}\n{heading}\n{body}".strip()))
                carry_heading, carry_body = "", ""
            else:
                merged.append((heading, body))

        if carry_body:
            if merged:
                last_heading, last_body = merged[-1]
                merged[-1] = (last_heading, f"{last_body}\n{carry_body}".strip())
            else:
                merged.append((carry_heading, carry_body))
        return merged


def build_chunker() -> HeadingChunker:
    """Cấu hình Quang dùng để chạy benchmark."""
    return HeadingChunker(max_chunk_size=700, min_chunk_size=80)
