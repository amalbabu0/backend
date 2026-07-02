from datetime import datetime, timezone

from fastapi import HTTPException

from ..upstash import UpstashError


def utc_now() -> str:
  return datetime.now(timezone.utc).isoformat()


def upstash_http_error(error: UpstashError) -> HTTPException:
  return HTTPException(status_code=error.status_code, detail=str(error))