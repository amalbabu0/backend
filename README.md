# Cache Commerce Backend

FastAPI backend for Supabase-authenticated cache storage.

## Architecture

The backend now runs as a microservice-style API gateway on Vercel. Each business area has its own service folder with independent router and service logic, while the public API contract stays stable for the frontend.

```text
app/services/catalog        Product catalog and product cache
app/services/cart           User cart cache
app/services/orders         Order history and status updates
app/services/cache_manager  Cache warming, clearing, and inspection
app/services/platform       Health and service registry endpoints
```

Use `GET /api/services` to see the service registry and `GET /health` to check gateway health.

## Env

```text
UPSTASH_REDIS_REST_URL=https://your-database-name.upstash.io
UPSTASH_REDIS_REST_TOKEN=your_upstash_redis_rest_token
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key
CORS_ORIGINS=http://localhost:5173,https://your-frontend-domain.vercel.app
```

## Run

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Endpoints

- `GET /health`
- `GET /api/services`
- `GET /api/catalog/health`
- `GET /api/products`
- `GET /api/cart/health`
- `GET /api/cart`
- `PUT /api/cart`
- `DELETE /api/cart`
- `GET /api/orders/health`
- `GET /api/orders`
- `POST /api/orders`
- `PATCH /api/orders/{order_id}`
- `GET /api/cache/health`
- `GET /api/cache`
- `POST /api/cache`