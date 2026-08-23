import mmap
import os
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from log_pipeline.benchmark.decorators import profile_performance
from log_pipeline.models.logs import LightweightLine


class LogParseError(Exception):
    """Raised when a log line fails format matching or field conversion."""


class LogParserWorker:
    @staticmethod
    def parse_line(log_line: bytes) -> LightweightLine:
        """Zero-allocation parser extracting fields using C-speed byte slicing.

        Expected format:
        IP - - [TIME] "METHOD PATH HTTP/1.1" STATUS BYTES "REF" "UA"
        """

        # 1. IP and Timestamp
        ip, _, rest = log_line.partition(b" - - [")
        time_bytes, _, rest = rest.partition(b'] "')

        # 2. HTTP Method and Request URI
        method, _, rest = rest.partition(b" ")
        endpoint, _, rest = rest.partition(b" HTTP/")

        # 3. Status and Size
        _, _, rest = rest.partition(b'" ')
        status_bytes, _, rest = rest.partition(b" ")
        size_bytes, _, _ = rest.partition(b' "')

        return LightweightLine(
            ip=ip,
            timestamp=time_bytes,
            method=method,
            endpoint=endpoint,
            status=int(status_bytes),
            size=int(size_bytes),
        )

    def parse_file(
        self,
        file_path_str: str,
        start_byte: int,
        end_byte: int,
    ) -> tuple[int, int, Counter[int], Counter[bytes]]:
        """Worker processing a memory-mapped byte range."""
        path = Path(file_path_str)

        total_lines = 0
        total_bytes = 0
        status_counts: Counter[int] = Counter()
        endpoint_counts: Counter[bytes] = Counter()

        with path.open("rb") as f:
            # Memory-map the file
            with mmap.mmap(f.fileno(), length=0, access=mmap.ACCESS_READ) as mm:
                mm.seek(start_byte)

                while mm.tell() < end_byte:
                    line = mm.readline()
                    if not line:
                        break

                    try:
                        record = self.parse_line(line)
                        total_lines += 1
                        total_bytes += record.size
                        status_counts[record.status] += 1
                        endpoint_counts[record.endpoint] += 1
                    except Exception:
                        continue  # Ignore empty or malformed boundary lines

        return total_lines, total_bytes, status_counts, endpoint_counts


class LogParser:
    def __init__(self, file_path: Path | str, num_workers: int | None = None) -> None:
        self.file_path = Path(file_path)
        self.num_workers = num_workers or (os.cpu_count() or 4)

    def _find_byte_chunk_offsets(
        self, file_path: Path, num_chunks: int
    ) -> list[tuple[int, int]]:
        """Calculates (start_byte, end_byte) boundaries aligned to newline boundaries."""
        total_size = file_path.stat().st_size
        chunk_size = total_size // num_chunks
        offsets: list[tuple[int, int]] = []

        with file_path.open("rb") as f:
            current_start = 0

            for i in range(num_chunks):
                if i == num_chunks - 1:
                    # Final chunk takes remainder to EOF
                    offsets.append((current_start, total_size))
                    break

                target_end = current_start + chunk_size
                f.seek(target_end)

                # Advance to the end of the current line
                _ = f.readline()
                actual_end = f.tell()

                offsets.append((current_start, actual_end))
                current_start = actual_end

        return offsets

    @profile_performance(name="Parallel Fast Parsing & Aggregation")
    def parse_and_analyze(self) -> dict:
        offsets = self._find_byte_chunk_offsets(self.file_path, self.num_workers)

        total_lines = 0
        total_bytes = 0
        status_totals: Counter[int] = Counter()
        endpoint_totals: Counter[bytes] = Counter()

        # Distribute chunks across CPU cores
        with ProcessPoolExecutor(max_workers=self.num_workers) as executor:
            futures = [
                executor.submit(
                    LogParserWorker().parse_file,
                    str(self.file_path),
                    start,
                    end,
                )
                for start, end in offsets
            ]

            # Merge partial reports (Map-Reduce step)
            for fut in futures:
                lines, bytes_sent, statuses, endpoints = fut.result()
                total_lines += lines
                total_bytes += bytes_sent
                status_totals.update(statuses)
                endpoint_totals.update(endpoints)

        return {
            "total_lines": total_lines,
            "total_bytes_sent": total_bytes,
            "status_codes": status_totals,
            "top_endpoints": endpoint_totals.most_common(5),
        }


def main():
    @profile_performance(name="Log Parsing")
    def parse():
        log_parser = LogParser("logs.txt")
        try:
            print(log_parser.parse_and_analyze())
        except LogParseError as e:
            print(f"Failed to parse log file: {e}")

    parse()


if __name__ == "__main__":
    main()
