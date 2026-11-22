"""Settings from env (SPEC-11 §3) and the startup guards (SPEC-09 §6).

Model names may appear here only as defaults; app code asks providers for a role.
"""

from functools import lru_cache
from typing import Literal

from pydantic import BaseModel, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

ALLOWED_EXTENSIONS = [".pdf", ".docx", ".xlsx", ".md", ".png", ".jpg", ".jpeg"]
DOC_TYPES = ["policy", "handbook", "memo", "sop", "spreadsheet", "notice", "chart", "other"]


class DemoUser(BaseModel):
    name: str
    groups: list[str]


class StartupError(SystemExit):
    """Raised when the configuration may not start; the message is printed on exit."""


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=("../.env", ".env"), env_file_encoding="utf-8", extra="ignore")

    app_env: Literal["development", "test", "production"] = "development"
    database_url: str = "postgresql+asyncpg://rag:rag@localhost:5433/rag"
    storage_dir: str = "./storage"
    max_upload_mb: int = 25
    demo_users: dict[str, DemoUser] = Field(default_factory=dict)
    org_name: str = "Serimaju Technologies"
    auth_mode: Literal["demo", "cloudflare_access"] = "demo"

    ai_provider: Literal["ilmu", "openai", "azure", "fake"] = "ilmu"
    ai_base_url: str = "https://api.ilmu.ai/v1"
    ai_api_key: SecretStr = SecretStr("")
    llm_answer_model: str = "nemo-super"
    llm_fast_model: str = "ilmu-nemo-nano"
    llm_fallback_model: str = "ilmu-glm-5.3-flash"
    llm_vision_model: str = "nemo-super"
    llm_judge_model: str = "nemo-super"
    embed_model: str = "bge-m3"
    embed_dim: int = 1024
    rerank_model: str = ""
    ai_max_rpm: int = 50

    top_k: int = 8
    min_vector_sim: float = 0.53
    worker_concurrency: int = 1
    not_found_contacts: dict[str, str] = Field(default_factory=lambda: {"default": "HR, hr@serimaju.example"})

    query_rewrite: bool = False
    k_vec: int = 40
    k_fts: int = 40
    rrf_k: int = 60
    rerank_candidates: int = 30
    min_rerank_score: float = 0.1
    max_chunks_per_doc: int = 4
    max_context_tokens: int = 12000
    chunk_max_tokens: int = 800
    xlsx_rows_per_chunk: int = 20
    embed_batch: int = 64
    ocr_min_chars: int = 80
    tokenizer_id: str = "BAAI/bge-m3"
    docling_artifacts_path: str | None = None

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    def access_groups(self) -> list[str]:
        """Every group a demo user belongs to, `all` first."""
        groups = {g for user in self.demo_users.values() for g in user.groups}
        return sorted(groups, key=lambda g: (g != "all", g))


def check_startup(settings: Settings) -> None:
    """SPEC-09 §6: refuse configurations that must never run."""
    if settings.app_env == "production" and settings.ai_provider == "fake":
        raise StartupError("Fake AI provider is not allowed in production.")
    if settings.app_env == "production" and settings.auth_mode == "demo":
        raise StartupError("Demo identity is not allowed in production. Set AUTH_MODE.")
    if settings.auth_mode == "cloudflare_access":
        raise StartupError("AUTH_MODE=cloudflare_access is not available yet (M100). Use AUTH_MODE=demo.")
    if settings.ai_provider != "fake" and not settings.ai_api_key.get_secret_value():
        raise StartupError(f"AI_API_KEY is not set for AI_PROVIDER={settings.ai_provider}. Set AI_API_KEY.")


@lru_cache
def get_settings() -> Settings:
    return Settings()
