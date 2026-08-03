"""
Chạy 5 câu hỏi benchmark của nhóm F5 trên chiến lược chunking của một thành viên.

Bộ 5 câu hỏi + gold answer được chốt trong KE_HOACH_NHOM.md — cả 5 thành viên chạy
CÙNG bộ này, chỉ khác chiến lược chia chunk.

Chạy:
    export PYTHONIOENCODING=utf-8
    EMBEDDING_PROVIDER=local python scripts/run_benchmark.py --member quang

Tham số:
    --member    tên module chiến lược trong src/strategies (mặc định: quang)
    --top-k     số kết quả lấy ra mỗi câu (mặc định: 3)
    --markdown  in thêm bảng Markdown dán thẳng vào REPORT_CANHAN_<Ten>.md
    --overlap   chạy một mức overlap 0/50/150 cho thành viên Sáng
    --sweep-overlap  chạy đủ ba mức overlap của Sáng trong một lệnh
"""
from __future__ import annotations

import argparse
import importlib
import inspect
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv  # noqa: E402
from llm_backends import safe_llm, select_llm  # noqa: E402

from ingest import build_knowledge_base  # noqa: E402
from src.agent import KnowledgeBaseAgent  # noqa: E402
from src.embeddings import (  # noqa: E402
    EMBEDDING_PROVIDER_ENV,
    LOCAL_EMBEDDING_MODEL,
    OPENAI_EMBEDDING_MODEL,
    LocalEmbedder,
    OpenAIEmbedder,
    _mock_embed,
)

DATA_DIR = "data/k4_ecommerce"

# Map tên thành viên -> module chiến lược trong src/strategies.
MEMBER_MODULES = {
    "quang": "src.strategies.quang_semantic",
    "thanh": "src.strategies.thanh_recursive",
    "sang": "src.strategies.sang_fixed",
    "tuong": "src.strategies.tuong_sentence",
    "han": "src.strategies.han_faq",
}

# 5 câu hỏi benchmark chung — KHÔNG sửa nếu chưa họp nhóm.
# (câu hỏi, gold answer rút gọn, doc_id kỳ vọng, metadata_filter)
QUERIES: list[tuple[str, str, str, dict | None]] = [
    (
        "Người mua có bao nhiêu ngày để gửi yêu cầu trả hàng hoàn tiền sau khi đơn hàng giao thành công?",
        "15 ngày kể từ khi giao hàng thành công; thực phẩm tươi sống và đông lạnh là 24 giờ.",
        "shopee-returns-refund-policy",
        None,
    ),
    (
        "Người bán bị áp dụng những chế tài nào nếu đăng bán sản phẩm thuộc danh mục cấm?",
        "Xóa sản phẩm; giới hạn quyền tài khoản; đình chỉ hoặc xóa tài khoản; cấn trừ số dư và "
        "phong tỏa quyền rút tiền; chế tài khác theo pháp luật.",
        "shopee-prohibited-products",
        {"customer_role": "seller"},
    ),
    (
        "Ai chịu chi phí vận chuyển chiều hoàn trả sản phẩm?",
        "Người Bán chịu, trong 3 trường hợp: Shopee chấp thuận yêu cầu không do lỗi Người Mua "
        "hoặc đơn vị vận chuyển; đơn giao không thành công; ngoại lệ khác theo quyết định của Shopee.",
        "shopee-returns-refund-policy",
        None,
    ),
    (
        "Thời gian Nhà Bán cam kết bảo hành tối đa là bao lâu?",
        "Tối đa không quá 30 ngày, tính từ khi Nhà Bán nhận hàng đến khi bảo hành xong, "
        "không tính thời gian vận chuyển.",
        "tiki-seller-warranty-faq",
        {"customer_role": "seller"},
    ),
    (
        "Shopee thu thập dữ liệu cá nhân của người dùng từ những nguồn nào?",
        "Từ chính bạn, các công ty liên kết, bên thứ ba: đối tác vận chuyển và thanh toán, "
        "cơ quan đánh giá tín dụng, đối tác marketing, người dùng khác, nguồn công khai hoặc của nhà nước.",
        "shopee-privacy-policy",
        None,
    ),
]


# Chuỗi nhận diện chunk gold cho từng câu — dùng để chấm "chunk gold có ở top-k không",
# chặt hơn tiêu chí "đúng doc_id". Trích nguyên văn từ corpus (verify bằng grep).
GOLD_MARKERS = [
    "15 (mười lăm) ngày",
    "(i) Sản phẩm bị xóa",
    "Người Bán sẽ chịu chi phí vận chuyển",
    "tối đa không quá 30 ngày",
    "cơ quan đánh giá tín dụng",
]


def select_embedder():
    """Chọn backend nhúng theo EMBEDDING_PROVIDER (giống main.py)."""
    load_dotenv(override=False)
    provider = os.getenv(EMBEDDING_PROVIDER_ENV, "mock").strip().lower()
    if provider == "local":
        try:
            return LocalEmbedder(model_name=os.getenv("LOCAL_EMBEDDING_MODEL", LOCAL_EMBEDDING_MODEL))
        except Exception:
            print("Local embedder không sẵn sàng; tạm dùng mock.")
    elif provider == "openai":
        try:
            return OpenAIEmbedder(model_name=os.getenv("OPENAI_EMBEDDING_MODEL", OPENAI_EMBEDDING_MODEL))
        except Exception:
            print("OpenAI embedder không sẵn sàng; tạm dùng mock.")
    return _mock_embed


def build_store_for(member: str, module, embedder):
    """Nạp store theo chiến lược của thành viên.

    Chiến lược của Quang dùng cơ chế parent-context nên có pipeline nạp riêng
    (`build_store`); các chiến lược còn lại dùng `ingest.build_knowledge_base()` chuẩn.
    """
    if hasattr(module, "build_store"):
        return module.build_store(DATA_DIR, embedding_fn=embedder)

    # Chỉ truyền embedder cho chunker nào KHAI BÁO tham số `embedding_fn`
    # (chiến lược cắt theo ngữ nghĩa cần nó). Đếm số tham số là không đủ:
    # một chunker có tham số `chunk_size` cũng có argcount > 0.
    params = inspect.signature(module.build_chunker).parameters
    chunker = module.build_chunker(embedding_fn=embedder) if "embedding_fn" in params else module.build_chunker()
    return build_knowledge_base(DATA_DIR, embedding_fn=embedder, chunker=chunker)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--member", default="quang", choices=sorted(MEMBER_MODULES))
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--markdown", action="store_true")
    parser.add_argument(
        "--overlap",
        type=int,
        metavar="N",
        help="overlap của chiến lược Sáng; chọn một trong 0, 50, 150",
    )
    parser.add_argument(
        "--sweep-overlap",
        action="store_true",
        help="chạy lần lượt cả ba cấu hình overlap 0, 50, 150 của Sáng",
    )
    args = parser.parse_args()

    module = importlib.import_module(MEMBER_MODULES[args.member])

    if args.member != "sang" and (args.overlap is not None or args.sweep_overlap):
        parser.error("--overlap và --sweep-overlap chỉ dùng với --member sang")
    if args.overlap is not None and args.sweep_overlap:
        parser.error("chỉ chọn một trong --overlap hoặc --sweep-overlap")

    if args.member == "sang":
        overlap_candidates = tuple(module.OVERLAP_CANDIDATES)
        if args.overlap is not None and args.overlap not in overlap_candidates:
            parser.error(f"--overlap phải là một trong {overlap_candidates}")

        if args.sweep_overlap:
            for overlap in overlap_candidates:
                print("\n" + "=" * 78, flush=True)
                print(
                    f"CHẠY CẤU HÌNH SÁNG: chunk_size={module.DEFAULT_CHUNK_SIZE}, overlap={overlap}",
                    flush=True,
                )
                print("=" * 78 + "\n", flush=True)
                command = [
                    sys.executable,
                    str(Path(__file__).resolve()),
                    "--member",
                    "sang",
                    "--top-k",
                    str(args.top_k),
                    "--overlap",
                    str(overlap),
                ]
                if args.markdown:
                    command.append("--markdown")
                subprocess.run(command, check=True)
            return 0

        if args.overlap is not None:
            module.DEFAULT_OVERLAP = args.overlap
        print(
            f"Cấu hình chunking: chunk_size={module.DEFAULT_CHUNK_SIZE}, "
            f"overlap={module.DEFAULT_OVERLAP}"
        )

    embedder = select_embedder()
    backend = getattr(embedder, "_backend_name", embedder.__class__.__name__)
    print(f"Thành viên: {args.member}   Module: {MEMBER_MODULES[args.member]}")
    print(f"Backend nhúng: {backend}")
    if backend == "mock embeddings fallback":
        print("CẢNH BÁO: mock KHÔNG phản ánh ngữ nghĩa. Đặt EMBEDDING_PROVIDER=local rồi chạy lại.\n")

    llm_fn, llm_name = select_llm()
    print(f"Backend LLM: {llm_name}")

    store = build_store_for(args.member, module, embedder)
    print(f"Đã nạp {store.get_collection_size()} chunk từ {DATA_DIR}\n")

    agent = KnowledgeBaseAgent(store=store, llm_fn=safe_llm(llm_fn))
    rows = []
    hits = 0

    for index, (query, gold, expected_doc, metadata_filter) in enumerate(QUERIES, start=1):
        if metadata_filter:
            results = store.search_with_filter(query, top_k=args.top_k, metadata_filter=metadata_filter)
            filter_note = f"  [metadata_filter={metadata_filter}]"
        else:
            results = store.search(query, top_k=args.top_k)
            filter_note = ""

        top_docs = [r["metadata"].get("doc_id") for r in results]
        relevant = expected_doc in top_docs
        hits += relevant

        print(f"--- Câu {index}{filter_note}")
        print(f"Q: {query}")
        print(f"Gold: {gold}")
        print(f"Kỳ vọng doc_id: {expected_doc}   -> top-{args.top_k} có chứa: {'CÓ' if relevant else 'KHÔNG'}")
        for rank, result in enumerate(results, start=1):
            preview = result["content"][:110].replace("\n", " ")
            parent = result["metadata"].get("parent_heading")
            print(f"  {rank}. score={result['score']:+.4f}  doc_id={result['metadata'].get('doc_id')}")
            if parent:
                print(f"     [mục cha] {parent[:90]}")
            print(f"     {preview}...")
        answer = agent.answer(query, top_k=args.top_k)
        print(f"Agent: {answer[:200]}...\n")

        rows.append(
            {
                "index": index,
                "query": query,
                "top1_doc": top_docs[0] if top_docs else "-",
                "top1_preview": results[0]["content"][:90].replace("\n", " ").replace("|", "/") if results else "-",
                "score": results[0]["score"] if results else 0.0,
                "relevant": relevant,
                "answer": answer[:120].replace("\n", " ").replace("|", "/"),
            }
        )

    print(f"===== TỔNG: {hits}/{len(QUERIES)} câu có chunk liên quan trong top-{args.top_k} =====")

    if args.markdown:
        print("\n--- Bảng dán vào REPORT_CANHAN Phần 5 ---\n")
        print("| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? | Câu trả lời của Agent (tóm tắt) |")
        print("|---|-------|--------------------------------|-------|-----------|------------------------|")
        for row in rows:
            mark = "✅ Có" if row["relevant"] else "❌ Không"
            print(
                f"| {row['index']} | {row['query']} | `{row['top1_doc']}` — {row['top1_preview']}... | "
                f"{row['score']:+.4f} | {mark} | {row['answer']}... |"
            )
        print(f"\n**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** {hits} / {len(QUERIES)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
