from typing import Annotated

import httpx
from fastapi import Header, HTTPException
from pydantic import BaseModel

from .settings import get_settings


class CurrentUser(BaseModel):
  id: str
  email: str | None = None


async def get_current_user(authorization: Annotated[str | None, Header()] = None) -> CurrentUser:
  if not authorization or not authorization.startswith("Bearer "):
    raise HTTPException(status_code=401, detail="Missing Supabase access token.")

  settings = get_settings()
  if not settings.supabase_url or not settings.supabase_anon_key:
    raise HTTPException(status_code=503, detail="Supabase backend env vars are not configured.")

  token = authorization.replace("Bearer ", "", 1).strip()
  async with httpx.AsyncClient(timeout=10) as client:
    response = await client.get(
      f"{settings.supabase_url}/auth/v1/user",
      headers={
        "Authorization": f"Bearer {token}",
        "apikey": settings.supabase_anon_key
      }
    )

  if response.status_code in (401, 403):
    raise HTTPException(status_code=401, detail="Invalid or expired Supabase session.")

  if response.status_code >= 400:
    raise HTTPException(status_code=502, detail="Could not verify Supabase session.")

  data = response.json()
  user_id = data.get("id")
  if not user_id:
    raise HTTPException(status_code=401, detail="Invalid Supabase session.")

  return CurrentUser(id=user_id, email=data.get("email"))
