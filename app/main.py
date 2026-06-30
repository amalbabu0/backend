from datetime import datetime, timezone
from typing import Annotated, Literal
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .auth import CurrentUser, get_current_user
from .products import APP_PREFIX, CACHE_KEYS, PRODUCTS, PRODUCT_CACHE_TTL_SECONDS, find_product
from .settings import get_settings
from .upstash import UpstashError, app_keys, delete_keys, get_json, get_ttl, is_configured, set_json

settings = get_settings()
app = FastAPI(title="Cache Commerce API")
app.add_middleware(
  CORSMiddleware,
  allow_origins=list(settings.cors_origins),
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"]
)

UserDep = Annotated[CurrentUser, Depends(get_current_user)]


class CartItemIn(BaseModel):
  productId: str
  quantity: int = Field(ge=1, le=20)


class CartIn(BaseModel):
  items: list[CartItemIn] = Field(default_factory=list)


class OrderIn(BaseModel):
  items: list[CartItemIn] | None = None
  status: Literal["success", "failed", "cancelled"] = "success"


class OrderPatchIn(BaseModel):
  status: Literal["success", "failed", "cancelled"]


class CacheActionIn(BaseModel):
  action: str


def utc_now() -> str:
  return datetime.now(timezone.utc).isoformat()


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


async def read_orders(user_id: str) -> list[dict]:
  orders = await get_json(user_key(user_id, "orders"))
  return orders if isinstance(orders, list) else []


async def write_orders(user_id: str, orders: list[dict]) -> None:
  await set_json(user_key(user_id, "orders"), orders[:50])


def upstash_http_error(error: UpstashError) -> HTTPException:
  return HTTPException(status_code=error.status_code, detail=str(error))


@app.get("/health")
async def health() -> dict:
  return {
    "ok": True,
    "upstashConfigured": is_configured(),
    "supabaseConfigured": bool(settings.supabase_url and settings.supabase_anon_key)
  }


@app.get("/api/products")
async def products() -> dict:
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

    await set_json(CACHE_KEYS["products"], PRODUCTS, PRODUCT_CACHE_TTL_SECONDS)
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


@app.get("/api/cart")
async def get_cart(user: UserDep) -> dict:
  try:
    cart = await read_cart(user.id)
    return {"cart": cart}
  except UpstashError as error:
    raise upstash_http_error(error) from error


@app.put("/api/cart")
async def put_cart(payload: CartIn, user: UserDep) -> dict:
  try:
    normalized = normalize_items(payload.items)
    await write_cart(user.id, normalized)
    return {"cart": normalized}
  except UpstashError as error:
    raise upstash_http_error(error) from error


@app.delete("/api/cart")
async def clear_cart(user: UserDep) -> dict:
  try:
    await delete_keys([user_key(user.id, "cart")])
    return {"cart": []}
  except UpstashError as error:
    raise upstash_http_error(error) from error


@app.get("/api/orders")
async def get_orders(user: UserDep) -> dict:
  try:
    return {"orders": await read_orders(user.id)}
  except UpstashError as error:
    raise upstash_http_error(error) from error


@app.post("/api/orders", status_code=201)
async def create_order(payload: OrderIn, user: UserDep) -> dict:
  try:
    incoming_items = payload.items or [CartItemIn(productId=item["productId"], quantity=item["quantity"]) for item in await read_cart(user.id)]
    if not incoming_items:
      raise HTTPException(status_code=400, detail="Cart is empty.")

    normalized = normalize_items(incoming_items)
    total_paise = sum(item["lineTotalPaise"] for item in normalized)
    now = utc_now()
    order = {
      "id": f"ORD-{uuid4().hex[:10].upper()}",
      "status": payload.status,
      "items": normalized,
      "itemCount": sum(item["quantity"] for item in normalized),
      "totalPaise": total_paise,
      "createdAt": now,
      "updatedAt": now
    }
    orders = await read_orders(user.id)
    await write_orders(user.id, [order, *orders])
    await write_cart(user.id, [])
    return {"order": order}
  except UpstashError as error:
    raise upstash_http_error(error) from error


@app.patch("/api/orders/{order_id}")
async def patch_order(order_id: str, payload: OrderPatchIn, user: UserDep) -> dict:
  try:
    orders = await read_orders(user.id)
    for index, order in enumerate(orders):
      if order["id"] == order_id:
        orders[index] = {
          **order,
          "status": payload.status,
          "updatedAt": utc_now()
        }
        await write_orders(user.id, orders)
        return {"order": orders[index]}

    raise HTTPException(status_code=404, detail="Order not found.")
  except UpstashError as error:
    raise upstash_http_error(error) from error


@app.get("/api/cache")
async def get_cache(user: UserDep) -> dict:
  keys = user_cache_keys(user.id)
  if not is_configured():
    return {
      "configured": False,
      "prefix": APP_PREFIX,
      "keys": [],
      "message": "Upstash env vars are not configured."
    }

  try:
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
  except UpstashError as error:
    return {
      "configured": False,
      "prefix": APP_PREFIX,
      "keys": [],
      "message": str(error)
    }


@app.post("/api/cache")
async def post_cache(payload: CacheActionIn, user: UserDep) -> dict:
  try:
    keys = user_cache_keys(user.id)
    message = "Cache updated."

    if payload.action == "warm-all":
      await set_json(CACHE_KEYS["products"], PRODUCTS, PRODUCT_CACHE_TTL_SECONDS)
      if await get_json(keys["cart"]) is None:
        await set_json(keys["cart"], [])
      if await get_json(keys["orders"]) is None:
        await set_json(keys["orders"], [])
      message = "Your cache is warmed."
    elif payload.action == "refresh-products":
      await set_json(CACHE_KEYS["products"], PRODUCTS, PRODUCT_CACHE_TTL_SECONDS)
      message = "Product cache refreshed."
    elif payload.action == "clear-products":
      await delete_keys([CACHE_KEYS["products"]])
      message = "Product cache cleared."
    elif payload.action == "clear-my-cache":
      await delete_keys([keys["cart"], keys["orders"]])
      message = "Your cart and order cache cleared."
    else:
      raise HTTPException(status_code=400, detail="Unknown cache action.")

    snapshot = await get_cache(user)
    snapshot["message"] = message
    return snapshot
  except UpstashError as error:
    raise upstash_http_error(error) from error
