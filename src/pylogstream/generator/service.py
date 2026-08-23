import argparse
import os
import random
import shutil
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from pylogstream.benchmark.decorators import profile_performance
from pylogstream.constants import (
    ANOMALY_BATCH_SIZE,
    ANOMALY_ENDPOINTS,
    ANOMALY_STATUS_CODES,
    DEFAULT_LINES_TO_GENERATE,
    DEFAULT_OUTPUT_PATH,
    HTTP_ENDPOINTS,
    HTTP_METHODS,
    HTTP_REFERERS,
    HTTP_STATUS_CODES,
    HTTP_USER_AGENTS,
)
from pylogstream.generator.utils import should_inject_anomaly


class LogGeneratorWorker:
    def __init__(
        self,
        worker_id: int,
        lines_to_generate: int,
        output_path: Path,
        chunk_lines: int = 50_000,
    ) -> None:
        self.worker_id = worker_id
        self.lines_to_generate = lines_to_generate
        self.output_path = output_path
        self.chunk_lines = chunk_lines

    def _construct_line(
        self,
        ip: bytes,
        current_time: bytes,
        method: bytes,
        endpoint: bytes,
        status: bytes,
        size: bytes,
        ref: bytes,
        ua: bytes,
    ) -> bytes:
        return b'%b - - [%b] "%b %b HTTP/1.1" %b %b "%b" "%b"\n' % (
            ip,
            current_time,
            method,
            endpoint,
            status,
            size,
            ref,
            ua,
        )

    def generate(self) -> Path:
        """Worker process that writes raw pre-encoded bytes directly to disk."""
        current_time_bytes = time.strftime("%d/%b/%Y:%H:%M:%S +0000").encode("ascii")
        ip_pool = [f"192.168.1.{i}".encode("ascii") for i in range(1, 255)]

        lines_written = 0
        anomaly_lines_to_buffer = 0
        buffer: list[bytes] = []

        # Pre-encoded anomaly choices
        anomaly_endpoints = [
            e.encode("ascii") if isinstance(e, str) else e for e in ANOMALY_ENDPOINTS
        ]
        anomaly_statuses = [
            str(s.value).encode("ascii") if hasattr(s, "value") else str(s).encode("ascii")
            for s in ANOMALY_STATUS_CODES
        ]
        referers = [r.encode("ascii") if isinstance(r, str) else r for r in HTTP_REFERERS]
        user_agents = [u.encode("ascii") if isinstance(u, str) else u for u in HTTP_USER_AGENTS]

        with self.output_path.open("wb", buffering=2 * 1024 * 1024) as file:
            while lines_written < self.lines_to_generate:
                batch_count = min(self.chunk_lines, self.lines_to_generate - lines_written)

                # Generate attacker identity for the burst
                attacker_ip = f"10.0.0.{random.randint(1, 255)}".encode("ascii")
                attacker_method = random.choice(HTTP_METHODS)
                attacker_endpoint = random.choice(anomaly_endpoints)
                attacker_status = random.choice(anomaly_statuses)
                attacker_ref = random.choice(referers)
                attacker_ua = random.choice(user_agents)

                for _ in range(batch_count):
                    if anomaly_lines_to_buffer == 0 and should_inject_anomaly():
                        anomaly_lines_to_buffer = ANOMALY_BATCH_SIZE

                    if anomaly_lines_to_buffer > 0:
                        size = str(random.randint(20, 5000)).encode("ascii")
                        buffer.append(
                            self._construct_line(
                                attacker_ip,
                                current_time_bytes,
                                attacker_method,
                                attacker_endpoint,
                                attacker_status,
                                size,
                                attacker_ref,
                                attacker_ua,
                            )
                        )
                        anomaly_lines_to_buffer -= 1
                    else:
                        size = str(random.randint(200, 8000)).encode("ascii")
                        buffer.append(
                            self._construct_line(
                                random.choice(ip_pool),
                                current_time_bytes,
                                random.choice(HTTP_METHODS),
                                random.choice(HTTP_ENDPOINTS),
                                random.choice(HTTP_STATUS_CODES),
                                size,
                                random.choice(referers),
                                random.choice(user_agents),
                            )
                        )

                # Single write call per batch
                file.write(b"".join(buffer))
                buffer.clear()
                lines_written += batch_count

        return self.output_path


class LogGenerator:
    def __init__(
        self,
        total_lines: int = DEFAULT_LINES_TO_GENERATE,
        output_path: Path | str = DEFAULT_OUTPUT_PATH,
        num_workers: int | None = None,
    ) -> None:
        self.total_lines = total_lines
        self.output_path = Path(output_path)
        self.num_workers = num_workers or (os.cpu_count() or 4)

    @profile_performance(name="Parallel Binary Log Generation")
    def generate(self) -> None:
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        temp_dir = self.output_path.parent / "_chunks"
        temp_dir.mkdir(parents=True, exist_ok=True)

        lines_per_worker = self.total_lines // self.num_workers
        remainder = self.total_lines % self.num_workers

        tasks = []
        chunk_files: list[Path] = []

        with ProcessPoolExecutor(max_workers=self.num_workers) as executor:
            for i in range(self.num_workers):
                count = lines_per_worker + (remainder if i == 0 else 0)
                chunk_file = temp_dir / f"chunk_{i}.log"
                chunk_files.append(chunk_file)

                worker = LogGeneratorWorker(
                    worker_id=i,
                    lines_to_generate=count,
                    output_path=chunk_file,
                )
                tasks.append(executor.submit(worker.generate))

            # Wait for all workers to complete
            for task in tasks:
                task.result()

        # Concatenate worker files into the final destination
        print(self.output_path)
        with self.output_path.open("wb") as out_f:
            for chunk_file in chunk_files:
                with chunk_file.open("rb") as in_f:
                    shutil.copyfileobj(in_f, out_f, length=4 * 1024 * 1024)

        # Cleanup chunk files
        shutil.rmtree(temp_dir)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic log lines.")
    parser.add_argument(
        "--lines",
        type=int,
        default=DEFAULT_LINES_TO_GENERATE,
        help=f"Total number of log lines to generate (default: {DEFAULT_LINES_TO_GENERATE})",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=DEFAULT_OUTPUT_PATH,
        help=f"Output file path (default: {DEFAULT_OUTPUT_PATH})",
    )
    args = parser.parse_args()

    generator = LogGenerator(total_lines=args.lines, output_path=args.output)
    generator.generate()
    print(f"Generated {args.lines:,} log lines and saved to {args.output}")


if __name__ == "__main__":
    main()
