import functools
import resource
import time
from collections.abc import Callable
from typing import ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")


def _get_resident_memory_mb() -> float:
    """Returns the process max resident set size (physical RAM) in MB."""
    # resource.getrusage returns maxrss in KiB on Linux, Bytes on macOS
    usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # Check for Linux/Unix standard (KiB) vs macOS (Bytes)
    import sys

    if sys.platform == "darwin":
        return usage / (1024 * 1024)
    return usage / 1024


def profile_performance(
    name: str | None = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator measuring runtime execution time, peak RAM."""

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            label = name or func.__qualname__

            start_mem = _get_resident_memory_mb()
            start_time = time.perf_counter()

            try:
                return func(*args, **kwargs)
            finally:
                elapsed = time.perf_counter() - start_time
                peak_mem = _get_resident_memory_mb()
                mem_diff = max(0.0, peak_mem - start_mem)

                print(f"\n[{label}] Performance Summary:")
                print(f"  • Elapsed Time : {elapsed:.4f}s")
                print(f"  • Peak RAM RSS : {peak_mem:.2f} MB (Delta: +{mem_diff:.2f} MB)")
                print()

        return wrapper

    return decorator
