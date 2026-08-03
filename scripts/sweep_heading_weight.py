"""
Quét tham số `heading_weight` của SemanticParentChunker trên 5 câu benchmark của nhóm.

Giả thuyết cần kiểm chứng: tiêu đề mục cha VỪA là nhiễu VỪA là tín hiệu, tùy câu hỏi.
    heading_weight=0  -> bỏ tiêu đề khỏi vector (chỉ giữ trong metadata)
    heading_weight=1  -> ghép tiêu đề một lần vào đầu chunk
    heading_weight=2  -> lặp tiêu đề hai lần, tăng trọng số tín hiệu tiêu đề

Chạy:
    export PYTHONIOENCODING=utf-8
    python scripts/sweep_heading_weight.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from run_benchmark import DATA_DIR, QUERIES, select_embedder  # noqa: E402

from src.strategies import quang_semantic  # noqa: E402

WEIGHTS = [0, 1, 2]

# Chuỗi nhận diện chunk gold cho từng câu — dùng để chấm "top-1 có ĐÚNG MỤC không",
# chặt hơn tiêu chí "đúng doc_id".
GOLD_MARKERS = [
    "15 (mười lăm) ngày",
    "(i) Sản phẩm bị xóa",
    "Người Bán sẽ chịu chi phí vận chuyển",
    "tối đa không quá 30 ngày",
    "cơ quan đánh giá tín dụng",
]


def score_run(store, top_k: int = 3) -> tuple[int, list[dict]]:
    """Chấm 5 câu theo rubric docs/SCORING.md (2 điểm/câu)."""
    total = 0
    rows: list[dict] = []

    for index, ((query, _gold, expected_doc, metadata_filter), marker) in enumerate(
        zip(QUERIES, GOLD_MARKERS), start=1
    ):
        if metadata_filter:
            results = store.search_with_filter(query, top_k=top_k, metadata_filter=metadata_filter)
        else:
            results = store.search(query, top_k=top_k)

        gold_rank = None
        for rank, result in enumerate(results, start=1):
            if marker in result["content"]:
                gold_rank = rank
                break

        doc_hit = expected_doc in [r["metadata"].get("doc_id") for r in results]

        if gold_rank == 1:
            points = 2          # chunk gold ở top-1 -> agent trả lời đúng
        elif gold_rank is not None:
            points = 1          # gold có trong top-3 nhưng không ở top-1
        elif doc_hit:
            points = 1          # đúng tài liệu nhưng sai mục
        else:
            points = 0

        total += points
        rows.append(
            {
                "index": index,
                "gold_rank": gold_rank,
                "doc_hit": doc_hit,
                "points": points,
                "top1_score": results[0]["score"] if results else 0.0,
                "top1_doc": results[0]["metadata"].get("doc_id") if results else "-",
            }
        )
    return total, rows


def main() -> int:
    embedder = select_embedder()
    backend = getattr(embedder, "_backend_name", embedder.__class__.__name__)
    print(f"Backend nhúng: {backend}")
    if backend == "mock embeddings fallback":
        print("DỪNG: sweep này vô nghĩa với mock. Đặt EMBEDDING_PROVIDER=local trong .env.")
        return 1

    summary: dict[int, tuple[int, list[dict], int]] = {}

    for weight in WEIGHTS:
        print(f"\n===== heading_weight = {weight} =====")
        store = quang_semantic.build_store(DATA_DIR, embedding_fn=embedder, heading_weight=weight)
        size = store.get_collection_size()
        total, rows = score_run(store)
        summary[weight] = (total, rows, size)

        for row in rows:
            rank = row["gold_rank"] or "-"
            print(
                f"  Câu {row['index']}: gold_rank={rank}  doc_hit={'Y' if row['doc_hit'] else 'N'}  "
                f"top1={row['top1_doc']} ({row['top1_score']:+.4f})  -> {row['points']}/2"
            )
        print(f"  TỔNG: {total}/10   ({size} chunk)")

    print("\n\n===== BẢNG SO SÁNH (dán vào báo cáo) =====\n")
    print("| Câu | heading_weight=0 | heading_weight=1 | heading_weight=2 |")
    print("|-----|------------------|------------------|------------------|")
    for i in range(len(QUERIES)):
        cells = []
        for weight in WEIGHTS:
            row = summary[weight][1][i]
            rank = f"hạng {row['gold_rank']}" if row["gold_rank"] else "không có"
            cells.append(f"{row['points']}/2 ({rank})")
        print(f"| {i + 1} | {cells[0]} | {cells[1]} | {cells[2]} |")

    totals = " | ".join(f"**{summary[w][0]}/10**" for w in WEIGHTS)
    sizes = " | ".join(f"{summary[w][2]} chunk" for w in WEIGHTS)
    print(f"| **Tổng** | {totals} |")
    print(f"| Số chunk | {sizes} |")

    best = max(WEIGHTS, key=lambda w: summary[w][0])
    print(f"\nCấu hình tốt nhất: heading_weight={best} ({summary[best][0]}/10)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
