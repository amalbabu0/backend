from pydantic import BaseModel, Field


class CartItemIn(BaseModel):
  productId: str
  sellerProductId: str | None = None
  name: str | None = None
  pricePaise: int | None = Field(default=None, ge=1)
  quantity: int = Field(ge=1, le=20)


class CartIn(BaseModel):
  items: list[CartItemIn] = Field(default_factory=list)
