from fastapi import APIRouter

from ...settings import get_settings
from ...upstash import is_configured

router = APIRouter(tags=["platform"])

SERVICE_REGISTRY = [
  {
    "name": "catalog",
    "responsibility": "Product listings and product cache warming.",
    "health": "/api/catalog/health",
    "routes": ["GET /api/products"]
  },
  {
    "name": "cart",
    "responsibility": "Authenticated user cart storage in Upstash Redis.",
    "health": "/api/cart/health",
    "routes": ["GET /api/cart", "PUT /api/cart", "DELETE /api/cart"]
  },
  {
    "name": "orders",
    "responsibility": "Authenticated order creation, history, and status changes.",
    "health": "/api/orders/health",
    "routes": ["GET /api/orders", "POST /api/orders", "PATCH /api/orders/{order_id}"]
  },
  {
    "name": "payments",
    "responsibility": "Razorpay order creation and payment signature verification.",
    "health": "/api/payments/health",
    "routes": ["POST /api/payments/razorpay/order", "POST /api/payments/razorpay/verify"]
  },
  {
    "name": "cache-manager",
    "responsibility": "Cache inspection, warming, refreshing, and user cache clearing.",
    "health": "/api/cache/health",
    "routes": ["GET /api/cache", "POST /api/cache"]
  }
]


@router.get("/health")
async def health() -> dict:
  settings = get_settings()
  return {
    "ok": True,
    "architecture": "microservice-gateway",
    "services": [service["name"] for service in SERVICE_REGISTRY],
    "upstashConfigured": is_configured(),
    "supabaseConfigured": bool(settings.supabase_url and settings.supabase_anon_key),
    "razorpayConfigured": bool(settings.razorpay_key_id and settings.razorpay_key_secret)
  }


@router.get("/api/services")
async def services() -> dict:
  return {
    "gateway": "cache-commerce-api",
    "architecture": "microservice-gateway",
    "services": SERVICE_REGISTRY
  }
