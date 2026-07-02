from ...products import CACHE_KEYS, PRODUCTS, PRODUCT_CACHE_TTL_SECONDS
from ...upstash import UpstashError, delete_keys, get_json, get_ttl, is_configured, set_json

SERVICE_NAME = "catalog"


async def list_products() -> dict:
  if not is_configured():
    return {
      "products": PRODUCTS,
      "cache": {
        "enabled": False,
        "hit": False,
        "key": CACHE_KEYS["products"],
        "source": "origin",
        "message": "Upstash env vars are not configured."
      }
    }

  try:
    cached_products = await get_json(CACHE_KEYS["products"])
    if isinstance(cached_products, list):
      return {
        "products": cached_products,
        "cache": {
          "enabled": True,
          "hit": True,
          "key": CACHE_KEYS["products"],
          "source": "upstash",
          "ttlSeconds": await get_ttl(CACHE_KEYS["products"])
        }
      }

    await warm_products_cache()
    return {
      "products": PRODUCTS,
      "cache": {
        "enabled": True,
        "hit": False,
        "key": CACHE_KEYS["products"],
        "source": "origin",
        "ttlSeconds": PRODUCT_CACHE_TTL_SECONDS
      }
    }
  except UpstashError:
    return {
      "products": PRODUCTS,
      "cache": {
        "enabled": False,
        "hit": False,
        "key": CACHE_KEYS["products"],
        "source": "origin",
        "error": "Could not reach Upstash from the server."
      }
    }


async def warm_products_cache() -> None:
  await set_json(CACHE_KEYS["products"], PRODUCTS, PRODUCT_CACHE_TTL_SECONDS)


async def clear_products_cache() -> int:
  return await delete_keys([CACHE_KEYS["products"]])


async def products_cache_ttl() -> int:
  return await get_ttl(CACHE_KEYS["products"])