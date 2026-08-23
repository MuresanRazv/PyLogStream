import random
from datetime import datetime
from http import HTTPMethod

import pytz

from log_pipeline.generator.constants import ANOMALY_ENDPOINTS
from log_pipeline.generator.utils import (
    generate_ipv4_address,
    get_weighted_random_http_status,
)
from log_pipeline.models.logs import LogLine


def generate_log_line() -> LogLine:
    log_line = LogLine(
        ip_address=generate_ipv4_address(),
        timestamp=datetime.now(pytz.utc),  # Current UTC time
        endpoint=str(random.choice(ANOMALY_ENDPOINTS)),
        http_status=get_weighted_random_http_status(),
        response_size=random.randint(
            100, 5000
        ),  # Random response size between 100 and 5000 bytes
        http_method=random.choice(list(HTTPMethod)),  # Random HTTP method
        referer=random.choice(
            [
                "https://www.google.com",
                "https://www.bing.com",
                "https://www.yahoo.com",
                "https://www.example.com",
                "https://www.test.com",
            ]
        ),
        user_agent=random.choice(
            [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.96 Safari/537.36",
                "Mozilla/5.0 (iPhone; CPU iPhone OS 14_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
                "Mozilla/5.0 (iPad; CPU OS 14_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
            ]
        ),
    )
    return log_line
