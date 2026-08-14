"""
Phase 2J — Safe Streaming Response Engine
Wraps provider token streams with bounded size limits, chunk sanitization, and timeout protection.
"""
from typing import Iterator, Optional
import time
from llm.schemas import LLMRequest
from llm.errors import LLMError, STREAM_ERROR
from llm.sanitizer import redact_secrets

MAX_STREAM_BYTES = 512 * 1024  # 512 KB limit for stream responses


class SafeStreamManager:
    """Wraps raw stream generators with bounds checks, cancellation hooks, and secret redaction."""

    @staticmethod
    def wrap_stream(
        stream_iter: Iterator[str],
        request: LLMRequest,
        is_cancelled_callback: Optional[callable] = None,
    ) -> Iterator[str]:
        total_bytes = 0
        start_t = time.perf_counter()

        try:
            for chunk in stream_iter:
                # Check for cooperative cancellation
                if is_cancelled_callback and is_cancelled_callback():
                    break

                # Check timeout
                if time.perf_counter() - start_t > request.timeout:
                    break

                # Size constraint
                chunk_bytes = len(chunk.encode("utf-8"))
                total_bytes += chunk_bytes
                if total_bytes > MAX_STREAM_BYTES:
                    break

                # Redact any accidental secret fragments
                clean_chunk, _ = redact_secrets(chunk)
                yield clean_chunk

        except Exception as e:
            # Never bubble unhandled raw provider exceptions to streaming client
            yield f"\n[STREAM_TERMINATED: Provider stream interrupted]"
