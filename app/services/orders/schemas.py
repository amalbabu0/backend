from typing import Literal

from pydantic import BaseModel

from ..cart.schemas import CartItemIn


class OrderIn(BaseModel):
  items: list[CartItemIn] | None = None
  status: Literal["success", "failed", "cancelled"] = "success"


class OrderPatchIn(BaseModel):
  status: Literal["success", "failed", "cancelled"]