from uuid import uuid4

from fastapi import HTTPException

from ...upstash import get_json, set_json
from ..cart.schemas import CartItemIn
from ..cart.service import normalize_items, read_cart, user_key, write_cart
from ..common import utc_now
from .schemas import OrderIn, OrderPatchIn

SERVICE_NAME = "orders"


async def read_orders(user_id: str) -> list[dict]:
  orders = await get_json(user_key(user_id, "orders"))
  return orders if isinstance(orders, list) else []


async def write_orders(user_id: str, orders: list[dict]) -> None:
  await set_json(user_key(user_id, "orders"), orders[:50])


async def create_order_for_user(user_id: str, payload: OrderIn) -> dict:
  incoming_items = payload.items
  if incoming_items is None:
    incoming_items = [
      CartItemIn(productId=item["productId"], quantity=item["quantity"])
      for item in await read_cart(user_id)
    ]

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
  orders = await read_orders(user_id)
  await write_orders(user_id, [order, *orders])
  await write_cart(user_id, [])
  return order


async def update_order_status(user_id: str, order_id: str, payload: OrderPatchIn) -> dict:
  orders = await read_orders(user_id)
  for index, order in enumerate(orders):
    if order["id"] == order_id:
      orders[index] = {
        **order,
        "status": payload.status,
        "updatedAt": utc_now()
      }
      await write_orders(user_id, orders)
      return orders[index]

  raise HTTPException(status_code=404, detail="Order not found.")