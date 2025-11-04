"""HTTP client utilities for the Article Quadrant Analyzer MCP Server."""

import asyncio
import logging
import time
import os
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse
import hashlib

import httpx
from fake_useragent import UserAgent

from mcp_server_article_quadrant.utils.error_handling import NetworkError, ValidationError, handle_error


class RateLimiter:
    """Rate limiter for HTTP requests to prevent overwhelming servers."""

    def __init__(self, max_requests_per_minute: int = 30):
        self.max_requests_per_minute = max_requests_per_minute
        self.requests = {}  # domain -> list of timestamps
        self.lock = asyncio.Lock()

    async def check_rate_limit(self, domain: str) -> bool:
        """Check if domain request limit is exceeded."""
        async with self.lock:
            current_time = time.time()
            minute_ago = current_time - 60

            # Clean old requests
            if domain in self.requests:
                self.requests[domain] = [
                    req_time for req_time in self.requests[domain]
                    if req_time > minute_ago
                ]
            else:
                self.requests[domain] = []

            # Check if we can make a request
            if len(self.requests[domain]) >= self.max_requests_per_minute:
                return False

            # Add current request
            self.requests[domain].append(current_time)
            return True

    async def wait_if_needed(self, domain: str) -> Optional[float]:
        """Wait if rate limit is exceeded and return wait time."""
        if await self.check_rate_limit(domain):
            return None

        # Calculate wait time
        if domain in self.requests and self.requests[domain]:
            oldest_request = min(self.requests[domain])
            wait_time = 60 - (time.time() - oldest_request)
            if wait_time > 0:
                await asyncio.sleep(wait_time)
                return wait_time

        return None


class HTTPClient:
    """Enhanced HTTP client with rate limiting, retries, and error handling."""

    def __init__(
        self,
        timeout: float = 30.0,
        max_retries: int = 3,
        max_concurrent: int = 5,
        enable_rate_limiting: bool = True,
        custom_headers: Optional[Dict[str, str]] = None,
        verify_ssl: bool = True
    ):
        self.timeout = timeout
        self.max_retries = max_retries
        self.max_concurrent = max_concurrent
        self.enable_rate_limiting = enable_rate_limiting
        self.custom_headers = custom_headers or {}
        self.verify_ssl = verify_ssl

        self.logger = logging.getLogger(__name__)
        self.rate_limiter = RateLimiter() if enable_rate_limiting else None
        self.semaphore = asyncio.Semaphore(max_concurrent)

        # Generate user agent
        self.ua = UserAgent()
        default_user_agent = os.getenv("USER_AGENT", "ArticleQuadrantAnalyzer/1.0")

        # Setup default headers
        self.default_headers = {
            "User-Agent": self.ua.random if hasattr(self.ua, 'random') else default_user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        self.default_headers.update(self.custom_headers)

        # Create HTTP client
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            follow_redirects=True,
            max_redirects=5,
            verify=verify_ssl,
            headers=self.default_headers
        )

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    def _get_domain(self, url: str) -> str:
        """Extract domain from URL for rate limiting."""
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower()
        except Exception:
            return "unknown"

    def _cache_key(self, url: str, method: str = "GET") -> str:
        """Generate cache key for request."""
        return hashlib.md5(f"{method}:{url}".encode()).hexdigest()

    async def _make_request(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> httpx.Response:
        """Make HTTP request with rate limiting and retries."""
        domain = self._get_domain(url)

        async with self.semaphore:
            # Rate limiting
            if self.rate_limiter:
                wait_time = await self.rate_limiter.wait_if_needed(domain)
                if wait_time:
                    self.logger.info(f"Rate limited for {domain}, waited {wait_time:.2f}s")

            last_exception = None

            for attempt in range(self.max_retries + 1):
                try:
                    self.logger.debug(f"HTTP {method} {url} (attempt {attempt + 1})")

                    # Add random delay to avoid detection
                    if attempt > 0:
                        delay = min(2 ** attempt, 10)  # Exponential backoff, max 10s
                        await asyncio.sleep(delay)

                    response = await self.client.request(method, url, **kwargs)

                    # Check for successful response
                    if response.status_code < 400:
                        return response

                    # Handle specific error codes
                    if response.status_code == 429:  # Rate limited
                        retry_after = int(response.headers.get('Retry-After', 60))
                        self.logger.warning(f"Rate limited by {domain}, waiting {retry_after}s")
                        await asyncio.sleep(retry_after)
                        continue

                    elif response.status_code in [401, 403]:  # Auth/Forbidden
                        raise NetworkError(
                            f"Access denied to {url}",
                            url=url,
                            status_code=response.status_code,
                            details={"response_text": response.text[:500]}
                        )

                    elif response.status_code >= 500:  # Server error
                        raise NetworkError(
                            f"Server error for {url}",
                            url=url,
                            status_code=response.status_code,
                            details={"response_text": response.text[:500]}
                        )

                    else:  # Client error
                        raise NetworkError(
                            f"HTTP {response.status_code} for {url}",
                            url=url,
                            status_code=response.status_code,
                            details={"response_text": response.text[:500]}
                        )

                except httpx.TimeoutException as e:
                    last_exception = NetworkError(
                        f"Request timeout for {url}",
                        url=url,
                        timeout=self.timeout,
                        details={"timeout": self.timeout}
                    )
                    self.logger.warning(f"Timeout for {url} (attempt {attempt + 1})")

                except httpx.ConnectError as e:
                    last_exception = NetworkError(
                        f"Connection error for {url}",
                        url=url,
                        details={"error": str(e)}
                    )
                    self.logger.warning(f"Connection error for {url} (attempt {attempt + 1})")

                except httpx.HTTPError as e:
                    last_exception = NetworkError(
                        f"HTTP error for {url}: {e}",
                        url=url,
                        details={"error": str(e)}
                    )
                    self.logger.warning(f"HTTP error for {url} (attempt {attempt + 1})")

                except Exception as e:
                    last_exception = NetworkError(
                        f"Unexpected error for {url}: {e}",
                        url=url,
                        details={"error": str(e)}
                    )
                    self.logger.warning(f"Unexpected error for {url} (attempt {attempt + 1})")

            # All retries failed
            if last_exception:
                raise last_exception
            else:
                raise NetworkError(f"Failed to request {url} after {self.max_retries} retries")

    async def get(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> httpx.Response:
        """Make GET request."""
        request_headers = self.default_headers.copy()
        if headers:
            request_headers.update(headers)

        return await self._make_request(
            "GET",
            url,
            headers=request_headers,
            params=params,
            **kwargs
        )

    async def post(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> httpx.Response:
        """Make POST request."""
        request_headers = self.default_headers.copy()
        if headers:
            request_headers.update(headers)

        return await self._make_request(
            "POST",
            url,
            data=data,
            json=json,
            headers=request_headers,
            **kwargs
        )

    async def fetch_content(
        self,
        url: str,
        max_content_length: Optional[int] = None,
        follow_redirects: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Fetch content from URL with size limits and validation.

        Returns:
            Dict with content, metadata, and response info
        """
        try:
            # Validate URL
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                raise ValidationError(f"Invalid URL: {url}", field_name="url", field_value=url)

            response = await self.get(url, **kwargs)

            # Check content length
            content_length = response.headers.get('content-length')
            if content_length:
                try:
                    length = int(content_length)
                    if max_content_length and length > max_content_length:
                        self.logger.warning(
                            f"Content too large: {length} bytes (limit: {max_content_length})"
                        )
                        # Return truncated content
                        content = response.text[:max_content_length]
                    else:
                        content = response.text
                except ValueError:
                    content = response.text
            else:
                content = response.text
                if max_content_length and len(content) > max_content_length:
                    self.logger.warning(
                        f"Content truncated to {max_content_length} characters"
                    )
                    content = content[:max_content_length]

            # Extract metadata
            metadata = {
                "url": str(response.url),
                "status_code": response.status_code,
                "content_type": response.headers.get("content-type"),
                "content_length": len(content),
                "encoding": response.encoding,
                "headers": dict(response.headers),
                "final_url": str(response.url) if str(response.url) != url else None
            }

            return {
                "content": content,
                "metadata": metadata,
                "success": True
            }

        except Exception as e:
            self.logger.error(f"Failed to fetch content from {url}: {e}")
            return {
                "content": None,
                "metadata": {"url": url, "error": str(e)},
                "success": False,
                "error": handle_error(e, context={"url": url})
            }

    async def fetch_multiple(
        self,
        urls: List[str],
        max_concurrent: Optional[int] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Fetch content from multiple URLs concurrently."""
        semaphore = asyncio.Semaphore(max_concurrent or self.max_concurrent)

        async def fetch_single(url: str):
            async with semaphore:
                return await self.fetch_content(url, **kwargs)

        tasks = [fetch_single(url) for url in urls]
        return await asyncio.gather(*tasks, return_exceptions=True)


# Global HTTP client instance
_http_client: Optional[HTTPClient] = None


def get_http_client() -> HTTPClient:
    """Get or create global HTTP client instance."""
    global _http_client
    if _http_client is None:
        timeout = float(os.getenv("REQUEST_TIMEOUT", "30"))
        max_retries = int(os.getenv("MAX_RETRIES", "3"))
        max_concurrent = int(os.getenv("MAX_CONCURRENT_REQUESTS", "5"))

        _http_client = HTTPClient(
            timeout=timeout,
            max_retries=max_retries,
            max_concurrent=max_concurrent
        )

    return _http_client


async def close_http_client():
    """Close global HTTP client."""
    global _http_client
    if _http_client:
        await _http_client.close()
        _http_client = None