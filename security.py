"""Pure, testable security helpers: in-memory rate limiting and HTTP headers.

Kept dependency-free and side-effect-free (no FastAPI imports) so the logic can be
unit-tested without spinning up the app or loading the ML model.
"""
import time
from collections import defaultdict, deque
from typing import Deque, Dict, MutableMapping, Optional

# Login/registration brute-force throttle: at most LOGIN_RATE_LIMIT attempts per
# LOGIN_RATE_WINDOW seconds, keyed by client IP.
LOGIN_RATE_LIMIT = 8
LOGIN_RATE_WINDOW = 300  # 5 minutes

# Module-level default store. Tests pass their own store for isolation.
_attempts: Dict[str, Deque[float]] = defaultdict(deque)


def is_rate_limited(
    key: str,
    now: Optional[float] = None,
    limit: int = LOGIN_RATE_LIMIT,
    window: int = LOGIN_RATE_WINDOW,
    store: Optional[MutableMapping[str, Deque[float]]] = None,
) -> bool:
    """Return True if `key` has exceeded `limit` attempts within `window` seconds.

    When not rate-limited, the current attempt is recorded. Old timestamps outside
    the window are evicted on each call (sliding window).
    """
    store = _attempts if store is None else store
    now = time.time() if now is None else now
    dq = store[key]
    cutoff = now - window
    while dq and dq[0] <= cutoff:
        dq.popleft()
    if len(dq) >= limit:
        return True
    dq.append(now)
    return False


def reset_rate_limits(store: Optional[MutableMapping[str, Deque[float]]] = None) -> None:
    """Clear all recorded attempts (used by tests)."""
    (store if store is not None else _attempts).clear()


# Defense-in-depth response headers applied to every response.
# CSP allows the specific CDNs the templates load (fonts, icons, Chart.js, Quill,
# html2pdf) plus 'unsafe-inline' (the templates use inline <style>/<script> and
# inline event handlers). object-src/base-uri/frame-ancestors still close off the
# highest-risk vectors (plugins, base-tag hijack, clickjacking).
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "SAMEORIGIN",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Content-Security-Policy": "; ".join([
        "default-src 'self'",
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://cdn.quilljs.com",
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net https://cdn.quilljs.com",
        "font-src 'self' data: https://fonts.gstatic.com https://cdn.jsdelivr.net",
        "img-src 'self' data: blob:",
        "connect-src 'self'",
        "frame-src 'self' blob:",
        "object-src 'none'",
        "base-uri 'self'",
        "frame-ancestors 'self'",
    ]),
}


def client_ip(forwarded_for: Optional[str], peer: Optional[str]) -> str:
    """Resolve the client IP, honoring the first hop of X-Forwarded-For when present.

    Hosting platforms (e.g. Hugging Face Spaces) put the real client IP in
    X-Forwarded-For; fall back to the direct peer address otherwise.
    """
    if forwarded_for:
        first = forwarded_for.split(",")[0].strip()
        if first:
            return first
    return peer or "unknown"
