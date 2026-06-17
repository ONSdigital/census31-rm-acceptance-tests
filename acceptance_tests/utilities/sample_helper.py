import csv
from pathlib import Path
from typing import List


def read_sample(sample_file_path: Path, validation_rules: List, delimiter=',') -> List:
    sample_columns = {column['columnName']: column for column in validation_rules}
    with open(sample_file_path) as f:
        sample_reader = csv.DictReader(f, delimiter=delimiter)
        raw_sample = [row for row in sample_reader]

    sample = []
    for row in raw_sample:
        sample_row = {'sample': {}, 'sensitive': {}}
        for field, value in row.items():
            if sample_columns[field].get('sensitive'):
                sample_row['sensitive'][field] = value
            else:
                sample_row['sample'][field] = value
        sample.append(sample_row)

    return sample
