import datetime
from dataclasses import dataclass
from http import HTTPMethod, HTTPStatus
from typing import NamedTuple


@dataclass(frozen=True, slots=True)
class WeightedHTTPStatus:
    status: HTTPStatus
    weight: float


@dataclass(frozen=True, slots=True)
class LogLine:
    ip_address: str
    timestamp: datetime.datetime
    endpoint: str
    http_status: HTTPStatus
    http_method: HTTPMethod
    referer: str
    user_agent: str
    response_size: int

    def __str__(self) -> str:
        # Format timestamp to: DD/Mon/YYYY:HH:MM:SS +0000
        formatted_time = self.timestamp.strftime("%d/%b/%Y:%H:%M:%S %z")

        return (
            f"{self.ip_address} - - [{formatted_time}] "
            f'"{self.http_method} {self.endpoint} HTTP/1.1" '
            f"{self.http_status.value} {self.response_size} "
            f'"{self.referer}" "{self.user_agent}"\n'
        )


class LightweightLine(NamedTuple):
    ip: bytes
    timestamp: bytes
    method: bytes
    endpoint: bytes
    status: int
    size: int
