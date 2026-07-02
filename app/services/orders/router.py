from typing import Annotated

from fastapi import APIRouter, Depends

from ...auth import CurrentUser, get_current_user
from ...upstash import UpstashError, is_configured
from ..common import upstash_http_error
from .schemas import OrderIn, OrderPatchIn
from .service import SERVICE_NAME, create_order_for_user, read_orders, update_order_status

UserDep = Annotated[CurrentUser, Depends(get_current_user)]
router = APIRouter(tags=["orders-service"])


@router.get("/api/orders/health")
async def orders_health() -> dict:
  return {
    "service": SERVICE_NAME,
    "ok": True,
    "cacheConfigured": is_configured()
  }


@router.get("/api/orders")
async def get_orders(user: UserDep) -> dict:
  try:
    return {"orders": await read_orders(user.id)}
  except UpstashError as error:
    raise upstash_http_error(error) from error


@router.post("/api/orders", status_code=201)
async def create_order(payload: OrderIn, user: UserDep) -> dict:
  try:
    return {"order": await create_order_for_user(user.id, payload)}
  except UpstashError as error:
    raise upstash_http_error(error) from error


@router.patch("/api/orders/{order_id}")
async def patch_order(order_id: str, payload: OrderPatchIn, user: UserDep) -> dict:
  try:
    return {"order": await update_order_status(user.id, order_id, payload)}
  except UpstashError as error:
    raise upstash_http_error(error) from error