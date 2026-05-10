from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Water Approval AI Service"
    chroma_dir: Path = Path(__file__).resolve().parent.parent / "data" / "chroma"
    default_collection: str = "water_approval_knowledge"


settings = Settings()