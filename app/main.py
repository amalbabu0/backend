from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .services.cache_manager.router import router as cache_router
from .services.cart.router import router as cart_router
from .services.catalog.router import router as catalog_router
from .services.orders.router import router as orders_router
from .services.payments.router import router as payments_router
from .services.platform.router import router as platform_router
from .settings import get_settings

settings = get_settings()
app = FastAPI(
  title="Cache Commerce API",
  description="API gateway composed of catalog, cart, orders, and cache microservices."
)
app.add_middleware(
  CORSMiddleware,
  allow_origins=list(settings.cors_origins),
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"]
)

app.include_router(platform_router)
app.include_router(catalog_router)
app.include_router(cart_router)
app.include_router(orders_router)
app.include_router(payments_router)
app.include_router(cache_router)
