"""
Chiến lược `FAQPairChunker`: cắt theo cặp Câu hỏi–Đáp án.

LÝ DO THIẾT KẾ
--------------
File `tiki-seller-warranty-faq.md` có cấu trúc FAQ đánh số rõ ràng, ví dụ:

    5. Thời gian Nhà Bán cam kết bảo hành là bao lâu?

    Nhà Bán cam kết thời gian bảo hành (tối đa không quá 30 ngày)...

Mỗi chunk = 1 câu hỏi + toàn bộ câu trả lời của nó. Khi người dùng hỏi câu tương tự,
embedding của query khớp thẳng vào embedding của câu hỏi trong chunk → recall cao hơn.

Kỳ vọng: thắng áp đảo câu benchmark số 4 ("Thời gian Nhà Bán cam kết bảo hành tối đa
là bao lâu?") vì trùng gần nguyên văn FAQ số 5 trong tài liệu. `K4_VARIANT.md` chấp nhận
FAQ pair là chiến lược điều/khoản hợp lệ.

"""
from __future__ import annotations

import re

from ..chunking import RecursiveChunker

# Bắt câu hỏi đánh số: "1. ...", "11. ...", phải kết thúc bằng dấu "?"
# Cho phép khoảng trắng/tab đầu dòng.
QUESTION_RE = re.compile(r"^\s*\d+\.\s+.+\?\s*$", re.MULTILINE)

# Ngưỡng tối thiểu để nhận dạng tài liệu có cấu trúc FAQ.
MIN_FAQ_QUESTIONS = 2


class FAQPairChunker:
    """Cắt theo cặp Câu hỏi–Đáp án; tài liệu không có FAQ thì fallback RecursiveChunker.

    Args:
        chunk_size: kích thước trần cho mỗi chunk. Cặp Q&A dài hơn ngưỡng này
            sẽ được cắt phụ bằng RecursiveChunker, mỗi mảnh gắn lại câu hỏi
            gốc ở đầu.
        min_faq_questions: số câu hỏi tối thiểu để xác định tài liệu là FAQ.
            Nếu ít hơn thì tự động fallback.
    """

    def __init__(
        self,
        chunk_size: int = 800,
        min_faq_questions: int = MIN_FAQ_QUESTIONS,
    ) -> None:
        self.chunk_size = chunk_size
        self.min_faq_questions = min_faq_questions
        self._fallback = RecursiveChunker(chunk_size=chunk_size)

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        # Tìm tất cả vị trí câu hỏi FAQ trong văn bản.
        matches = list(QUESTION_RE.finditer(text))

        if len(matches) < self.min_faq_questions:
            # Không đủ dấu hiệu FAQ → fallback về chiến lược tổng quát.
            return self._fallback.chunk(text)

        positions = [m.start() for m in matches]
        chunks: list[str] = []

        # ── Preamble (phần trước câu hỏi đầu tiên) ──
        preamble = text[: positions[0]].strip()
        if preamble:
            if len(preamble) <= self.chunk_size:
                chunks.append(preamble)
            else:
                chunks.extend(self._fallback.chunk(preamble))

        # ── Từng cặp Q&A ──
        for i, pos in enumerate(positions):
            # Lát cắt: từ câu hỏi hiện tại đến câu hỏi kế tiếp (hoặc hết văn bản).
            end = positions[i + 1] if i + 1 < len(positions) else len(text)
            qa_pair = text[pos:end].strip()
            if not qa_pair:
                continue

            if len(qa_pair) <= self.chunk_size:
                chunks.append(qa_pair)
            else:
                # Q&A quá dài → cắt phụ, giữ câu hỏi làm header cho mỗi mảnh.
                question_line = matches[i].group(0).strip()
                answer_body = text[matches[i].end() : end].strip()

                if len(answer_body) == 0:
                    # Chỉ có câu hỏi, không có đáp án.
                    chunks.append(question_line)
                    continue

                sub_chunks = self._fallback.chunk(answer_body)
                for sub in sub_chunks:
                    piece = f"{question_line}\n\n{sub}".strip()
                    chunks.append(piece)

        return [c for c in chunks if c]


def build_chunker() -> FAQPairChunker:
    """Cấu hình dùng để chạy benchmark."""
    return FAQPairChunker(chunk_size=800, min_faq_questions=2)
