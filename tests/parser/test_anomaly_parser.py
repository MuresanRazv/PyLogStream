from pathlib import Path

from pylogstream.parser.anomaly_parser import (
    AnomalyChunkResult,
    AnomalyParser,
    AnomalyParserWorker,
)


def test_anomaly_worker_scan_chunk(tmp_path: Path) -> None:
    test_file = tmp_path / "threat_chunk.log"
    content = (
        b'10.0.0.99 - - [23/Aug/2026:10:00:00 +0000] "GET /.env HTTP/1.1" 404 120 "-" "-"\n'
        b'10.0.0.99 - - [23/Aug/2026:10:00:01 +0000] "POST /api/login HTTP/1.1" 401 80 "-" "-"\n'
        b'192.168.1.5 - - [23/Aug/2026:10:00:02 +0000] "GET /index.html HTTP/1.1" 200 1500 "-" "-"\n'
    )
    test_file.write_bytes(content)

    worker = AnomalyParserWorker()
    chunk_res = worker.scan_chunk(str(test_file), 0, test_file.stat().st_size)

    assert isinstance(chunk_res, AnomalyChunkResult)
    assert chunk_res.total_lines == 3
    assert chunk_res.requests[b"10.0.0.99"] == 2
    assert chunk_res.failed_auth[b"10.0.0.99"] == 1
    assert chunk_res.probes[b"10.0.0.99"] == 1
    assert chunk_res.requests[b"192.168.1.5"] == 1


def test_anomaly_detector_detects_brute_force_and_probes(tmp_path: Path) -> None:
    test_file = tmp_path / "multi_threat.log"

    # Attacker 1: Brute-force auth
    bf_line = b'10.0.0.100 - - [23/Aug/2026:10:00:00 +0000] "POST /login HTTP/1.1" 401 100 "-" "-"\n'
    # Attacker 2: Sensitive path probes
    probe_line = b'10.0.0.200 - - [23/Aug/2026:10:00:00 +0000] "GET /wp-admin HTTP/1.1" 404 150 "-" "-"\n'
    # Legitimate traffic
    normal_line = b'192.168.1.1 - - [23/Aug/2026:10:00:00 +0000] "GET /products HTTP/1.1" 200 500 "-" "-"\n'

    content = (bf_line * 30) + (probe_line * 5) + (normal_line * 50)
    test_file.write_bytes(content)

    detector = AnomalyParser(
        file_path=test_file,
        brute_force_limit=20,
        sensitive_probe_limit=3,
        rate_limit=200,
        num_workers=2,
    )
    result = detector.detect_attackers()

    assert result.total_lines_scanned == 85
    assert len(result.flagged_actors) == 2

    actors_map = {actor.ip: actor for actor in result.flagged_actors}

    # Verify Attacker 1
    assert b"10.0.0.100" in actors_map
    assert actors_map[b"10.0.0.100"].failed_auth_count == 30
    assert any("Brute Force" in r for r in actors_map[b"10.0.0.100"].reasons)

    # Verify Attacker 2
    assert b"10.0.0.200" in actors_map
    assert actors_map[b"10.0.0.200"].sensitive_path_hits == 5
    assert any("Vulnerability Probes" in r for r in actors_map[b"10.0.0.200"].reasons)
