from collections import Counter
from dataclasses import dataclass, field
from http import HTTPStatus


@dataclass(slots=True)
class SuspiciousActivity:
    ip_address: str
    reason: str
    count: int


@dataclass(slots=True)
class MetricsReport:
    total_requests: int = 0
    total_bytes_sent: int = 0
    status_codes: Counter[HTTPStatus] = field(default_factory=Counter)
    top_endpoints: Counter[str] = field(default_factory=Counter)
    top_ips: Counter[str] = field(default_factory=Counter)
    suspicious_ips: list[SuspiciousActivity] = field(default_factory=list)

    @property
    def error_rate_percentage(self) -> float:
        """Percentage of 4xx and 5xx client/server errors."""
        if self.total_requests == 0:
            return 0.0
        error_count = sum(
            count for status, count in self.status_codes.items() if status.value >= 400
        )
        return (error_count / self.total_requests) * 100
