from dataclasses import dataclass, field


@dataclass(slots=True)
class SuspiciousActor:
    ip: bytes
    reasons: list[str] = field(default_factory=list)
    failed_auth_count: int = 0
    sensitive_path_hits: int = 0
    total_requests: int = 0


@dataclass(slots=True)
class AnomalyScanResult:
    total_lines_scanned: int = 0
    flagged_actors: list[SuspiciousActor] = field(default_factory=list)


@dataclass(slots=True)
class AnomalyThresholds:
    brute_force_limit: int = 25  # Max 401/403 auth failures before flagging
    sensitive_probe_limit: int = 3  # Max hits against honeypot/sensitive paths
    rate_limit: int = 500  # Max total requests within scanned window
