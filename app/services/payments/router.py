from typing import Annotated

from fastapi import APIRouter, Depends

from ...auth import CurrentUser, get_current_user
from ...upstash import UpstashError
from ..common import upstash_http_error
from .schemas import RazorpayOrderIn, RazorpayVerifyIn
from .service import SERVICE_NAME, create_razorpay_order, razorpay_configured, verify_razorpay_payment

UserDep = Annotated[CurrentUser, Depends(get_current_user)]
router = APIRouter(tags=["payments-service"])


@router.get("/api/payments/health")
async def payments_health() -> dict:
  return {
    "service": SERVICE_NAME,
    "ok": True,
    "razorpayConfigured": razorpay_configured()
  }


@router.post("/api/payments/razorpay/order")
async def create_payment_order(payload: RazorpayOrderIn, user: UserDep) -> dict:
  try:
    return await create_razorpay_order(user.id, payload.address, payload.items, payload.checkoutMode)
  except UpstashError as error:
    raise upstash_http_error(error) from error


@router.post("/api/payments/razorpay/verify")
async def verify_payment(payload: RazorpayVerifyIn, user: UserDep) -> dict:
  try:
    return await verify_razorpay_payment(user.id, payload)
  except UpstashError as error:
    raise upstash_http_error(error) from error
