"""
Chấm điểm truy xuất cho MỌI thành viên đã nộp chiến lược, xuất bảng so sánh cho REPORT_NHOM.

Cách chấm bám đúng `docs/SCORING.md` (2 điểm/câu):
    2đ — chunk gold ở TOP-1 và agent trả lời chính xác
    1đ — chunk gold có trong top-3 nhưng không ở top-1, hoặc agent trả lời thiếu
    0đ — top-3 không có chunk gold (agent không thể trả lời đúng)

"Chunk gold" được nhận diện bằng chuỗi trích nguyên văn từ corpus (`GOLD_MARKERS`),
chặt hơn cách chỉ so `doc_id` — vì đúng tài liệu mà sai mục thì agent vẫn trả lời sai.
Script gọi LLM thật (nếu `.env` có API key) để kiểm chứng vế "agent trả lời chính xác",
thay vì suy đoán từ điểm similarity.

Chạy:
    export PYTHONIOENCODING=utf-8
    python scripts/score_all.py                 # tất cả thành viên đã nộp
    python scripts/score_all.py --members quang thanh
"""
from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from llm_backends import safe_llm, select_llm  # noqa: E402
from run_benchmark import (  # noqa: E402
    DATA_DIR,
    GOLD_MARKERS,
    MEMBER_MODULES,
    QUERIES,
    build_store_for,
    select_embedder,
)

from src.agent import KnowledgeBaseAgent  # noqa: E402

DISPLAY_NAMES = {
    "quang": "Quang",
    "thanh": "Lê Quý Thành",
    "sang": "Trần Quang Sáng",
    "tuong": "Cao Các Tường",
    "han": "Lưu Nguyễn Ngọc Hân",
}

STRATEGY_NAMES = {
    "quang": "SemanticParentChunker (custom)",
    "thanh": "ThanhRecursiveChunker (Recursive tuned)",
    "sang": "FixedSizeChunker (tuned)",
    "tuong": "SentenceChunker (tuned)",
    "han": "FAQPairChunker (custom)",
}

# Câu trả lời bị coi là "không trả lời được" nếu chứa một trong các cụm này.
REFUSAL_MARKERS = ("không tìm thấy", "không có thông tin", "không biết", "không rõ ràng")


def available_members() -> list[str]:
    """Những thành viên đã thực sự nộp file chiến lược."""
    found = []
    for member, module_path in MEMBER_MODULES.items():
        try:
            importlib.import_module(module_path)
            found.append(member)
        except ModuleNotFoundError:
            continue
    return found


LLM_ERROR_PREFIX = "[LỖI GỌI LLM"


def retrieval_only_llm(prompt: str) -> str:
    """Chế độ --no-llm: không gọi API, chỉ đánh dấu rằng vế 'agent trả lời' bị bỏ qua."""
    return "(bỏ qua — chế độ chỉ chấm truy xuất)"


def score_member(member: str, embedder, llm_fn, top_k: int = 3, use_llm: bool = True) -> dict:
    module = importlib.import_module(MEMBER_MODULES[member])
    store = build_store_for(member, module, embedder)
    agent = KnowledgeBaseAgent(store=store, llm_fn=llm_fn)

    rows, total = [], 0
    for index, ((query, _gold, expected_doc, metadata_filter), marker) in enumerate(
        zip(QUERIES, GOLD_MARKERS), start=1
    ):
        if metadata_filter:
            results = store.search_with_filter(query, top_k=top_k, metadata_filter=metadata_filter)
        else:
            results = store.search(query, top_k=top_k)

        gold_rank = next((r for r, res in enumerate(results, 1) if marker in res["content"]), None)
        doc_hit = expected_doc in [r["metadata"].get("doc_id") for r in results]

        answer = agent.answer(query, top_k=top_k)
        llm_failed = answer.startswith(LLM_ERROR_PREFIX)
        # Không có câu trả lời thật (lỗi API hoặc chế độ --no-llm) thì KHÔNG được phép
        # coi là "agent trả lời sai" — chỉ chấm phần truy xuất.
        graded_on_answer = use_llm and not llm_failed
        refused = graded_on_answer and any(m in answer.lower() for m in REFUSAL_MARKERS)

        if not graded_on_answer:
            points = 2 if gold_rank == 1 else (1 if gold_rank is not None else 0)
        elif gold_rank == 1 and not refused:
            points = 2
        elif gold_rank is not None and not refused:
            points = 1
        elif gold_rank is not None or (doc_hit and not refused):
            points = 1
        else:
            points = 0

        total += points
        rows.append(
            {
                "index": index,
                "gold_rank": gold_rank,
                "doc_hit": doc_hit,
                "refused": refused,
            "llm_failed": llm_failed,
            "graded_on_answer": graded_on_answer,
                "points": points,
                "top1_doc": results[0]["metadata"].get("doc_id") if results else "-",
                "top1_score": results[0]["score"] if results else 0.0,
                "answer": answer.replace("\n", " ")[:150],
            }
        )
    return {"member": member, "size": store.get_collection_size(), "total": total, "rows": rows}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--members", nargs="*", default=None)
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument(
        "--save",
        nargs="?",
        const="report/BENCHMARK_RESULTS.md",
        default=None,
        metavar="ĐƯỜNG_DẪN",
        help="Ghi kết quả ra file Markdown để đóng băng số liệu (mặc định: report/BENCHMARK_RESULTS.md)",
    )
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Chỉ chấm phần TRUY XUẤT (tất định, không tốn quota API). Bỏ qua vế 'agent trả lời đúng'.",
    )
    args = parser.parse_args()

    members = args.members or available_members()
    missing = [m for m in MEMBER_MODULES if m not in members]

    embedder = select_embedder()
    if args.no_llm:
        llm_fn, llm_name = retrieval_only_llm, "KHÔNG DÙNG (--no-llm, chỉ chấm truy xuất)"
    else:
        raw_llm, llm_name = select_llm()
        llm_fn = safe_llm(raw_llm)
    print(f"Backend nhúng: {getattr(embedder, '_backend_name', type(embedder).__name__)}")
    print(f"Backend LLM  : {llm_name}")
    print(f"Chấm cho     : {', '.join(members)}")
    if missing:
        print(f"Chưa nộp     : {', '.join(missing)}")

    reports = []
    for member in members:
        print(f"\n===== {DISPLAY_NAMES.get(member, member)} =====")
        report = score_member(member, embedder, llm_fn, top_k=args.top_k, use_llm=not args.no_llm)
        reports.append(report)
        for row in report["rows"]:
            rank = row["gold_rank"] or "-"
            note = " [agent từ chối trả lời]" if row["refused"] else ""
            print(
                f"  Câu {row['index']}: gold_rank={rank}  top1={row['top1_doc']} "
                f"({row['top1_score']:+.4f})  -> {row['points']}/2{note}"
            )
            print(f"       {row['answer']}")
        print(f"  TỔNG: {report['total']}/10   ({report['size']} chunk)")

    print("\n\n===== BẢNG DÁN VÀO REPORT_NHOM PHẦN 3 =====\n")
    header = "| # | Câu hỏi | " + " | ".join(DISPLAY_NAMES.get(r["member"], r["member"]) for r in reports)
    print(header + " | Chiến lược tốt nhất cho câu này |")
    print("|---|---------|" + "|".join(["---"] * (len(reports) + 1)) + "|")
    for i in range(len(QUERIES)):
        cells = []
        best, best_points = "-", -1
        for report in reports:
            row = report["rows"][i]
            rank = f"hạng {row['gold_rank']}" if row["gold_rank"] else "không có"
            cells.append(f"{row['points']}/2 ({rank})")
            if row["points"] > best_points:
                best_points, best = row["points"], DISPLAY_NAMES.get(report["member"], report["member"])
        if best_points == 0:
            best = "**chưa ai giải được**"
        print(f"| {i + 1} | {QUERIES[i][0][:60]}… | " + " | ".join(cells) + f" | {best} |")
    totals = " | ".join(f"**{r['total']}/10**" for r in reports)
    sizes = " | ".join(f"{r['size']}" for r in reports)
    print(f"| **Tổng** | | {totals} | |")
    print(f"| Số chunk | | {sizes} | |")

    if args.save:
        path = write_results_file(args.save, reports, embedder, llm_name, args.top_k)
        print(f"\nĐã ghi kết quả vào {path}")
    return 0


def write_results_file(
    path_str: str, reports: list[dict], embedder, llm_name: str, top_k: int, no_llm: bool = False
) -> Path:
    """Đóng băng kết quả benchmark ra file Markdown để không phải chạy lại.

    Retrieval là tất định (cùng embedder + chunker -> cùng gold_rank, cùng score), nhưng
    câu trả lời của LLM thì không, và ai không có API key sẽ rơi về stub. File này giữ lại
    số liệu của một lần chạy có đầy đủ cấu hình để cả nhóm trích dẫn chung.
    """
    from datetime import date

    backend = getattr(embedder, "_backend_name", type(embedder).__name__)
    lines: list[str] = [
        "# Kết quả Benchmark — Nhóm F5 (số liệu đóng băng)",
        "",
        "> File này do `scripts/score_all.py --save` sinh ra. **Không sửa tay.**",
        "> Chạy lại bằng: `python scripts/score_all.py --save`",
        "",
        f"- **Ngày chạy:** {date.today().isoformat()}",
        f"- **Backend nhúng:** `{backend}`",
        f"- **Backend LLM:** `{llm_name}`",
        f"- **top_k:** {top_k}",
        f"- **Corpus:** `{DATA_DIR}` (6 tài liệu)",
        "",
        "Retrieval là **tất định**: cùng embedder và cùng chunker luôn cho cùng `gold_rank` và cùng",
        "điểm similarity — chạy lại bao nhiêu lần cũng ra đúng bảng này.",
        "",
        (
            "> **Chế độ chỉ chấm TRUY XUẤT** (`--no-llm`): điểm dưới đây chỉ phản ánh chunk gold có ở "
            "top-1/top-3 hay không. Vế *'agent trả lời chính xác'* của rubric CHƯA được kiểm chứng — "
            "cần chạy lại có LLM khi hạn mức API hồi phục."
            if no_llm
            else "Câu trả lời của agent do LLM sinh; script chạy `temperature=0` để tái lập được."
        ),
        "",
        "## Bảng tổng hợp",
        "",
        "| # | Câu hỏi | " + " | ".join(DISPLAY_NAMES.get(r["member"], r["member"]) for r in reports) + " |",
        "|---|---------|" + "|".join(["---"] * len(reports)) + "|",
    ]
    for i in range(len(QUERIES)):
        cells = []
        for report in reports:
            row = report["rows"][i]
            rank = f"hạng {row['gold_rank']}" if row["gold_rank"] else "không có"
            cells.append(f"{row['points']}/2 ({rank})")
        lines.append(f"| {i + 1} | {QUERIES[i][0]} | " + " | ".join(cells) + " |")
    lines.append("| **Tổng** | | " + " | ".join(f"**{r['total']}/10**" for r in reports) + " |")
    lines.append("| Số chunk | | " + " | ".join(str(r["size"]) for r in reports) + " |")

    lines += ["", "## Chi tiết từng thành viên", ""]
    for report in reports:
        name = DISPLAY_NAMES.get(report["member"], report["member"])
        strategy = STRATEGY_NAMES.get(report["member"], "-")
        lines += [
            f"### {name} — `{strategy}`",
            "",
            f"Store: **{report['size']} chunk** · Tổng điểm: **{report['total']}/10**",
            "",
            "| Câu | gold_rank | top-1 doc_id | score | Điểm | Câu trả lời của agent |",
            "|---|---|---|---|---|---|",
        ]
        for row in report["rows"]:
            rank = row["gold_rank"] or "—"
            answer = row["answer"].replace("|", "/")
            note = " ⚠️ *từ chối trả lời*" if row["refused"] else ""
            lines.append(
                f"| {row['index']} | {rank} | `{row['top1_doc']}` | {row['top1_score']:+.4f} | "
                f"**{row['points']}/2** | {answer}…{note} |"
            )
        lines.append("")

    path = Path(path_str)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


if __name__ == "__main__":
    raise SystemExit(main())
