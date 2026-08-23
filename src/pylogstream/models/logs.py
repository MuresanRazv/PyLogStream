from dataclasses import dataclass
from http import HTTPStatus
from typing import NamedTuple


@dataclass(frozen=True, slots=True)
class WeightedHTTPStatus:
    status: HTTPStatus
    weight: float


class LightweightLine(NamedTuple):
    ip: bytes
    timestamp: bytes
    method: bytes
    endpoint: bytes
    status: int
    size: int
