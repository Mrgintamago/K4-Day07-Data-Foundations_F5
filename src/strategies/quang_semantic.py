"""
Chiến lược của Quang — `SemanticParentChunker`: cắt theo ngữ nghĩa + trả về ngữ cảnh cha.

Ý TƯỞNG CỐT LÕI
---------------
Cả 3 chiến lược dựng sẵn trong `src/chunking.py` đều **cắt mù**: chúng chỉ nhìn dấu câu
(`SentenceChunker`), dấu phân cách (`RecursiveChunker`) hoặc số ký tự (`FixedSizeChunker`).
Không cái nào ĐỌC nội dung để quyết định chỗ cắt.

Chiến lược này dùng chính **mô hình nhúng** làm thước đo ranh giới:

    1. Tách văn bản thành câu.
    2. Nhúng TỪNG câu -> vector.
    3. Đo cosine giữa mỗi cặp câu liền kề. Khoảng cách = 1 - cosine.
    4. Cắt tại những vị trí có khoảng cách LỚN NHẤT (vượt ngưỡng phân vị) — đó chính là
       chỗ mạch ý chuyển sang chủ đề khác.

    s1 ──0.82──► s2 ──0.79──► s3 ──0.31──► s4
                                    ▲
                            cắt tại đây (ý đổi hướng)

Ranh giới chunk vì thế là **ranh giới Ý**, không phải ranh giới dấu chấm hay số ký tự.

CƠ CHẾ THỨ HAI: PARENT CONTEXT (small-to-big retrieval)
------------------------------------------------------
Bài học rút ra từ lần chạy benchmark trước với `HeadingChunker`: khi dán tiêu đề mục vào
đầu chunk, tiêu đề chiếm tỷ trọng lớn trong vector và **kéo điểm số theo tiêu đề thay vì
theo nội dung** — câu benchmark số 5 hỏi "thu thập dữ liệu từ nguồn nào" đã khớp nhầm vào
mục "THU THẬP CÁC DỮ LIỆU KHÁC" chỉ vì trùng tiêu đề.

Cách sửa: **tách phần dùng để TÌM khỏi phần dùng để TRẢ LỜI**.

    - Phần nhúng (child)  = đoạn ngữ nghĩa thuần, KHÔNG chứa tiêu đề -> tìm chính xác
    - Phần ngữ cảnh (parent) = tiêu đề mục cha, lưu trong metadata `parent_heading`
      -> agent dùng để trả lời, nhưng KHÔNG ảnh hưởng điểm similarity

Đây là điều `EmbeddingStore` cho phép làm mà 3 chiến lược dựng sẵn không tận dụng:
`metadata` đi kèm từng chunk và được trả về nguyên vẹn trong kết quả `search()`.

ĐIỂM YẾU (phải nêu trong báo cáo)
---------------------------------
- **Chi phí nhúng cao hơn hẳn**: phải nhúng từng câu để tìm ranh giới, rồi nhúng lại từng
  chunk khi nạp store. Trên corpus 6 tài liệu là chấp nhận được, nhưng không scale cho
  hàng nghìn tài liệu nếu không cache.
- **Phụ thuộc chất lượng mô hình nhúng**: nếu chạy bằng mock embedder thì ranh giới cắt
  ra hoàn toàn ngẫu nhiên — chiến lược này BẮT BUỘC dùng `EMBEDDING_PROVIDER=local`.
- Ngưỡng phân vị là siêu tham số phải tinh chỉnh; đặt quá thấp thì chunk vụn, quá cao thì
  chunk dính vào nhau.
"""
from __future__ import annotations

import re

from ..chunking import RecursiveChunker, compute_similarity

# Tách câu: cắt tại khoảng trắng đứng sau dấu kết câu, giữ dấu câu ở cuối câu.
SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")

# Tiêu đề/điều khoản dùng làm ngữ cảnh cha: "# ...", "1.", "1.2.", "I."
HEADING_RE = re.compile(
    r"^(?:#{1,6}\s+\S.*|\d+(?:\.\d+)*\.?\s+\S.*|[IVX]+\.\s+\S.*)$",
    re.MULTILINE,
)


class SemanticParentChunker:
    """Cắt theo ngữ nghĩa (embedding) và gắn ngữ cảnh mục cha vào metadata.

    Args:
        embedding_fn: hàm nhúng dùng để đo ranh giới ngữ nghĩa. BẮT BUỘC là embedder
            thật — mock sẽ cho ranh giới ngẫu nhiên.
        breakpoint_percentile: phân vị khoảng cách để chọn điểm cắt. 90 nghĩa là cắt tại
            10% vị trí có khoảng cách ngữ nghĩa lớn nhất.
        max_chunk_size: chunk vượt ngưỡng này sẽ được cắt phụ bằng RecursiveChunker.
        min_sentences: số câu tối thiểu mỗi chunk, tránh chunk 1 câu quá ngắn.
    """

    def __init__(
        self,
        embedding_fn,
        breakpoint_percentile: float = 90.0,
        max_chunk_size: int = 900,
        min_sentences: int = 2,
        heading_weight: int = 1,
    ) -> None:
        self.embedding_fn = embedding_fn
        self.breakpoint_percentile = breakpoint_percentile
        self.max_chunk_size = max_chunk_size
        self.min_sentences = max(1, min_sentences)
        # Số lần lặp tiêu đề mục cha trong phần đem đi NHÚNG:
        #   0 = bỏ hẳn tiêu đề (tiêu đề chỉ nằm trong metadata)
        #   1 = ghép tiêu đề một lần vào đầu chunk
        #   2 = lặp tiêu đề hai lần -> tăng trọng số tín hiệu tiêu đề trong vector
        self.heading_weight = max(0, heading_weight)
        self._fallback = RecursiveChunker(chunk_size=max_chunk_size)

    def embed_text(self, child: str, parent_heading: str) -> str:
        """Dựng đúng chuỗi sẽ được đem đi nhúng, theo `heading_weight`."""
        if not parent_heading or self.heading_weight == 0:
            return child
        prefix = "\n".join([parent_heading] * self.heading_weight)
        return f"{prefix}\n{child}"

    # ------------------------------------------------------------------ API chính

    def chunk(self, text: str) -> list[str]:
        """Interface chuẩn của lab: trả về danh sách chuỗi (không kèm ngữ cảnh cha)."""
        return [child for child, _parent in self.chunk_with_parents(text)]

    def chunk_with_parents(self, text: str) -> list[tuple[str, str]]:
        """Trả về danh sách `(nội_dung_chunk, tiêu_đề_mục_cha)`.

        `nội_dung_chunk` là thứ được đem đi NHÚNG (không chứa tiêu đề).
        `tiêu_đề_mục_cha` được lưu vào metadata để agent dùng khi trả lời.
        """
        if not text or not text.strip():
            return []

        sections = self._split_by_heading(text)
        results: list[tuple[str, str]] = []

        for heading, body in sections:
            body = body.strip()
            if not body:
                continue
            for piece in self._semantic_split(body):
                if len(piece) <= self.max_chunk_size:
                    results.append((piece, heading))
                    continue
                # Đoạn ngữ nghĩa vẫn quá dài -> cắt phụ, giữ nguyên ngữ cảnh cha.
                for sub in self._fallback.chunk(piece):
                    results.append((sub, heading))
        return [(c.strip(), h) for c, h in results if c.strip()]

    # ------------------------------------------------------- cắt theo ngữ nghĩa

    def _semantic_split(self, text: str) -> list[str]:
        """Cắt một đoạn văn tại các vị trí ý nghĩa chuyển hướng mạnh nhất."""
        sentences = [s.strip() for s in SENTENCE_RE.split(text) if s.strip()]
        if len(sentences) <= self.min_sentences:
            return [text.strip()] if text.strip() else []

        vectors = [self.embedding_fn(s) for s in sentences]

        # Khoảng cách ngữ nghĩa giữa hai câu liền kề: càng lớn càng nên cắt.
        distances = [
            1.0 - compute_similarity(vectors[i], vectors[i + 1])
            for i in range(len(sentences) - 1)
        ]
        if not distances:
            return [text.strip()]

        threshold = self._percentile(distances, self.breakpoint_percentile)

        chunks: list[str] = []
        current: list[str] = [sentences[0]]
        for index, distance in enumerate(distances):
            next_sentence = sentences[index + 1]
            # Chỉ cắt khi vượt ngưỡng VÀ chunk hiện tại đã đủ số câu tối thiểu.
            if distance >= threshold and len(current) >= self.min_sentences:
                chunks.append(" ".join(current))
                current = [next_sentence]
            else:
                current.append(next_sentence)
        if current:
            chunks.append(" ".join(current))
        return chunks

    @staticmethod
    def _percentile(values: list[float], percentile: float) -> float:
        """Phân vị theo nội suy tuyến tính (không phụ thuộc numpy)."""
        if not values:
            return 0.0
        ordered = sorted(values)
        if len(ordered) == 1:
            return ordered[0]
        position = (percentile / 100.0) * (len(ordered) - 1)
        lower = int(position)
        upper = min(lower + 1, len(ordered) - 1)
        weight = position - lower
        return ordered[lower] * (1 - weight) + ordered[upper] * weight

    # ------------------------------------------------------------- ngữ cảnh cha

    def _split_by_heading(self, text: str) -> list[tuple[str, str]]:
        """Tách văn bản thành các mục `(tiêu_đề, nội_dung)` để lấy ngữ cảnh cha."""
        matches = list(HEADING_RE.finditer(text))
        if not matches:
            return [("", text)]

        sections: list[tuple[str, str]] = []
        preamble = text[: matches[0].start()].strip()
        if preamble:
            sections.append(("", preamble))

        for index, match in enumerate(matches):
            heading = match.group(0).strip()
            start = match.end()
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            sections.append((heading, text[start:end]))
        return sections


# Cấu hình cuối cùng, chọn sau khi chạy `scripts/sweep_heading_weight.py`:
#   heading_weight=0 -> 7/10   (bỏ tiêu đề: tốt cho câu 2, mất tín hiệu ở câu 3)
#   heading_weight=1 -> 6/10   (ghép một lần: TỆ NHẤT — xem giải thích trong báo cáo)
#   heading_weight=2 -> 8/10   (lặp hai lần: tiêu đề đủ mạnh để dẫn hướng)
CHOSEN_HEADING_WEIGHT = 2


def build_chunker(embedding_fn, heading_weight: int | None = None):
    """Cấu hình Quang dùng để chạy benchmark."""
    return SemanticParentChunker(
        embedding_fn=embedding_fn,
        breakpoint_percentile=90.0,
        max_chunk_size=900,
        min_sentences=2,
        heading_weight=CHOSEN_HEADING_WEIGHT if heading_weight is None else heading_weight,
    )


def build_store(
    data_dir: str,
    embedding_fn,
    collection_name: str = "lab7_semantic",
    heading_weight: int | None = None,
):
    """Nạp corpus theo cơ chế parent-context.

    Khác `ingest.build_knowledge_base()` ở đúng một điểm: tiêu đề mục cha được đưa vào
    `metadata["parent_heading"]` thay vì ghép vào nội dung. Nhờ đó vector chỉ mã hóa
    phần nội dung ngữ nghĩa, còn ngữ cảnh cha vẫn đi kèm kết quả `search()`.
    """
    from ingest import load_documents
    from ..models import Document
    from ..store import EmbeddingStore

    chunker = build_chunker(embedding_fn, heading_weight=heading_weight)
    chunk_docs: list[Document] = []

    for doc in load_documents(data_dir):
        for index, (child, parent_heading) in enumerate(chunker.chunk_with_parents(doc.content)):
            metadata = dict(doc.metadata)
            metadata["doc_id"] = doc.id
            metadata["chunk_index"] = index
            metadata["parent_heading"] = parent_heading or "(không có tiêu đề)"
            chunk_docs.append(
                Document(
                    id=f"{doc.id}::chunk_{index}",
                    # Nội dung = thứ được NHÚNG (có/không có tiêu đề tùy heading_weight).
                    content=chunker.embed_text(child, parent_heading),
                    metadata=metadata,
                )
            )

    store = EmbeddingStore(collection_name=collection_name, embedding_fn=embedding_fn)
    store.add_documents(chunk_docs)
    return store
