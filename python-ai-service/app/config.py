from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Water Approval AI Service"
    chroma_dir: Path = Path(__file__).resolve().parent.parent / "data" / "chroma"
    default_collection: str = "water_approval_knowledge"
    port: int = 8000

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