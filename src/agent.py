from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        # 1. Truy xuất
        results = self.store.search(question, top_k=top_k)
        if not results:
            return "Không tìm thấy thông tin liên quan trong cơ sở tri thức."

        # 2. Dựng prompt — đánh số nguồn để có thể truy vết chunk nào tạo ra câu trả lời.
        context = "\n\n".join(
            f"[Nguồn {index}] (doc_id={result['metadata'].get('doc_id', 'unknown')}, "
            f"score={result['score']:.3f})\n{result['content']}"
            for index, result in enumerate(results, start=1)
        )
        prompt = (
            "Bạn là trợ lý trả lời câu hỏi dựa trên tài liệu được cung cấp.\n"
            "Chỉ dùng thông tin trong phần NGỮ CẢNH. Nếu ngữ cảnh không đủ, hãy nói rõ là không biết.\n\n"
            f"NGỮ CẢNH:\n{context}\n\n"
            f"CÂU HỎI: {question}\n\n"
            "TRẢ LỜI (kèm số hiệu nguồn đã dùng):"
        )

        # 3. Sinh câu trả lời
        return self.llm_fn(prompt)
