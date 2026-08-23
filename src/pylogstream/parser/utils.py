from datetime import datetime
from pathlib import Path


def parse_timestamp(timestamp_str: str) -> datetime:
    return datetime.strptime(timestamp_str, "%d/%b/%Y:%H:%M:%S %z")


def find_byte_chunk_offsets(file_path: Path, num_chunks: int) -> list[tuple[int, int]]:
    """Calculates (start_byte, end_byte) boundaries snapped to the nearest newline."""
    total_size = file_path.stat().st_size
    if total_size == 0:
        return []

    chunk_size = max(1, total_size // num_chunks)
    offsets: list[tuple[int, int]] = []

    with file_path.open("rb") as f:
        current_start = 0

        for i in range(num_chunks):
            if i == num_chunks - 1:
                offsets.append((current_start, total_size))
                break

            f.seek(current_start + chunk_size)
            _ = f.readline()
            actual_end = f.tell()

            offsets.append((current_start, actual_end))
            current_start = actual_end

    return offsets
