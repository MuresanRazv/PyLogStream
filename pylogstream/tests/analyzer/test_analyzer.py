from datetime import UTC, datetime
from http import HTTPMethod, HTTPStatus

from log_pipeline.analyzer.service import LogsAnalyzer
from log_pipeline.models.logs import LogLine


def test_analyze_stream_aggregates_correctly() -> None:
    now = datetime.now(UTC)
    entries = [
        LogLine(
            ip_address="10.0.0.1",
            timestamp=now,
            endpoint="/api/v1/resource",
            http_status=HTTPStatus.OK,
            response_size=500,
            http_method=HTTPMethod.GET,
            referer="https://example.com",
            user_agent="Mozilla/5.0",
        ),
        LogLine(
            ip_address="10.0.0.1",
            timestamp=now,
            endpoint="/api/v1/resource",
            http_status=HTTPStatus.OK,
            response_size=500,
            http_method=HTTPMethod.GET,
            referer="https://example.com",
            user_agent="Mozilla/5.0",
        ),
        LogLine(
            ip_address="10.0.0.2",
            timestamp=now,
            endpoint="/login",
            http_status=HTTPStatus.UNAUTHORIZED,
            response_size=100,
            http_method=HTTPMethod.POST,
            referer="",
            user_agent="",
        ),
    ]

    service = LogsAnalyzer(brute_force_threshold=1)
    report = service.analyze(entries)

    assert report.total_requests == 3
    assert report.total_bytes_sent == 1100
    assert report.status_codes[HTTPStatus.OK] == 2
    assert report.status_codes[HTTPStatus.UNAUTHORIZED] == 1
    assert report.top_ips["10.0.0.1"] == 2
    assert len(report.suspicious_ips) == 1
    assert report.suspicious_ips[0].ip_address == "10.0.0.2"
