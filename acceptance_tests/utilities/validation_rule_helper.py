import csv
from pathlib import Path


def get_sample_rows_and_generate_open_validation_rules(sample_file_path: Path):
    sample_header, sample_rows = get_sample_header_and_rows(sample_file_path)

    return sample_rows


def get_sample_header_and_rows(sample_file_path: Path):
    with open(sample_file_path) as sample_file:
        reader = csv.DictReader(sample_file)
        sample_header = reader.fieldnames
        sample_rows = [row for row in reader]
    return sample_header, sample_rows
