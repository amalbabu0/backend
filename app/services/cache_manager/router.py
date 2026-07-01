from typing import Annotated

from fastapi import APIRouter, Depends

from ...auth import CurrentUser, get_current_user
from ...upstash import UpstashError, is_configured
from ..common import upstash_http_error
from .schemas import CacheActionIn
from .service import SERVICE_NAME, cache_snapshot, run_cache_action

UserDep = Annotated[CurrentUser, Depends(get_current_user)]
router = APIRouter(tags=["cache-manager-service"])


@router.get("/api/cache/health")
async def cache_health() -> dict:
  return {
    "service": SERVICE_NAME,
    "ok": True,
    "cacheConfigured": is_configured()
  }


@router.get("/api/cache")
async def get_cache(user: UserDep) -> dict:
  try:
    return await cache_snapshot(user.id)
  except UpstashError as error:
    return {
      "configured": False,
      "prefix": "cache-commerce",
      "keys": [],
      "message": str(error)
    }


@router.post("/api/cache")
async def post_cache(payload: CacheActionIn, user: UserDep) -> dict:
  try:
    return await run_cache_action(user.id, payload.action)
  except UpstashError as error:
    raise upstash_http_error(error) from error