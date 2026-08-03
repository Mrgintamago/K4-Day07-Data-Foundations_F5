"""
Chọn LLM thật cho `KnowledgeBaseAgent.llm_fn` thay vì stub trích ngữ cảnh.

Vì sao cần: rubric `docs/SCORING.md` cho 2 điểm/câu chỉ khi "top-3 chứa chunk liên quan
**VÀ** câu trả lời của agent chính xác". Với stub `demo_llm` (chỉ trích nguyên văn Nguồn 1),
ta không đánh giá được vế thứ hai — agent không thực sự tổng hợp từ nhiều chunk.

Cấu hình trong `.env` (file này nằm trong .gitignore, KHÔNG push khóa API lên repo):

    # Cách 1 — Anthropic
    LLM_PROVIDER=anthropic
    ANTHROPIC_API_KEY=sk-ant-...
    ANTHROPIC_MODEL=claude-sonnet-5          # mặc định

    # Cách 2 — OpenAI
    LLM_PROVIDER=openai
    OPENAI_API_KEY=sk-...
    OPENAI_CHAT_MODEL=gpt-4o-mini            # mặc định

    # Cách 3 — không cấu hình gì: tự động dùng stub (echo ngữ cảnh)

Để `LLM_PROVIDER=auto` (hoặc bỏ trống) thì tự dò: có ANTHROPIC_API_KEY -> anthropic,
có OPENAI_API_KEY -> openai, không có gì -> stub. Mọi lỗi (thiếu thư viện, khóa sai,
hết quota) đều rơi về stub kèm cảnh báo, để benchmark không bao giờ crash giữa chừng.

Cài thư viện tương ứng:
    pip install anthropic          # nếu dùng Anthropic
    pip install openai             # nếu dùng OpenAI
"""
from __future__ import annotations

import os
from typing import Callable

DEFAULT_ANTHROPIC_MODEL = "claude-sonnet-5"
DEFAULT_OPENAI_CHAT_MODEL = "gpt-4o-mini"
MAX_TOKENS = 500

SYSTEM_PROMPT = (
    "Bạn là trợ lý trả lời câu hỏi về chính sách thương mại điện tử. "
    "Chỉ dùng thông tin trong phần NGỮ CẢNH được cung cấp. "
    "Nếu ngữ cảnh không đủ để trả lời, hãy nói rõ là không tìm thấy thông tin. "
    "Trả lời ngắn gọn bằng tiếng Việt và ghi rõ đã dùng Nguồn số mấy."
)


def _echo_stub(prompt: str) -> str:
    """LLM giả lập: trích nguyên văn Nguồn 1 để kiểm tra grounding thủ công."""
    marker = "[Nguồn 1]"
    if marker in prompt:
        body = prompt.split(marker, 1)[1].split("[Nguồn 2]", 1)[0]
        body = body.split("\n", 1)[-1].strip()
        return f"(stub — trích Nguồn 1) {body[:280]}..."
    return "Không đủ ngữ cảnh để trả lời."


def _make_anthropic(model: str) -> Callable[[str], str]:
    from anthropic import Anthropic

    client = Anthropic()  # tự đọc ANTHROPIC_API_KEY từ môi trường

    def call(prompt: str) -> str:
        response = client.messages.create(
            model=model,
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(block.text for block in response.content if block.type == "text").strip()

    return call


def _make_openai(model: str) -> Callable[[str], str]:
    from openai import OpenAI

    client = OpenAI()  # tự đọc OPENAI_API_KEY từ môi trường

    def call(prompt: str) -> str:
        response = client.chat.completions.create(
            model=model,
            max_tokens=MAX_TOKENS,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )
        return (response.choices[0].message.content or "").strip()

    return call


def select_llm() -> tuple[Callable[[str], str], str]:
    """Trả về `(hàm_llm, tên_backend)`. Không bao giờ raise — lỗi thì rơi về stub."""
    provider = os.getenv("LLM_PROVIDER", "auto").strip().lower()

    if provider in ("auto", ""):
        if os.getenv("ANTHROPIC_API_KEY"):
            provider = "anthropic"
        elif os.getenv("OPENAI_API_KEY"):
            provider = "openai"
        else:
            return _echo_stub, "stub (chưa cấu hình LLM_PROVIDER hoặc API key)"

    if provider == "anthropic":
        model = os.getenv("ANTHROPIC_MODEL", DEFAULT_ANTHROPIC_MODEL)
        try:
            return _make_anthropic(model), f"anthropic/{model}"
        except Exception as error:
            print(f"Anthropic không sẵn sàng ({error}); tạm dùng stub.")
            return _echo_stub, "stub (anthropic lỗi)"

    if provider == "openai":
        model = os.getenv("OPENAI_CHAT_MODEL", DEFAULT_OPENAI_CHAT_MODEL)
        try:
            return _make_openai(model), f"openai/{model}"
        except Exception as error:
            print(f"OpenAI không sẵn sàng ({error}); tạm dùng stub.")
            return _echo_stub, "stub (openai lỗi)"

    print(f"LLM_PROVIDER='{provider}' không hợp lệ (chọn: anthropic | openai | auto); dùng stub.")
    return _echo_stub, "stub (provider không hợp lệ)"


def safe_llm(llm_fn: Callable[[str], str]) -> Callable[[str], str]:
    """Bọc llm_fn để một lần gọi lỗi (rate limit, mạng) không làm hỏng cả benchmark."""

    def call(prompt: str) -> str:
        try:
            return llm_fn(prompt)
        except Exception as error:
            return f"[LỖI GỌI LLM: {type(error).__name__}] {_echo_stub(prompt)}"

    return call
