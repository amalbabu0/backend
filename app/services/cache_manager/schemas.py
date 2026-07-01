from pydantic import BaseModel


class CacheActionIn(BaseModel):
  action: str