import json
from typing import List


def parse_array_to_list(text: str) -> List:
    parsed_array = json.loads(text)
    if not isinstance(parsed_array, List):
        raise ValueError(f'Parameter {text} is not a JSON array')
    return parsed_array


def parse_json_object(text: str):
    parsed = json.loads(text)
    if isinstance(parsed, str):
        # Plain strings should not be passed through using JSON type
        raise ValueError(f'Parameter {text} is a plain string, not a JSON object')
    return parsed
