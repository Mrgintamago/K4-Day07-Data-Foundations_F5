"""Chiến lược của Sáng: fixed-size chunking với overlap được tinh chỉnh.

Chiến lược giữ ``chunk_size=500`` để các chunk có độ dài tương đối đồng đều
và tăng ``overlap`` lên 150 ký tự (30% kích thước chunk). Phần chồng lấp lớn
hơn giúp giữ lại ngữ cảnh của câu hoặc điều khoản nằm đúng tại ranh giới giữa
hai chunk, đổi lại sẽ tạo nhiều chunk và tốn thêm chi phí embedding.

Các mức overlap dùng trong thí nghiệm: 0, 50 và 150 ký tự.
"""
from __future__ import annotations

from ..chunking import FixedSizeChunker


DEFAULT_CHUNK_SIZE = 500
DEFAULT_OVERLAP = 150
OVERLAP_CANDIDATES = (0, 50, 150)


class SangFixedChunker:
    """Bọc ``FixedSizeChunker`` với cấu hình overlap của Sáng.

    Args:
        chunk_size: Số ký tự tối đa trong mỗi chunk.
        overlap: Số ký tự được lặp lại giữa hai chunk liên tiếp. Giá trị này
            phải nhỏ hơn ``chunk_size`` để bước trượt luôn dương.
    """

    def __init__(
        self,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        overlap: int = DEFAULT_OVERLAP,
    ) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size phải lớn hơn 0")
        if overlap < 0:
            raise ValueError("overlap không được âm")
        if overlap >= chunk_size:
            raise ValueError("overlap phải nhỏ hơn chunk_size")

        self.chunk_size = chunk_size
        self.overlap = overlap
        self._chunker = FixedSizeChunker(
            chunk_size=self.chunk_size,
            overlap=self.overlap,
        )

    def chunk(self, text: str) -> list[str]:
        """Chia văn bản bằng ``FixedSizeChunker`` đã có sẵn."""
        return self._chunker.chunk(text)


def build_chunker() -> SangFixedChunker:
    """Trả về cấu hình Sáng chọn để chạy benchmark: 500/150."""
    return SangFixedChunker(
        chunk_size=DEFAULT_CHUNK_SIZE,
        overlap=DEFAULT_OVERLAP,
    )


__all__ = [
    "SangFixedChunker",
    "build_chunker",
    "DEFAULT_CHUNK_SIZE",
    "DEFAULT_OVERLAP",
    "OVERLAP_CANDIDATES",
]
