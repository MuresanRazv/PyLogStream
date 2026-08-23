import pytest

from log_pipeline.parser.service import LogParseError, LogParser


def test_parse_valid_combined_line() -> None:
    sample = (
        "192.168.1.42 - - [23/Aug/2026:10:10:47 +0000] "
        '"GET /api/v1/users HTTP/1.1" 200 4096 "-" "Mozilla/5.0"\n'
    )
    entry = LogParser.parse_line(sample)

    assert entry.ip_address == "192.168.1.42"
    assert entry.timestamp.isoformat() == "2026-08-23T10:10:47+00:00"
    assert entry.endpoint == "/api/v1/users"
    assert entry.http_status.value == 200
    assert entry.response_size == 4096
    assert entry.http_method.name == "GET"
    assert entry.referer == "-"
    assert entry.user_agent == "Mozilla/5.0"


def test_parse_invalid_combined_line() -> None:
    invalid_sample = "Invalid random string that does not match log schema"

    with pytest.raises(LogParseError):
        LogParser.parse_line(invalid_sample)
