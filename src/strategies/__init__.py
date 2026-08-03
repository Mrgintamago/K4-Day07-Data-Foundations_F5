"""
Chiến lược chunking riêng của từng thành viên nhóm F5 (Giai đoạn 2).

Gói `src` (chunking.py / store.py / agent.py) là phần CHUNG — đã hoàn thành 15 TODO
và pass 42/42 test, không ai được sửa. Mỗi thành viên tự thêm MỘT file trong thư mục
này, chứa chiến lược chia chunk của riêng mình.

Quy ước đặt tên: `<ten>_<chien_luoc>.py`, mỗi file export một lớp có đúng một phương
thức `chunk(text: str) -> list[str]` để truyền thẳng vào
`ingest.build_knowledge_base(..., chunker=...)`, kèm hàm `build_chunker()` trả về cấu
hình đã chọn.

Phân công (xem KE_HOACH_NHOM.md để biết lý do thiết kế và checklist từng người):

    quang_heading.py    — HeadingChunker    (Quang)                    ✅ đã có
    thanh_recursive.py  — RecursiveChunker  (Lê Quý Thành)             ⬜ tự làm
    sang_fixed.py       — FixedSizeChunker  (Trần Quang Sáng)          ⬜ tự làm
    tuong_sentence.py   — SentenceChunker   (Cao Các Tường)            ⬜ tự làm
    han_faq.py          — FAQPairChunker    (Lưu Nguyễn Ngọc Hân)      ⬜ tự làm
"""

from .quang_heading import HeadingChunker

__all__ = ["HeadingChunker"]
