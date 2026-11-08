import logging

from fastapi import Header, HTTPException, status

from app.configuration import settings

logger = logging.getLogger(__name__)


async def verify_api_key(authorization: str | None = Header(default=None)) -> None:
    if not settings.API_ACCESS_KEY:
        logger.warning("API_ACCESS_KEY not configured - endpoint UNPROTECTED")
        return
    if not authorization:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing Authorization header")
    key = authorization
    if key.lower().startswith("bearer "):
        key = key[len("bearer "):]
    if key.strip() != settings.API_ACCESS_KEY:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid API key")