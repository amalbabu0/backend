from pydantic import BaseModel


class PaymentAddressIn(BaseModel):
  fullName: str | None = None
  phone: str | None = None
  address: str | None = None
  pincode: str | None = None
  city: str | None = None
  state: str | None = None


class RazorpayOrderIn(BaseModel):
  address: PaymentAddressIn | None = None


class RazorpayVerifyIn(BaseModel):
  razorpayOrderId: str
  razorpayPaymentId: str
  razorpaySignature: str
