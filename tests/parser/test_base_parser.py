from pathlib import Path

from pylogstream.models.logs import LightweightLine
from pylogstream.parser.base import BaseLogWorker
from pylogstream.parser.utils import find_byte_chunk_offsets


def test_base_worker_parse_line_valid() -> None:
    sample_line = (
        b"192.168.1.50 - - [23/Aug/2026:10:15:30 +0000] "
        b'"GET /api/v1/checkout HTTP/1.1" 200 4096 "-" "Mozilla/5.0"\n'
    )

    record = BaseLogWorker.parse_line(sample_line)

    assert isinstance(record, LightweightLine)
    assert record.ip == b"192.168.1.50"
    assert record.timestamp == b"23/Aug/2026:10:15:30 +0000"
    assert record.method == b"GET"
    assert record.endpoint == b"/api/v1/checkout"
    assert record.status == 200
    assert record.size == 4096


def test_find_byte_chunk_offsets_aligns_to_newlines(tmp_path: Path) -> None:
    test_file = tmp_path / "test_chunks.log"
    line = b'192.168.1.1 - - [23/Aug/2026:10:00:00 +0000] "GET / HTTP/1.1" 200 500 "-" "-"\n'

    # Write 300 lines across multiple chunks
    test_file.write_bytes(line * 300)
    total_size = test_file.stat().st_size

    offsets = find_byte_chunk_offsets(test_file, num_chunks=4)

    assert len(offsets) == 4
    assert offsets[0][0] == 0
    assert offsets[-1][1] == total_size

    # Verify every boundary ends on a newline
    with test_file.open("rb") as f:
        for _, end in offsets:
            if end < total_size:
                f.seek(end - 1)
                assert f.read(1) == b"\n", f"Offset end {end} not aligned to newline"


def test_find_byte_chunk_offsets_empty_file(tmp_path: Path) -> None:
    empty_file = tmp_path / "empty.log"
    empty_file.touch()

    offsets = find_byte_chunk_offsets(empty_file, num_chunks=4)
    assert offsets == []
