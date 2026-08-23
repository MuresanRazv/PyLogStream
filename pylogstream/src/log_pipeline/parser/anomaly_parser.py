from collections import Counter
from pathlib import Path
from typing import NamedTuple

from log_pipeline.benchmark.decorators import profile_performance
from log_pipeline.constants import ANOMALY_ENDPOINTS
from log_pipeline.models.logs import LightweightLine
from log_pipeline.parser.base import BaseLogWorker, BaseParallelProcessor
from log_pipeline.parser.models import AnomalyScanResult, SuspiciousActor


class AnomalyChunkResult(NamedTuple):
    total_lines: int
    requests: Counter[bytes]
    failed_auth: Counter[bytes]
    probes: Counter[bytes]


class AnomalyParserWorker(BaseLogWorker):
    def scan_chunk(
        self, file_path_str: str, start_byte: int, end_byte: int
    ) -> AnomalyChunkResult:
        requests_per_ip: Counter[bytes] = Counter()
        failed_auth_per_ip: Counter[bytes] = Counter()
        probes_per_ip: Counter[bytes] = Counter()

        def on_line(record: LightweightLine) -> None:
            requests_per_ip[record.ip] += 1
            if record.status in (401, 403):
                failed_auth_per_ip[record.ip] += 1
            if any(endpoint in record.endpoint for endpoint in ANOMALY_ENDPOINTS):
                probes_per_ip[record.ip] += 1

        total_lines = self.iterate_chunk(file_path_str, start_byte, end_byte, on_line)
        return AnomalyChunkResult(
            total_lines, requests_per_ip, failed_auth_per_ip, probes_per_ip
        )


class AnomalyParser(BaseParallelProcessor[AnomalyChunkResult, AnomalyScanResult]):
    def __init__(
        self,
        file_path: Path | str,
        brute_force_limit: int = 25,
        sensitive_probe_limit: int = 3,
        rate_limit: int = 500,
        num_workers: int | None = None,
    ) -> None:
        super().__init__(file_path, num_workers)
        self.brute_force_limit = brute_force_limit
        self.sensitive_probe_limit = sensitive_probe_limit
        self.rate_limit = rate_limit

    def _execute_worker_task(self, start: int, end: int) -> AnomalyChunkResult:
        return AnomalyParserWorker().scan_chunk(str(self.file_path), start, end)

    def _reduce(self, chunk_results: list[AnomalyChunkResult]) -> AnomalyScanResult:
        total_lines = sum(c.total_lines for c in chunk_results)
        global_requests: Counter[bytes] = Counter()
        global_failed_auth: Counter[bytes] = Counter()
        global_probes: Counter[bytes] = Counter()

        for c in chunk_results:
            global_requests.update(c.requests)
            global_failed_auth.update(c.failed_auth)
            global_probes.update(c.probes)

        suspects: dict[bytes, SuspiciousActor] = {}

        for ip, count in global_failed_auth.items():
            if count >= self.brute_force_limit:
                actor = suspects.setdefault(ip, SuspiciousActor(ip=ip))
                actor.failed_auth_count = count
                actor.reasons.append(f"Brute Force Attempt ({count} failed auths)")

        for ip, count in global_probes.items():
            if count >= self.sensitive_probe_limit:
                actor = suspects.setdefault(ip, SuspiciousActor(ip=ip))
                actor.sensitive_path_hits = count
                actor.reasons.append(f"Vulnerability Probes ({count} hits)")

        for ip, count in global_requests.items():
            if count >= self.rate_limit:
                actor = suspects.setdefault(ip, SuspiciousActor(ip=ip))
                actor.reasons.append(f"High-Rate Scanner ({count} requests)")

        for ip, actor in suspects.items():
            actor.total_requests = global_requests[ip]

        return AnomalyScanResult(
            total_lines_scanned=total_lines, flagged_actors=list(suspects.values())
        )

    @profile_performance(name="Multi-Core Threat Detection Scan")
    def detect_attackers(self) -> AnomalyScanResult:
        return self.run()
