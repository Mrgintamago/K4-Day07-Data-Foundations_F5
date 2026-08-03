"""
Bài tập 3.3 — Dự đoán độ tương tự cosine (Cá nhân).

Quy tắc của bài: GHI DỰ ĐOÁN TRƯỚC KHI CHẠY. Các dự đoán bên dưới đã được
viết cứng trong `PAIRS` trước khi chạy lần đầu, nên không thể sửa hồi tố.

Chạy:
    export PYTHONIOENCODING=utf-8
    EMBEDDING_PROVIDER=local python scripts/similarity_demo.py

Không đặt EMBEDDING_PROVIDER thì rơi về mock (chỉ hợp để chạy thử — mock sinh
vector gần như ngẫu nhiên nên KHÔNG phản ánh ngữ nghĩa tiếng Việt).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv  # noqa: E402

from src.chunking import compute_similarity  # noqa: E402
from src.embeddings import (  # noqa: E402
    EMBEDDING_PROVIDER_ENV,
    LOCAL_EMBEDDING_MODEL,
    OPENAI_EMBEDDING_MODEL,
    LocalEmbedder,
    OpenAIEmbedder,
    _mock_embed,
)

# (câu A, câu B, dự đoán, lý do dự đoán)
PAIRS: list[tuple[str, str, str, str]] = [
    (
        "Tôi muốn trả lại đơn hàng vì sản phẩm bị lỗi.",
        "Làm sao để hoàn trả hàng hóa không đúng mô tả?",
        "CAO",
        "Cùng ý định đổi trả, chỉ khác cách diễn đạt.",
    ),
    (
        "Người bán phải cung cấp hóa đơn hợp lệ cho mọi đơn hàng.",
        "Người bán có nghĩa vụ xuất chứng từ mua bán cho khách.",
        "CAO",
        "Cùng nghĩa vụ của người bán, dùng từ đồng nghĩa.",
    ),
    (
        "Phí vận chuyển được tính theo khối lượng và khoảng cách.",
        "Chính sách bảo mật quy định cách sàn xử lý dữ liệu cá nhân.",
        "THẤP",
        "Hai chủ đề chính sách hoàn toàn khác nhau.",
    ),
    (
        "Đơn hàng sẽ được giao trong vòng 3 ngày làm việc.",
        "Thời gian giao hàng dự kiến là 72 giờ kể từ khi xác nhận.",
        "CAO",
        "Cùng thông tin thời gian giao hàng, diễn đạt bằng đơn vị khác.",
    ),
    (
        "Hôm nay trời Hà Nội mưa rất to.",
        "Điều kiện để sản phẩm được chấp nhận bảo hành là còn tem niêm phong.",
        "THẤP",
        "Không liên quan gì đến nhau — dùng làm mốc đối chứng.",
    ),
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


def main() -> int:
    embedder = select_embedder()
    backend = getattr(embedder, "_backend_name", embedder.__class__.__name__)
    print(f"Backend nhúng: {backend}\n")
    if backend == "mock embeddings fallback":
        print(
            "CẢNH BÁO: mock sinh vector gần như ngẫu nhiên. Kết quả dưới đây KHÔNG dùng để\n"
            "kết luận về ngữ nghĩa — hãy chạy lại với EMBEDDING_PROVIDER=local trước khi\n"
            "dán vào REPORT_CANHAN.md.\n"
        )

    scores = []
    for index, (sentence_a, sentence_b, prediction, _reason) in enumerate(PAIRS, start=1):
        score = compute_similarity(embedder(sentence_a), embedder(sentence_b))
        scores.append(score)
        print(f"Cặp {index}: dự đoán={prediction:5s}  thực tế={score:+.4f}")
        print(f"   A: {sentence_a}")
        print(f"   B: {sentence_b}\n")

    # Ngưỡng phân loại: lấy trung bình làm mốc, tránh gán cứng một con số.
    threshold = sum(scores) / len(scores)
    print(f"Ngưỡng phân loại (trung bình 5 cặp): {threshold:+.4f}\n")

    print("| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |")
    print("|-----|-------|-------|---------|--------------|-------|")
    correct = 0
    for index, ((sentence_a, sentence_b, prediction, _r), score) in enumerate(zip(PAIRS, scores), start=1):
        actual = "CAO" if score >= threshold else "THẤP"
        hit = "✅" if actual == prediction else "❌"
        correct += actual == prediction
        print(f"| {index} | {sentence_a} | {sentence_b} | {prediction} | {score:+.4f} | {hit} |")
    print(f"\nDự đoán đúng: {correct}/{len(PAIRS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
