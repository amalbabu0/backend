from pydantic import BaseModel, Field


class CartItemIn(BaseModel):
  productId: str
  quantity: int = Field(ge=1, le=20)


class CartIn(BaseModel):
  items: list[CartItemIn] = Field(default_factory=list)