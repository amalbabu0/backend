from typing import Annotated

from fastapi import APIRouter, Depends

from ...auth import CurrentUser, get_current_user
from ...upstash import UpstashError, is_configured
from ..common import upstash_http_error
from .schemas import CartIn
from .service import SERVICE_NAME, clear_user_cart, read_cart, replace_cart

UserDep = Annotated[CurrentUser, Depends(get_current_user)]
router = APIRouter(tags=["cart-service"])


@router.get("/api/cart/health")
async def cart_health() -> dict:
  return {
    "service": SERVICE_NAME,
    "ok": True,
    "cacheConfigured": is_configured()
  }


@router.get("/api/cart")
async def get_cart(user: UserDep) -> dict:
  try:
    cart = await read_cart(user.id)
    return {"cart": cart}
  except UpstashError as error:
    raise upstash_http_error(error) from error


@router.put("/api/cart")
async def put_cart(payload: CartIn, user: UserDep) -> dict:
  try:
    cart = await replace_cart(user.id, payload.items)
    return {"cart": cart}
  except UpstashError as error:
    raise upstash_http_error(error) from error


@router.delete("/api/cart")
async def clear_cart(user: UserDep) -> dict:
  try:
    cart = await clear_user_cart(user.id)
    return {"cart": cart}
  except UpstashError as error:
    raise upstash_http_error(error) from error