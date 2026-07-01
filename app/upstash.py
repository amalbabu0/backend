import json
from typing import Any

import httpx

from .products import APP_PREFIX
from .settings import get_settings


class UpstashError(Exception):
  def __init__(self, message: str, status_code: int = 502, code: str = "UPSTASH_ERROR") -> None:
    super().__init__(message)
    self.status_code = status_code
    self.code = code


def is_configured() -> bool:
  settings = get_settings()
  return bool(settings.upstash_redis_rest_url and settings.upstash_redis_rest_token)


async def command(parts: list[Any]) -> Any:
  settings = get_settings()
  if not is_configured():
    raise UpstashError("Upstash environment variables are not configured.", 503, "UPSTASH_NOT_CONFIGURED")

  try:
    async with httpx.AsyncClient(timeout=10) as client:
      response = await client.post(
        settings.upstash_redis_rest_url,
        headers={
          "Authorization": f"Bearer {settings.upstash_redis_rest_token}",
          "Content-Type": "application/json"
        },
        json=parts
      )
  except httpx.RequestError as exc:
    raise UpstashError("Could not reach Upstash from the server.", 502, "UPSTASH_NETWORK_ERROR") from exc

  try:
    data = response.json()
  except ValueError as exc:
    raise UpstashError("Upstash returned an invalid response.", 502, "UPSTASH_INVALID_RESPONSE") from exc

  if not isinstance(data, dict):
    raise UpstashError("Upstash returned an invalid response.", 502, "UPSTASH_INVALID_RESPONSE")

  if response.status_code >= 400 or data.get("error"):
    status_code = 401 if response.status_code == 401 else 502
    raise UpstashError(data.get("error", "Upstash request failed."), status_code, "UPSTASH_REQUEST_FAILED")

  return data.get("result")


async def get_json(key: str) -> Any:
  value = await command(["GET", key])
  if value is None:
    return None

  if not isinstance(value, str):
    return value

  return json.loads(value)


async def set_json(key: str, value: Any, ttl_seconds: int | None = None) -> Any:
  serialized = json.dumps(value, separators=(",", ":"))
  if ttl_seconds:
    return await command(["SET", key, serialized, "EX", ttl_seconds])

  return await command(["SET", key, serialized])


async def get_ttl(key: str) -> int:
  return await command(["TTL", key])


async def delete_keys(keys: list[str]) -> int:
  filtered = [key for key in keys if key]
  if not filtered:
    return 0

  return await command(["DEL", *filtered])


async def app_keys(pattern: str | None = None) -> list[str]:
  keys = await command(["KEYS", pattern or f"{APP_PREFIX}:*"])
  return sorted(keys) if isinstance(keys, list) else []