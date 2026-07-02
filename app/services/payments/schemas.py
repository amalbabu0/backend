from typing import Literal

from pydantic import BaseModel

from ..cart.schemas import CartItemIn


class PaymentAddressIn(BaseModel):
  fullName: str | None = None
  phone: str | None = None
  address: str | None = None
  pincode: str | None = None
  city: str | None = None
  state: str | None = None


class RazorpayOrderIn(BaseModel):
  address: PaymentAddressIn | None = None
  items: list[CartItemIn] | None = None
  checkoutMode: Literal["cart", "buyNow"] = "cart"


class RazorpayVerifyIn(BaseModel):
  razorpayOrderId: str
  razorpayPaymentId: str
  razorpaySignature: str
