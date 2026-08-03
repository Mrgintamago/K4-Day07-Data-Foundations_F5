"""
Chiến lược chunking riêng của từng thành viên nhóm F5 (Giai đoạn 2).

Gói `src` (chunking.py / store.py / agent.py) là phần CHUNG — đã hoàn thành 15 TODO
và pass 42/42 test, không ai được sửa. Mỗi thành viên có MỘT file trong thư mục này,
chứa chiến lược chia chunk của riêng mình.

Quy ước: mỗi file export một lớp có phương thức `chunk(text: str) -> list[str]`,
kèm hàm `build_chunker()` trả về cấu hình đã chọn.

Phân công (xem KE_HOACH_NHOM.md để biết lý do thiết kế và checklist từng người):

    quang_semantic.py   — SemanticParentChunker (Quang)                 ✅
    thanh_recursive.py  — ThanhRecursiveChunker (Lê Quý Thành)          ✅
    sang_fixed.py       — FixedSizeChunker      (Trần Quang Sáng)       ✅
    tuong_sentence.py   — SentenceChunker       (Cao Các Tường)         ✅
    han_faq.py          — FAQPairChunker        (Lưu Nguyễn Ngọc Hân)   ✅

Chạy benchmark cho một người:  python scripts/run_benchmark.py --member <ten>
Chấm điểm cả nhóm:             python scripts/score_all.py
"""

from .quang_semantic import SemanticParentChunker
from .thanh_recursive import ThanhRecursiveChunker

__all__ = ["SemanticParentChunker", "ThanhRecursiveChunker"]
