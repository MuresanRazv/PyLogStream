from datetime import datetime

import pytz


def parse_timestamp(timestamp_str: str) -> datetime:
    return datetime.strptime(timestamp_str, "%d/%b/%Y:%H:%M:%S %z").replace(
        tzinfo=pytz.utc
    )
