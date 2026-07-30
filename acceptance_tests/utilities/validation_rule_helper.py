import csv
from pathlib import Path


def get_sample_rows_and_generate_open_validation_rules(sample_file_path: Path, delimiter: str = '|'):
    sample_header, sample_rows = get_sample_header_and_rows(sample_file_path, delimiter=delimiter)

    return sample_rows


def get_sample_header_and_rows(sample_file_path: Path, delimiter: str):
    with open(sample_file_path) as sample_file:
        reader = csv.DictReader(sample_file, delimiter=delimiter)
        sample_header = reader.fieldnames
        sample_rows = [row for row in reader]
    return sample_header, sample_rows
