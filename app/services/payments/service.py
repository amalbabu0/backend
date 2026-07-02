import hashlib
import hmac
from uuid import uuid4

import httpx
from fastapi import HTTPException

from ...settings import get_settings
from ...upstash import delete_keys, get_json, set_json
from ..cart.schemas import CartItemIn
from ..cart.service import normalize_items, read_cart, user_key
from ..common import utc_now
from ..orders.schemas import OrderIn
from ..orders.service import create_order_for_user
from .schemas import PaymentAddressIn, RazorpayVerifyIn

SERVICE_NAME = "payments"
PAYMENT_INTENT_TTL_SECONDS = 900
RAZORPAY_ORDERS_URL = "https://api.razorpay.com/v1/orders"


def razorpay_configured() -> bool:
  settings = get_settings()
  return bool(settings.razorpay_key_id and settings.razorpay_key_secret)


def payment_intent_key(user_id: str) -> str:
  return user_key(user_id, "payment_intent")


def cart_payment_summary(cart: list[dict]) -> dict:
  selling_paise = sum(int(item.get("lineTotalPaise") or 0) for item in cart)
  coupon_paise = min(1200, max(0, round(selling_paise * 0.08))) if cart else 0
  platform_fee_paise = 900 if cart else 0
  total_paise = max(0, selling_paise - coupon_paise + platform_fee_paise)
  return {
    "sellingPaise": selling_paise,
    "couponPaise": coupon_paise,
    "platformFeePaise": platform_fee_paise,
    "totalPaise": total_paise,
    "itemCount": sum(int(item.get("quantity") or 0) for item in cart)
  }


def address_notes(address: PaymentAddressIn | None) -> dict[str, str]:
  if not address:
    return {}

  return {
    key: value[:256]
    for key, value in {
      "customer_name": address.fullName or "",
      "customer_phone": address.phone or "",
      "delivery_city": address.city or "",
      "delivery_state": address.state or "",
      "delivery_pincode": address.pincode or ""
    }.items()
    if value
  }


def address_data(address: PaymentAddressIn | None) -> dict | None:
  if not address:
    return None
  if hasattr(address, "model_dump"):
    return address.model_dump()
  return address.dict()


async def create_razorpay_order(
  user_id: str,
  address: PaymentAddressIn | None = None,
  items: list[CartItemIn] | None = None,
  checkout_mode: str = "cart"
) -> dict:
  settings = get_settings()
  if not razorpay_configured():
    raise HTTPException(status_code=503, detail="Razorpay backend env vars are not configured.")

  is_buy_now = checkout_mode == "buyNow"
  cart = normalize_items(items) if items is not None else await read_cart(user_id)
  if not cart:
    raise HTTPException(status_code=400, detail="Cart is empty.")

  summary = cart_payment_summary(cart)
  if summary["totalPaise"] <= 0:
    raise HTTPException(status_code=400, detail="Payment amount is invalid.")

  receipt = f"rcpt_{uuid4().hex[:24]}"
  payload = {
    "amount": summary["totalPaise"],
    "currency": settings.razorpay_currency,
    "receipt": receipt,
    "notes": {
      "user_id": user_id[:64],
      "item_count": str(summary["itemCount"]),
      **address_notes(address)
    }
  }

  try:
    async with httpx.AsyncClient(timeout=12) as client:
      response = await client.post(
        RAZORPAY_ORDERS_URL,
        auth=(settings.razorpay_key_id, settings.razorpay_key_secret),
        json=payload
      )
  except httpx.RequestError as exc:
    raise HTTPException(status_code=502, detail="Could not reach Razorpay.") from exc

  data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
  if response.status_code >= 400:
    error = data.get("error") if isinstance(data, dict) else None
    detail = error.get("description") if isinstance(error, dict) else "Could not create Razorpay order."
    raise HTTPException(status_code=502, detail=detail)

  razorpay_order_id = data.get("id")
  if not razorpay_order_id:
    raise HTTPException(status_code=502, detail="Razorpay returned an invalid order response.")

  await set_json(
    payment_intent_key(user_id),
    {
      "razorpayOrderId": razorpay_order_id,
      "amountPaise": summary["totalPaise"],
      "currency": settings.razorpay_currency,
      "receipt": receipt,
      "cart": cart,
      "items": cart,
      "checkoutMode": "buyNow" if is_buy_now else "cart",
      "clearCartAfterPayment": not is_buy_now,
      "address": address_data(address),
      "summary": summary,
      "createdAt": utc_now()
    },
    ttl_seconds=PAYMENT_INTENT_TTL_SECONDS
  )

  return {
    "keyId": settings.razorpay_key_id,
    "order": {
      "id": razorpay_order_id,
      "amount": data.get("amount", summary["totalPaise"]),
      "currency": data.get("currency", settings.razorpay_currency),
      "receipt": data.get("receipt", receipt)
    },
    "summary": summary
  }


async def verify_razorpay_payment(user_id: str, payload: RazorpayVerifyIn) -> dict:
  settings = get_settings()
  if not razorpay_configured():
    raise HTTPException(status_code=503, detail="Razorpay backend env vars are not configured.")

  intent = await get_json(payment_intent_key(user_id))
  if not intent or intent.get("razorpayOrderId") != payload.razorpayOrderId:
    raise HTTPException(status_code=400, detail="Payment session has expired. Please try again.")

  message = f"{payload.razorpayOrderId}|{payload.razorpayPaymentId}".encode()
  expected = hmac.new(settings.razorpay_key_secret.encode(), message, hashlib.sha256).hexdigest()
  if not hmac.compare_digest(expected, payload.razorpaySignature):
    raise HTTPException(status_code=400, detail="Payment verification failed.")

  intent_items = intent.get("items") or intent.get("cart", [])
  order = await create_order_for_user(
    user_id,
    OrderIn(
      status="success",
      items=[
        CartItemIn(**item)
        for item in intent_items
      ]
    ),
    payment={
      "provider": "razorpay",
      "razorpayOrderId": payload.razorpayOrderId,
      "razorpayPaymentId": payload.razorpayPaymentId,
      "amountPaise": intent.get("amountPaise"),
      "currency": intent.get("currency"),
      "verifiedAt": utc_now()
    },
    total_paise=intent.get("amountPaise"),
    pricing=intent.get("summary"),
    clear_cart=bool(intent.get("clearCartAfterPayment", True))
  )
  await delete_keys([payment_intent_key(user_id)])
  return {"order": order}
