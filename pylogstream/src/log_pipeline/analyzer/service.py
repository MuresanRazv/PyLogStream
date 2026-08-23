from collections import Counter
from collections.abc import Iterable
from http import HTTPStatus

from log_pipeline.analyzer.models import MetricsReport, SuspiciousActivity
from log_pipeline.models.logs import LogLine


class LogsAnalyzer:
    def __init__(
        self,
        brute_force_threshold: int = 20,
        rate_limit_threshold: int = 500,
    ) -> None:
        self.brute_force_threshold = brute_force_threshold
        self.rate_limit_threshold = rate_limit_threshold

    def analyze(self, entries: Iterable[LogLine]) -> MetricsReport:
        report = MetricsReport()
        failed_auth_per_ip: Counter[str] = Counter()
        requests_per_ip: Counter[str] = Counter()

        for entry in entries:
            # 1. Update general volume metrics
            report.total_requests += 1
            report.total_bytes_sent += entry.response_size
            report.status_codes[entry.http_status] += 1
            report.top_endpoints[entry.endpoint] += 1
            report.top_ips[entry.ip_address] += 1

            # 2. Track per-IP heuristic triggers
            requests_per_ip[entry.ip_address] += 1
            if entry.http_status in (HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN):
                failed_auth_per_ip[entry.ip_address] += 1

        # 3. Post-process anomaly flags
        for ip, count in failed_auth_per_ip.items():
            if count >= self.brute_force_threshold:
                report.suspicious_ips.append(
                    SuspiciousActivity(
                        ip_address=ip,
                        reason="Potential Brute Force / Unauthorized Access Spike",
                        count=count,
                    )
                )

        for ip, count in requests_per_ip.items():
            if count >= self.rate_limit_threshold:
                report.suspicious_ips.append(
                    SuspiciousActivity(
                        ip_address=ip,
                        reason="Rate limit burst / High-rate scanner",
                        count=count,
                    )
                )

        return report
