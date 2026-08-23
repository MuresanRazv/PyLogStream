from collections import Counter
from typing import NamedTuple

from log_pipeline.benchmark.decorators import profile_performance
from log_pipeline.models.logs import LightweightLine
from log_pipeline.parser.base import BaseLogWorker, BaseParallelProcessor


class ChunkMetrics(NamedTuple):
    total_lines: int
    total_bytes: int
    status_codes: Counter[int]
    top_endpoints: Counter[bytes]


class LogParserWorker(BaseLogWorker):
    def parse_chunk(
        self, file_path_str: str, start_byte: int, end_byte: int
    ) -> ChunkMetrics:
        total_bytes = 0
        status_counts: Counter[int] = Counter()
        endpoint_counts: Counter[bytes] = Counter()

        def on_line(record: LightweightLine) -> None:
            nonlocal total_bytes
            total_bytes += record.size
            status_counts[record.status] += 1
            endpoint_counts[record.endpoint] += 1

        total_lines = self.iterate_chunk(file_path_str, start_byte, end_byte, on_line)
        return ChunkMetrics(total_lines, total_bytes, status_counts, endpoint_counts)


class LogParser(BaseParallelProcessor[ChunkMetrics, dict]):
    def _execute_worker_task(self, start: int, end: int) -> ChunkMetrics:
        return LogParserWorker().parse_chunk(str(self.file_path), start, end)

    def _reduce(self, chunk_results: list[ChunkMetrics]) -> dict:
        total_lines = sum(c.total_lines for c in chunk_results)
        total_bytes = sum(c.total_bytes for c in chunk_results)
        status_totals: Counter[int] = Counter()
        endpoint_totals: Counter[bytes] = Counter()

        for c in chunk_results:
            status_totals.update(c.status_codes)
            endpoint_totals.update(c.top_endpoints)

        return {
            "total_lines": total_lines,
            "total_bytes_sent": total_bytes,
            "status_codes": status_totals,
            "top_endpoints": endpoint_totals.most_common(5),
        }

    @profile_performance(name="Parallel Fast Parsing & Aggregation")
    def parse_and_analyze(self) -> dict:
        return self.run()
