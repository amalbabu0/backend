from ...products import APP_PREFIX, CACHE_KEYS
from ...upstash import delete_keys, get_json, get_ttl, is_configured, set_json
from ..cart.service import user_cache_keys
from ..catalog.service import clear_products_cache, warm_products_cache

SERVICE_NAME = "cache-manager"


async def cache_snapshot(user_id: str) -> dict:
  keys = user_cache_keys(user_id)
  if not is_configured():
    return {
      "configured": False,
      "prefix": APP_PREFIX,
      "keys": [],
      "message": "Upstash env vars are not configured."
    }

  all_keys = [CACHE_KEYS["products"], keys["cart"], keys["orders"]]
  return {
    "configured": True,
    "prefix": APP_PREFIX,
    "keys": [
      {"key": key, "ttlSeconds": await get_ttl(key)}
      for key in all_keys
    ],
    "message": "Connected to Upstash."
  }


async def run_cache_action(user_id: str, action: str) -> dict:
  keys = user_cache_keys(user_id)
  message = "Cache updated."

  if action == "warm-all":
    await warm_products_cache()
    if await get_json(keys["cart"]) is None:
      await set_json(keys["cart"], [])
    if await get_json(keys["orders"]) is None:
      await set_json(keys["orders"], [])
    message = "Your cache is warmed."
  elif action == "refresh-products":
    await warm_products_cache()
    message = "Product cache refreshed."
  elif action == "clear-products":
    await clear_products_cache()
    message = "Product cache cleared."
  elif action == "clear-my-cache":
    await delete_keys([keys["cart"], keys["orders"]])
    message = "Your cart and order cache cleared."
  else:
    from fastapi import HTTPException

    raise HTTPException(status_code=400, detail="Unknown cache action.")

  snapshot = await cache_snapshot(user_id)
  snapshot["message"] = message
  return snapshot