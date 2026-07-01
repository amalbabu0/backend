from fastapi import HTTPException

from ...products import APP_PREFIX, find_product
from ...upstash import delete_keys, get_json, set_json
from .schemas import CartItemIn

SERVICE_NAME = "cart"


def user_key(user_id: str, name: str) -> str:
  return f"{APP_PREFIX}:user:{user_id}:{name}"


def user_cache_keys(user_id: str) -> dict[str, str]:
  return {
    "cart": user_key(user_id, "cart"),
    "orders": user_key(user_id, "orders")
  }


def normalize_items(items: list[CartItemIn]) -> list[dict]:
  normalized = []
  for item in items:
    product = find_product(item.productId)
    if not product:
      raise HTTPException(status_code=400, detail="Cart contains an invalid product.")

    normalized.append({
      "productId": product["id"],
      "name": product["name"],
      "pricePaise": product["pricePaise"],
      "quantity": item.quantity,
      "lineTotalPaise": product["pricePaise"] * item.quantity
    })

  return normalized


async def read_cart(user_id: str) -> list[dict]:
  cart = await get_json(user_key(user_id, "cart"))
  return cart if isinstance(cart, list) else []


async def write_cart(user_id: str, items: list[dict]) -> None:
  await set_json(user_key(user_id, "cart"), items)


async def replace_cart(user_id: str, items: list[CartItemIn]) -> list[dict]:
  normalized = normalize_items(items)
  await write_cart(user_id, normalized)
  return normalized


async def clear_user_cart(user_id: str) -> list[dict]:
  await delete_keys([user_key(user_id, "cart")])
  return []