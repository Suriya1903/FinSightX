from __future__ import annotations

from prometheus_client import Counter, Histogram


HTTP_REQUESTS_TOTAL = Counter(
    "finsightx_http_requests_total",
    "Total number of HTTP requests received by the API Gateway.",
    [
        "method",
        "path",
        "status_code",
    ],
)


HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "finsightx_http_request_duration_seconds",
    "HTTP request processing duration in seconds.",
    [
        "method",
        "path",
    ],
)


def record_http_request(
    *,
    method: str,
    path: str,
    status_code: int,
    duration_seconds: float,
) -> None:
    HTTP_REQUESTS_TOTAL.labels(
        method=method,
        path=path,
        status_code=str(status_code),
    ).inc()

    HTTP_REQUEST_DURATION_SECONDS.labels(
        method=method,
        path=path,
    ).observe(duration_seconds)