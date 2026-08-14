import httpx
from typing import Optional
from utils.logger import logger

_client: Optional[httpx.AsyncClient] = None

def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        logger.info("Initializing HTTP client connection pool...")
        # Create global client with standard connection pool limits
        limits = httpx.Limits(
            max_keepalive_connections=20,
            max_connections=50,
            keepalive_expiry=30.0
        )
        # Timeout rules: connect = 5s, read = 30s, write = 15s, pool = 10s
        timeout = httpx.Timeout(
            timeout=30.0,
            connect=5.0,
            read=30.0,
            write=15.0,
            pool=10.0
        )
        _client = httpx.AsyncClient(limits=limits, timeout=timeout)
    return _client

async def close_client():
    global _client
    if _client is not None:
        logger.info("Closing HTTP client connection pool...")
        try:
            await _client.aclose()
        except Exception as e:
            logger.error(f"Error closing HTTP connection pool: {e}", exc_info=True)
        finally:
            _client = None
