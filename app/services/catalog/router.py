from fastapi import APIRouter

from ...products import CACHE_KEYS
from ...upstash import is_configured
from .service import SERVICE_NAME, list_products

router = APIRouter(tags=["catalog-service"])


@router.get("/api/products")
async def products() -> dict:
  return await list_products()


@router.get("/api/catalog/health")
async def catalog_health() -> dict:
  return {
    "service": SERVICE_NAME,
    "ok": True,
    "cacheConfigured": is_configured(),
    "cacheKey": CACHE_KEYS["products"]
  }