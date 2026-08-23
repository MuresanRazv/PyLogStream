import argparse
from pathlib import Path

from log_pipeline.generator.anomalies import (
    inject_anomaly,
    should_inject_anomaly,
)
from log_pipeline.generator.constants import (
    ANOMALY_BATCH_SIZE,
    DEFAULT_LINES_TO_GENERATE,
    DEFAULT_OUTPUT_PATH,
)
from log_pipeline.generator.formatter import generate_log_line


class LogGenerator:
    def __init__(
        self,
        total_lines: int = DEFAULT_LINES_TO_GENERATE,
        output_path: str = DEFAULT_OUTPUT_PATH,
        batch_size: int = 10000,
    ) -> None:
        self.total_lines = total_lines
        self.output_path = Path(output_path)
        self.batch_size = batch_size

    def _append_log_line(self, log_line: str, buffer: list[str], file) -> None:
        buffer.append(log_line)
        if len(buffer) >= self.batch_size:
            file.writelines(buffer)
            buffer.clear()

    def generate(self) -> None:
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        buffer: list[str] = []
        lines_generated = 0

        with self.output_path.open("w") as file:
            while lines_generated < self.total_lines:
                if (
                    should_inject_anomaly()
                    and lines_generated + ANOMALY_BATCH_SIZE <= self.total_lines
                ):
                    anomaly = inject_anomaly(generate_log_line())
                    [
                        self._append_log_line(log_line, buffer, file)
                        for log_line in [
                            str(anomaly) for _ in range(ANOMALY_BATCH_SIZE)
                        ]
                    ]
                    lines_generated += ANOMALY_BATCH_SIZE
                else:
                    log_line = generate_log_line()
                    self._append_log_line(str(log_line), buffer, file)
                    lines_generated += 1
            if buffer:
                file.writelines(buffer)


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic log lines.")
    parser.add_argument(
        "--lines",
        type=int,
        default=DEFAULT_LINES_TO_GENERATE,
        help=f"""
            Total number of log lines to generate",
            (default: {DEFAULT_LINES_TO_GENERATE}),
        """,
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
    print(f"Generated {args.lines} log lines and saved to {args.output}")


if __name__ == "__main__":
    main()
