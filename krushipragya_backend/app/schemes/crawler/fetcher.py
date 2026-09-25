"""Asynchronous HTTP fetcher with SSRF guards, streaming size limits, retries, and rate limiting."""
import asyncio
from dataclasses import dataclass
from datetime import datetime
import logging
import time
from typing import Dict, List, Optional
from urllib.parse import urlparse

import httpx

from app.core.config import settings
from app.schemes.crawler.security import is_safe_url

logger = logging.getLogger(__name__)


@dataclass
class FetchResult:
    """Outcome of fetching an official source webpage."""
    url: str
    status_code: int
    content: str
    content_type: str
    headers: Dict[str, str]
    last_modified: Optional[str] = None
    error: Optional[str] = None
    is_success: bool = False


class SchemeFetcher:
    """Production-safe HTTP client for crawling approved government scheme portals."""

    def __init__(
        self,
        timeout_seconds: float = float(settings.SCHEME_CRAWL_TIMEOUT_SECONDS),
        max_size_mb: int = settings.SCHEME_MAX_DOCUMENT_SIZE_MB,
        max_retries: int = settings.SCHEME_MAX_RETRIES,
        request_delay_ms: int = settings.SCHEME_REQUEST_DELAY_MS,
        user_agent: str = settings.SCHEME_USER_AGENT,
    ):
        self.timeout = timeout_seconds
        self.max_bytes = max_size_mb * 1024 * 1024
        self.max_retries = max_retries
        self.delay_seconds = request_delay_ms / 1000.0
        self.user_agent = user_agent
        self._last_request_times: Dict[str, float] = {}

    async def _rate_limit(self, hostname: str) -> None:
        """Enforce polite crawling delay per host."""
        now = time.monotonic()
        last_time = self._last_request_times.get(hostname, 0.0)
        elapsed = now - last_time
        if elapsed < self.delay_seconds:
            await asyncio.sleep(self.delay_seconds - elapsed)
        self._last_request_times[hostname] = time.monotonic()

    async def fetch(
        self,
        url: str,
        allowed_domains: List[str],
    ) -> FetchResult:
        """Fetch page content safely with SSRF protection, size caps, and backoff retries.
        
        Args:
            url: Target URL to fetch.
            allowed_domains: Approved domain patterns for SSRF and allowlist check.
            
        Returns:
            FetchResult object with text or error details.
        """
        # Step 1: Pre-fetch security check
        safe, reason = is_safe_url(url, allowed_domains)
        if not safe:
            logger.warning("Blocked fetch for unsafe URL '%s': %s", url, reason)
            return FetchResult(
                url=url,
                status_code=0,
                content="",
                content_type="",
                headers={},
                error=reason,
                is_success=False,
            )

        hostname = urlparse(url).hostname or ""
        await self._rate_limit(hostname)

        headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "kn,en-US,en;q=0.9",
        }

        # Step 2: Fetch with retries and streaming size protection
        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                async with httpx.AsyncClient(
                    timeout=httpx.Timeout(self.timeout),
                    follow_redirects=True,
                    headers=headers,
                ) as client:
                    async with client.stream("GET", url) as response:
                        # Validate final redirect destination
                        final_url = str(response.url)
                        if final_url != url:
                            safe_dest, reason_dest = is_safe_url(final_url, allowed_domains)
                            if not safe_dest:
                                return FetchResult(
                                    url=final_url,
                                    status_code=response.status_code,
                                    content="",
                                    content_type=response.headers.get("content-type", ""),
                                    headers=dict(response.headers),
                                    error=f"Redirect to unsafe destination: {reason_dest}",
                                    is_success=False,
                                )

                        # Check Content-Length header if present
                        content_length = response.headers.get("content-length")
                        if content_length and content_length.isdigit():
                            if int(content_length) > self.max_bytes:
                                return FetchResult(
                                    url=final_url,
                                    status_code=response.status_code,
                                    content="",
                                    content_type=response.headers.get("content-type", ""),
                                    headers=dict(response.headers),
                                    error=f"Document exceeds maximum size limit of {self.max_bytes // (1024*1024)}MB",
                                    is_success=False,
                                )

                        if response.status_code >= 400:
                            return FetchResult(
                                url=final_url,
                                status_code=response.status_code,
                                content="",
                                content_type=response.headers.get("content-type", ""),
                                headers=dict(response.headers),
                                error=f"HTTP {response.status_code} received from official source",
                                is_success=False,
                            )

                        # Stream response bytes with counter
                        chunks = []
                        total_bytes = 0
                        async for chunk in response.aiter_bytes():
                            total_bytes += len(chunk)
                            if total_bytes > self.max_bytes:
                                return FetchResult(
                                    url=final_url,
                                    status_code=response.status_code,
                                    content="",
                                    content_type=response.headers.get("content-type", ""),
                                    headers=dict(response.headers),
                                    error=f"Response exceeded size limit of {self.max_bytes // (1024*1024)}MB during stream",
                                    is_success=False,
                                )
                            chunks.append(chunk)

                        raw_body = b"".join(chunks)
                        # Decode HTML with fallback
                        encoding = response.encoding or "utf-8"
                        try:
                            text_content = raw_body.decode(encoding)
                        except UnicodeDecodeError:
                            text_content = raw_body.decode("utf-8", errors="replace")

                        return FetchResult(
                            url=final_url,
                            status_code=response.status_code,
                            content=text_content,
                            content_type=response.headers.get("content-type", ""),
                            headers=dict(response.headers),
                            last_modified=response.headers.get("last-modified"),
                            error=None,
                            is_success=True,
                        )

            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                last_error = f"Network/Timeout error on attempt {attempt}: {exc}"
                logger.warning("Fetch failed for %s (%s). Retrying...", url, last_error)
                if attempt < self.max_retries:
                    await asyncio.sleep(0.5 * (2 ** (attempt - 1)))  # Exponential backoff
            except Exception as exc:
                last_error = f"Unexpected fetch error: {exc}"
                logger.error("Fetch exception for %s: %s", url, exc)
                break

        return FetchResult(
            url=url,
            status_code=0,
            content="",
            content_type="",
            headers={},
            error=last_error or "Unknown fetch error",
            is_success=False,
        )
