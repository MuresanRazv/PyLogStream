import time
import tracemalloc
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass


@dataclass(slots=True)
class BenchmarkResult:
    name: str
    elapsed_seconds: float
    peak_memory_mb: float
    total_items: int = 0

    @property
    def throughput(self) -> float:
        """Calculates items or lines processed per second."""
        if self.elapsed_seconds == 0:
            return 0.0
        return self.total_items / self.elapsed_seconds

    def __str__(self) -> str:
        lines = [
            f"--- Benchmark: {self.name} ---",
            f"Elapsed Time : {self.elapsed_seconds:.4f} s",
            f"Peak Memory  : {self.peak_memory_mb:.2f} MB",
        ]
        if self.total_items > 0:
            lines.append(f"Throughput   : {self.throughput:,.0f} items/s")
        return "\n".join(lines)


@contextmanager
def benchmark(name: str, total_items: int = 0) -> Generator[BenchmarkResult]:
    """Context manager measuring execution time and peak memory footprint."""
    tracemalloc.start()
    start_time = time.perf_counter()

    result = BenchmarkResult(
        name=name, elapsed_seconds=0.0, peak_memory_mb=0.0, total_items=total_items
    )

    try:
        yield result
    finally:
        end_time = time.perf_counter()
        _, peak_bytes = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        result.elapsed_seconds = end_time - start_time
        result.peak_memory_mb = peak_bytes / (1024 * 1024)
