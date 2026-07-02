from pydantic import BaseModel, Field


class SellerRegistrationIn(BaseModel):
  store_name: str = Field(..., min_length=3, max_length=255)
  business_type: str = Field(..., pattern="^(individual|business)$")
  category: str = Field(..., min_length=1, max_length=100)
  gst_number: str | None = Field(None, max_length=15)
  description: str | None = Field(None, max_length=1000)


class SellerOut(BaseModel):
  id: str
  user_id: str
  store_name: str
  business_type: str
  category: str
  gst_number: str | None
  description: str | None
  status: str
  commission_rate: float
  total_products: int
  total_orders: int
  total_revenue: float
  rating: float
  created_at: str
  updated_at: str
