"""
Chien luoc cua Cao Cac Tuong - `TuongSentenceChunker`.

LY DO THIET KE
--------------
Chien luoc nay dung `SentenceChunker` co san va tinh chinh tham so
`max_sentences_per_chunk`. Diem manh cua cach cat theo cau la khong cat giua cau,
vi vay moi chunk doc tu nhien hon so voi cat cung theo ky tu.

Voi van ban chinh sach TMDT, toi chon cau hinh mac dinh 4 cau/chunk de can bang
giua hai muc tieu:

- Chunk khong qua ngan, tranh truong hop tieu de ngan dung rieng mot minh.
- Chunk khong qua dai, tranh gom qua nhieu dieu khoan khac nhau vao cung mot vector.

DIEM YEU CAN NEU TRONG BAO CAO
-----------------------------
Sentence-based chunking khong hieu cau truc dieu/khoan. Mot tieu de ngan nhu
"1.2. Pham Vi Ap Dung" co the thanh chunk rat ngan, trong khi mot cau/danh sach
dai co the tao chunk rat lon. Do dai chunk lech manh lam embedding de nhieu,
dac biet voi tai lieu phap ly nhieu heading, bullet va dieu khoan.
"""
from __future__ import annotations

from ..chunking import SentenceChunker


class TuongSentenceChunker:
    """Cat van ban theo nhom cau voi so cau moi chunk co the tinh chinh.

    Args:
        max_sentences_per_chunk: so cau toi da trong moi chunk. Gia tri nen thu
            trong benchmark: 2, 4, 6. Cau hinh mac dinh cua toi la 4.
    """

    def __init__(self, max_sentences_per_chunk: int = 4) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)
        self._chunker = SentenceChunker(
            max_sentences_per_chunk=self.max_sentences_per_chunk
        )

    def chunk(self, text: str) -> list[str]:
        return self._chunker.chunk(text)


def build_chunker() -> TuongSentenceChunker:
    """Cau hinh Cao Cac Tuong dung de chay benchmark."""
    return TuongSentenceChunker(max_sentences_per_chunk=4)
