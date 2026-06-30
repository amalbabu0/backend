import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = BACKEND_DIR.parent

load_dotenv(BACKEND_DIR / ".env")
load_dotenv(PROJECT_DIR / ".env")


def csv(value: str) -> list[str]:
  return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
  upstash_redis_rest_url: str = os.getenv("UPSTASH_REDIS_REST_URL", "").rstrip("/")
  upstash_redis_rest_token: str = os.getenv("UPSTASH_REDIS_REST_TOKEN", "")
  supabase_url: str = os.getenv("SUPABASE_URL", "").rstrip("/")
  supabase_anon_key: str = os.getenv("SUPABASE_ANON_KEY", "")
  cors_origins: tuple[str, ...] = tuple(csv(os.getenv("CORS_ORIGINS", "http://localhost:5173")))


@lru_cache
def get_settings() -> Settings:
  return Settings()
