import mmap
import os
from abc import ABC, abstractmethod
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Generic, TypeVar

from log_pipeline.models.logs import LightweightLine
from log_pipeline.parser.utils import find_byte_chunk_offsets

TChunkResult = TypeVar("TChunkResult")
TFinalReport = TypeVar("TFinalReport")


class BaseLogWorker(ABC):
    @staticmethod
    def parse_line(log_line: bytes) -> LightweightLine:
        """Zero-allocation byte-slicing parser for Nginx/Apache logs."""
        ip, _, rest = log_line.partition(b" - - [")
        time_bytes, _, rest = rest.partition(b'] "')
        method, _, rest = rest.partition(b" ")
        endpoint, _, rest = rest.partition(b" HTTP/")
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

    def iterate_chunk(
        self,
        file_path_str: str,
        start_byte: int,
        end_byte: int,
        line_callback: Callable[[LightweightLine], None],
    ) -> int:
        """Helper that memory-maps the slice and executes line_callback on each record."""
        lines_processed = 0
        path = Path(file_path_str)

        with path.open("rb") as f:
            with mmap.mmap(f.fileno(), length=0, access=mmap.ACCESS_READ) as mm:
                mm.seek(start_byte)
                while mm.tell() < end_byte:
                    raw_line = mm.readline()
                    if not raw_line:
                        break
                    try:
                        record = self.parse_line(raw_line)
                        line_callback(record)
                        lines_processed += 1
                    except Exception:
                        continue

        return lines_processed


class BaseParallelProcessor(ABC, Generic[TChunkResult, TFinalReport]):
    """Generic Map-Reduce coordinator across CPU worker processes."""

    def __init__(self, file_path: Path | str, num_workers: int | None = None) -> None:
        self.file_path = Path(file_path)
        self.num_workers = num_workers or (os.cpu_count() or 4)

    @abstractmethod
    def _execute_worker_task(self, start: int, end: int) -> TChunkResult:
        """Dispatched into ProcessPoolExecutor."""

    @abstractmethod
    def _reduce(self, chunk_results: list[TChunkResult]) -> TFinalReport:
        """Merges all worker results into the final aggregated output."""

    def run(self) -> TFinalReport:
        offsets = find_byte_chunk_offsets(self.file_path, self.num_workers)
        if not offsets:
            return self._reduce([])

        with ProcessPoolExecutor(max_workers=self.num_workers) as executor:
            futures = [
                executor.submit(self._execute_worker_task, start, end)
                for start, end in offsets
            ]
            results = [f.result() for f in futures]

        return self._reduce(results)
