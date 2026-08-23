from log_pipeline.generator.service import LogGenerator


def test_generator_service_writes_correct_line_count(tmp_path):
    total_lines = 1000
    output_file = tmp_path / "test_logs.log"

    generator = LogGenerator(total_lines=total_lines, output_path=str(output_file))
    generator.generate()

    assert output_file.exists(), f"Output file {output_file} does not exist"

    with open(output_file) as f:
        lines = f.readlines()

    assert len(lines) == total_lines
