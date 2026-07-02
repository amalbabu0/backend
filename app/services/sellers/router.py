from typing import Annotated

from fastapi import APIRouter, Depends

from ...auth import CurrentUser, get_current_user
from .schemas import SellerRegistrationIn, SellerOut
from .service import SERVICE_NAME, create_seller, get_seller_by_user_id

UserDep = Annotated[CurrentUser, Depends(get_current_user)]
router = APIRouter(tags=["sellers-service"])


@router.get("/api/sellers/health")
async def sellers_health() -> dict:
  return {
    "service": SERVICE_NAME,
    "ok": True
  }


@router.get("/api/sellers/me", response_model=SellerOut | None)
async def get_my_seller_profile(user: UserDep) -> dict | None:
  """Get current user's seller profile"""
  return await get_seller_by_user_id(user.id)


@router.post("/api/sellers", status_code=201, response_model=SellerOut)
async def register_seller(payload: SellerRegistrationIn, user: UserDep) -> dict:
  """Register as a seller"""
  return await create_seller(user.id, payload)
