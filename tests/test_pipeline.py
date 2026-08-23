from pathlib import Path

from pylogstream.generator.service import LogGenerator
from pylogstream.parser.log_parser import LogParser


def test_end_to_end_generate_and_parse_map_reduce(tmp_path: Path) -> None:
    log_file = tmp_path / "e2e_access.log"
    total_lines = 50_000

    # 1. Generate in parallel
    generator = LogGenerator(
        total_lines=total_lines,
        output_path=str(log_file),
        num_workers=2,
    )
    generator.generate()

    # 2. Parse & aggregate in parallel
    parser = LogParser(file_path=log_file, num_workers=2)
    metrics = parser.parse_and_analyze()

    # 3. Assert metrics match input scale
    assert metrics["total_lines"] == total_lines
    assert metrics["total_bytes_sent"] > 0
    assert sum(metrics["status_codes"].values()) == total_lines
    assert len(metrics["top_endpoints"]) > 0
