import httpx
from fastapi import HTTPException

from ...settings import get_settings
from .schemas import SellerRegistrationIn, SellerOut

SERVICE_NAME = "sellers"


async def get_seller_by_user_id(user_id: str) -> dict | None:
  """Get seller profile by user_id"""
  settings = get_settings()
  if not settings.supabase_url or not settings.supabase_anon_key:
    raise HTTPException(status_code=503, detail="Supabase not configured.")

  async with httpx.AsyncClient(timeout=10) as client:
    response = await client.get(
      f"{settings.supabase_url}/rest/v1/sellers?user_id=eq.{user_id}",
      headers={
        "apikey": settings.supabase_anon_key,
        "Authorization": f"Bearer {settings.supabase_anon_key}"
      }
    )

  if response.status_code >= 400:
    if response.status_code == 404:
      return None
    raise HTTPException(status_code=502, detail="Failed to fetch seller profile.")

  data = response.json()
  return data[0] if isinstance(data, list) and len(data) > 0 else None


async def create_seller(user_id: str, payload: SellerRegistrationIn) -> dict:
  """Register a new seller"""
  settings = get_settings()
  if not settings.supabase_url or not settings.supabase_anon_key:
    raise HTTPException(status_code=503, detail="Supabase not configured.")

  # Check if seller already exists
  existing = await get_seller_by_user_id(user_id)
  if existing:
    raise HTTPException(status_code=400, detail="User is already registered as a seller.")

  seller_data = {
    "user_id": user_id,
    "store_name": payload.store_name,
    "business_type": payload.business_type,
    "category": payload.category,
    "gst_number": payload.gst_number,
    "description": payload.description,
    "status": "pending"
  }

  async with httpx.AsyncClient(timeout=10) as client:
    response = await client.post(
      f"{settings.supabase_url}/rest/v1/sellers",
      json=seller_data,
      headers={
        "apikey": settings.supabase_anon_key,
        "Authorization": f"Bearer {settings.supabase_anon_key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
      }
    )

  if response.status_code not in (200, 201):
    print(f"Supabase error: {response.status_code} - {response.text}")
    raise HTTPException(status_code=502, detail="Failed to create seller profile.")

  data = response.json()
  seller = data[0] if isinstance(data, list) else data
  return seller


async def update_seller(user_id: str, updates: dict) -> dict:
  """Update seller profile"""
  settings = get_settings()
  if not settings.supabase_url or not settings.supabase_anon_key:
    raise HTTPException(status_code=503, detail="Supabase not configured.")

  async with httpx.AsyncClient(timeout=10) as client:
    response = await client.patch(
      f"{settings.supabase_url}/rest/v1/sellers?user_id=eq.{user_id}",
      json=updates,
      headers={
        "apikey": settings.supabase_anon_key,
        "Authorization": f"Bearer {settings.supabase_anon_key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
      }
    )

  if response.status_code >= 400:
    raise HTTPException(status_code=502, detail="Failed to update seller profile.")

  data = response.json()
  return data[0] if isinstance(data, list) and len(data) > 0 else {}
