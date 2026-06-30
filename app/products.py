APP_PREFIX = "cache-commerce"
PRODUCT_CACHE_TTL_SECONDS = 300

CACHE_KEYS = {
  "products": f"{APP_PREFIX}:products"
}

PRODUCTS = [
  {
    "id": "pulse-headphones",
    "name": "Pulse Wireless Headphones",
    "description": "Noise-softening over-ear audio with 40 hours of battery.",
    "pricePaise": 100,
    "badge": "Audio",
    "image": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=900&q=80",
    "alt": "Black wireless headphones on a bright background"
  },
  {
    "id": "loop-smartwatch",
    "name": "Loop Smart Watch",
    "description": "Lightweight fitness tracking with calls, steps and sleep insights.",
    "pricePaise": 200,
    "badge": "Wearable",
    "image": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=900&q=80",
    "alt": "Smart watch with a clean strap on a tabletop"
  },
  {
    "id": "city-backpack",
    "name": "City Day Backpack",
    "description": "Water-resistant daily bag with a padded laptop section.",
    "pricePaise": 100,
    "badge": "Travel",
    "image": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?auto=format&fit=crop&w=900&q=80",
    "alt": "Brown backpack photographed in natural light"
  },
  {
    "id": "nova-sneakers",
    "name": "Nova Run Sneakers",
    "description": "Cushioned everyday sneakers with breathable knit support.",
    "pricePaise": 200,
    "badge": "Footwear",
    "image": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=900&q=80",
    "alt": "Red running shoes floating above a red surface"
  }
]


def find_product(product_id: str) -> dict | None:
  return next((product for product in PRODUCTS if product["id"] == product_id), None)
