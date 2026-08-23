from pathlib import Path

from pylogstream.parser.log_parser import ChunkMetrics, LogParser, LogParserWorker


def test_worker_parse_chunk_and_skip_malformed(tmp_path: Path) -> None:
    test_file = tmp_path / "slice_metrics.log"
    content = (
        b'192.168.1.1 - - [23/Aug/2026:10:00:00 +0000] "GET /api/users HTTP/1.1" 200 100 "-" "-"\n'
        b"MALFORMED GARBAGE LINE THAT SHOULD BE SKIPPED SAFELY\n"
        b'192.168.1.2 - - [23/Aug/2026:10:00:01 +0000] "POST /api/login HTTP/1.1" 500 250 "-" "-"\n'
    )
    test_file.write_bytes(content)

    worker = LogParserWorker()
    result = worker.parse_chunk(str(test_file), 0, test_file.stat().st_size)

    assert isinstance(result, ChunkMetrics)
    assert result.total_lines == 2
    assert result.total_bytes == 350
    assert result.status_codes[200] == 1
    assert result.status_codes[500] == 1
    assert result.top_endpoints[b"/api/users"] == 1


def test_log_parser_parallel_integration(tmp_path: Path) -> None:
    test_file = tmp_path / "full_run.log"
    line_ok = b'192.168.1.1 - - [23/Aug/2026:10:00:00 +0000] "GET /home HTTP/1.1" 200 500 "-" "-"\n'
    line_err = b'192.168.1.2 - - [23/Aug/2026:10:00:01 +0000] "GET /missing HTTP/1.1" 404 150 "-" "-"\n'

    test_file.write_bytes((line_ok * 600) + (line_err * 400))

    parser = LogParser(file_path=test_file, num_workers=2)
    report = parser.parse_and_analyze()

    assert report["total_lines"] == 1000
    assert report["total_bytes_sent"] == (600 * 500) + (400 * 150)
    assert report["status_codes"][200] == 600
    assert report["status_codes"][404] == 400
    assert dict(report["top_endpoints"])[b"/home"] == 600
