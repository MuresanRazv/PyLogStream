from pathlib import Path

from log_pipeline.models.logs import LightweightLine
from log_pipeline.parser.service import LogParser, LogParserWorker

# --- 1. Unit Tests: Single Line Byte Slicing ---


def test_worker_parse_line_valid() -> None:
    sample_line = (
        b"192.168.1.50 - - [23/Aug/2026:10:15:30 +0000] "
        b'"GET /api/v1/checkout HTTP/1.1" 200 4096 "-" "Mozilla/5.0"\n'
    )

    record = LogParserWorker.parse_line(sample_line)

    assert isinstance(record, LightweightLine)
    assert record.ip == b"192.168.1.50"
    assert record.timestamp == b"23/Aug/2026:10:15:30 +0000"
    assert record.method == b"GET"
    assert record.endpoint == b"/api/v1/checkout"
    assert record.status == 200
    assert record.size == 4096


def test_worker_parse_line_different_methods_and_statuses() -> None:
    sample_post = (
        b"10.0.0.1 - - [23/Aug/2026:10:16:00 +0000] "
        b'"POST /api/v1/auth/login HTTP/1.1" 401 128 "https://google.com" "curl/7.68.0"\n'
    )

    record = LogParserWorker.parse_line(sample_post)

    assert record.ip == b"10.0.0.1"
    assert record.method == b"POST"
    assert record.endpoint == b"/api/v1/auth/login"
    assert record.status == 401
    assert record.size == 128


# --- 2. Unit Tests: Chunker Boundary Alignment ---


def test_find_byte_chunk_offsets_aligns_to_newlines(tmp_path: Path) -> None:
    test_file = tmp_path / "test_chunks.log"
    line = b'192.168.1.1 - - [23/Aug/2026:10:00:00 +0000] "GET / HTTP/1.1" 200 500 "-" "-"\n'

    # Write 300 lines to ensure multiple chunks
    test_file.write_bytes(line * 300)
    total_size = test_file.stat().st_size

    parser = LogParser(file_path=test_file, num_workers=4)
    offsets = parser._find_byte_chunk_offsets(test_file, num_chunks=4)

    assert len(offsets) == 4
    assert offsets[0][0] == 0
    assert offsets[-1][1] == total_size

    # Ensure each chunk boundary (except start at 0) ends precisely on a newline
    with test_file.open("rb") as f:
        for start, end in offsets:
            if end < total_size:
                f.seek(end - 1)
                assert f.read(1) == b"\n", (
                    f"Offset end {end} is not positioned at a newline"
                )


# --- 3. Integration Tests: Worker Slice & Aggregation ---


def test_worker_parse_file_slice_and_skips_malformed(tmp_path: Path) -> None:
    test_file = tmp_path / "slice_test.log"
    content = (
        b'192.168.1.1 - - [23/Aug/2026:10:00:00 +0000] "GET /api/users HTTP/1.1" 200 100 "-" "-"\n'
        b"MALFORMED GARBAGE LINE THAT SHOULD BE SKIPPED SAFELY\n"
        b'192.168.1.2 - - [23/Aug/2026:10:00:01 +0000] "POST /api/login HTTP/1.1" 500 250 "-" "-"\n'
    )
    test_file.write_bytes(content)
    total_size = test_file.stat().st_size

    worker = LogParserWorker()
    lines, bytes_sent, statuses, endpoints = worker.parse_file(
        str(test_file),
        start_byte=0,
        end_byte=total_size,
    )

    # Malformed line is ignored by the try/except block
    assert lines == 2
    assert bytes_sent == 350
    assert statuses[200] == 1
    assert statuses[500] == 1
    assert endpoints[b"/api/users"] == 1
    assert endpoints[b"/api/login"] == 1


# --- 4. End-to-End Parallel Integration Test ---


def test_parse_and_analyze_multiprocess(tmp_path: Path) -> None:
    test_file = tmp_path / "full_run.log"

    line_ok = b'192.168.1.1 - - [23/Aug/2026:10:00:00 +0000] "GET /home HTTP/1.1" 200 500 "-" "-"\n'
    line_err = b'192.168.1.2 - - [23/Aug/2026:10:00:01 +0000] "GET /missing HTTP/1.1" 404 150 "-" "-"\n'

    # 500 OK lines + 200 404 lines = 700 total
    test_file.write_bytes((line_ok * 500) + (line_err * 200))

    parser = LogParser(file_path=test_file, num_workers=2)
    results = parser.parse_and_analyze()

    assert results["total_lines"] == 700
    assert results["total_bytes_sent"] == (500 * 500) + (200 * 150)
    assert results["status_codes"][200] == 500
    assert results["status_codes"][404] == 200

    top_endpoints = dict(results["top_endpoints"])
    assert top_endpoints[b"/home"] == 500
    assert top_endpoints[b"/missing"] == 200
