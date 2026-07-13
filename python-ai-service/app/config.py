from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Water Approval AI Service"
    chroma_dir: Path = Path(__file__).resolve().parent.parent / "data" / "chroma"
    default_collection: str = "water_approval_knowledge"
    port: int = 8000

    # Embedding backend configuration
    embedding_provider: str = "hash"
    embedding_model_name: str = "BAAI/bge-small-zh-v1.5"
    embedding_fallback_provider: str = "hash"

    # PDF reader configuration
    pdf_reader_provider: str = "auto"
    pdf_reader_min_chars: int = 80
    pdf_reader_qwen_model: str = "qwen-vl-plus-latest"
    pdf_reader_max_pages: int = 20
    pdf_reader_render_zoom: float = 2.0

    # Semantic retrieval tuning
    semantic_search_candidate_k: int = 12
    semantic_search_max_variants: int = 4
    semantic_search_lexical_weight: float = 0.35
    semantic_search_vector_weight: float = 0.65

    # Review flow mode: fast, smart, or strict.
    # fast: rules + retrieval only; smart: call external AI only for risky cases; strict: always call external AI.
    review_mode: str = "smart"

    # Document parse cache. Keeps extracted text by file SHA256 to avoid repeated OCR/PDF parsing.
    document_cache_enabled: bool = True
    document_cache_dir: Path = Path(__file__).resolve().parent.parent / "data" / "document_cache"

    # External AI integration (optional)
    external_ai_enabled: bool = False
    # API key/token for DashScope compatible OpenAI API (or other compatible providers)
    external_ai_api_key: Optional[str] = None
    # Compatible base URL. DashScope default is kept for convenience.
    external_ai_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    # Model name for chat completions.
    external_ai_model: str = "qwen3.6-plus"
    # Whether to pass extra_body={"enable_thinking": True}.
    external_ai_enable_thinking: bool = True
    # Provider hint (for display and future extension)
    external_ai_provider: str = "dashscope-openai-compatible"


settings = Settings()
