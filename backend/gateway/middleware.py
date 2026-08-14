"""
Phase 2H — Gateway FastAPI Middleware
Coordinating security headers, request IDs, size validation, rate limits, metrics, and error sanitization.
"""
from __future__ import annotations
import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from gateway.headers import sanitize_or_generate_request_id, get_security_headers
from gateway.request_limits import validate_payload_size
from gateway.rate_limit import rate_limiter
from gateway.abuse import abuse_detector
from gateway.metrics import metrics_collector
from gateway.audit import log_gateway_event
from gateway.errors import GatewayError, INTERNAL_ERROR, REQUEST_TOO_LARGE
from utils.logger import logger


class GatewayMiddleware(BaseHTTPMiddleware):
    """Global request/response gatekeeper."""

    async def dispatch(self, request: Request, call_next):
        start_t = time.perf_counter()
        raw_req_id = request.headers.get("X-Request-ID")
        req_id = sanitize_or_generate_request_id(raw_req_id)
        
        # Determine client origin identifier
        client_ip = request.client.host if request.client else "unknown"
        endpoint = request.url.path
        method = request.method

        # 1. Content-Length Check
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                cl_bytes = int(content_length)
                validate_payload_size(cl_bytes)
            except GatewayError as ge:
                dur = (time.perf_counter() - start_t) * 1000
                metrics_collector.record_request(endpoint, dur, ge.status_code)
                log_gateway_event(
                    request_id=req_id,
                    endpoint=endpoint,
                    method=method,
                    status_code=ge.status_code,
                    duration_ms=dur,
                    rate_limit_status="OK",
                    reason=ge.detail,
                )
                headers = get_security_headers()
                headers["X-Request-ID"] = req_id
                return JSONResponse(
                    status_code=ge.status_code,
                    content={"detail": {"code": ge.code, "message": ge.detail}},
                    headers=headers,
                )
            except Exception:
                pass

        # 2. Abuse Cooldown Check & General Rate Limit
        try:
            abuse_detector.check_abuse_status(client_ip)
            # Skip rate limiting for static / health / docs if needed, but apply to /api
            if endpoint.startswith("/api"):
                rate_limiter.check_and_record(client_ip, operation="GENERAL")
        except GatewayError as ge:
            dur = (time.perf_counter() - start_t) * 1000
            metrics_collector.record_request(endpoint, dur, ge.status_code)
            log_gateway_event(
                request_id=req_id,
                endpoint=endpoint,
                method=method,
                status_code=ge.status_code,
                duration_ms=dur,
                rate_limit_status=ge.code,
                reason=ge.detail,
            )
            headers = get_security_headers()
            headers["X-Request-ID"] = req_id
            return JSONResponse(
                status_code=ge.status_code,
                content={"detail": {"code": ge.code, "message": ge.detail}},
                headers=headers,
            )

        # Process Request
        try:
            response = await call_next(request)
            dur = (time.perf_counter() - start_t) * 1000
            
            # Inject security headers and Request ID
            sec_headers = get_security_headers()
            for k, v in sec_headers.items():
                response.headers[k] = v
            response.headers["X-Request-ID"] = req_id

            metrics_collector.record_request(endpoint, dur, response.status_code)
            log_gateway_event(
                request_id=req_id,
                endpoint=endpoint,
                method=method,
                status_code=response.status_code,
                duration_ms=dur,
            )
            return response

        except Exception as e:
            dur = (time.perf_counter() - start_t) * 1000
            logger.error(f"[gateway] Unhandled exception on {method} {endpoint}: {e}")
            metrics_collector.record_request(endpoint, dur, 500)
            log_gateway_event(
                request_id=req_id,
                endpoint=endpoint,
                method=method,
                status_code=500,
                duration_ms=dur,
                reason=str(e)[:100],
            )
            headers = get_security_headers()
            headers["X-Request-ID"] = req_id
            return JSONResponse(
                status_code=500,
                content={"detail": {"code": INTERNAL_ERROR, "message": "An internal server error occurred."}},
                headers=headers,
            )
