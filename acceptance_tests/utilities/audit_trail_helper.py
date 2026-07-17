import logging
import random
import string
from pathlib import Path
from typing import Dict, List

from structlog import wrap_logger

logger = wrap_logger(logging.getLogger(__name__))


def get_unique_user_email():
    name_part = ''.join(random.choices(string.ascii_lowercase, k=5))
    domain_part = ''.join(random.choices(string.ascii_lowercase, k=5))
    tld_part = ''.join(random.choices(["com", "org", "gov.uk", "io"]))
    return f'{name_part}@{domain_part}.{tld_part}'


def get_random_alpha_numerics(length=4):
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))


def log_out_user_context_values(context, context_attributes: List[Dict]):
    logger.error('Outputting user context vars')
    context_output = build_context_audit_log(context, context_attributes)

    logger.error(context_output)

def add_random_suffix_to_email(email_address):
    return f'{email_address}@{get_random_alpha_numerics(4)}'


def build_context_audit_log(context, context_attributes: List[Dict]) -> str:
    context_output = "\n"

    for context_attribute in context_attributes:
        if context_attribute['Type'] == 'List':
            context_output += get_context_list_value(context, context_attribute['Attribute'])
        else:
            context_output += get_context_value(context, context_attribute['Attribute'])

    return context_output


def get_context_value(context, key):
    if not hasattr(context, key):
        return f"context.{key} not set. \n"

    return f'context.{key}:   {getattr(context, key)} \n'


def get_context_list_value(context, key):
    if not hasattr(context, key):
        return f"context.{key} not set. \n"

    context_list_var = getattr(context, key)

    list_values = f'context.{key}, length {len(context_list_var)} \n'
    for index, element in enumerate(context_list_var):
        list_values += f'   context.{key}[{index}]:   {element} \n'

    return list_values


def parse_markdown_context_table(code_guide_markdown_path: Path) -> List[Dict]:
    with open(code_guide_markdown_path) as code_guide_markdown:
        # Find the start of the table
        for line in code_guide_markdown:

            # The start of the table is identified with a div tag
            if line == '<div id="context-index-table">\n':
                break
        else:
            raise ValueError('Failed to find `<div id="context-index-table">` in code guide markdown')

        # Skip the blank line after the div tag
        next(code_guide_markdown)

        # Parse the header
        raw_header_row = next(code_guide_markdown)
        header_fields = tuple(parse_markdown_table_row(raw_header_row))
        required_header_fields = {'Attribute', 'Type'}
        if not set(header_fields).issuperset(required_header_fields):
            raise ValueError(
                f'Context table missing required fields, requires: {required_header_fields}, got: {header_fields}')

        # Skip the separator line between the table header and body
        next(code_guide_markdown)

        # Parse the table body
        context_guide = []
        for table_row in code_guide_markdown:

            # Break out when we hit the empty line at the end of the table
            if not table_row.rstrip('\n'):
                break

            columns = parse_markdown_table_row(table_row)
            context_guide.append(dict(zip(header_fields, columns)))
        else:
            raise ValueError('Error parsing context attribute table markdown, did not reach end of table')

    return context_guide


def parse_markdown_table_row(table_row: str) -> List:
    # Table rows are expected to be in the format:
    # | foo   | bar      |
    # We split on the pipe characters, throw away the empty first and last values either side of the table edges,
    # then strip out any whitespace either side of the values
    return [column.strip() for column in table_row.split('|')[1:-1]]
