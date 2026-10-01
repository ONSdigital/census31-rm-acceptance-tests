from behave import step

from acceptance_tests.utilities.event_helper import (
    get_fieldwork_action_instructions,
    get_fieldwork_action_instructions_for_case_ids,
    assert_no_fieldwork_action_instructions,
    non_n_case_ids,
)
from acceptance_tests.utilities.test_case_helper import test_helper

PASSED, FILTERED = 'passed', 'filtered'


def _parse_expectations(table):
    expectations = []
    for row in table:
        outcome = row['outcome'].strip().lower()
        test_helper.assertIn(
            outcome, (PASSED, FILTERED),
            f"Unknown outcome '{row['outcome']}' for UPRN {row['uprn']}; expected 'passed' or 'filtered'"
        )
        expectations.append((row['uprn'].strip(), outcome, row['reason']))
    return expectations


def validate_fieldwork_action_messages(context, messages, instruction_type):
    """Check each table row's UPRN did/didn't receive an instruction of `instruction_type`."""
    case_ids_with_message = {
        str(m['caseId']) for m in messages
        if m['actionInstruction'] == instruction_type
    }
    case_ids_by_uprn = {
        str(case['address']['uprn']): str(case['caseId']) for case in context.emitted_cases
    }

    failures = []
    for uprn, outcome, reason in _parse_expectations(context.table):
        case_id = case_ids_by_uprn.get(uprn)
        if case_id is None:
            failures.append(f"UPRN {uprn} ('{reason}') not found in emitted cases.")
            continue

        has_message = case_id in case_ids_with_message
        if outcome == PASSED and not has_message:
            failures.append(f"UPRN {uprn} should pass ('{reason}') but no {instruction_type} was found.")
        elif outcome == FILTERED and has_message:
            failures.append(f"UPRN {uprn} should be filtered ('{reason}') but got a {instruction_type}.")

    test_helper.assertFalse(
        failures,
        f"{instruction_type} fieldwork action instruction mismatches:\n" + "\n".join(failures)
    )


@step('field follow-up messages are checked for the following cases:')
def check_expected_cases(context):
    if getattr(context, 'emitted_fieldwork_action_instructions', None) is None:
        context.emitted_fieldwork_action_instructions = get_fieldwork_action_instructions_for_case_ids(
            non_n_case_ids(context.emitted_cases),
            context.test_start_utc_datetime,
        )

    validate_fieldwork_action_messages(context, context.emitted_fieldwork_action_instructions, 'CREATE')


@step('CANCEL fieldwork action instruction messages are validated for the following cases:')
def check_cancel_action_instruction_for_cases(context):
    expected_count = sum(outcome == PASSED for _, outcome, _ in _parse_expectations(context.table))

    if expected_count == 0:
        assert_no_fieldwork_action_instructions('CANCEL', context.test_start_utc_datetime)
        return

    messages = get_fieldwork_action_instructions(expected_count, context.test_start_utc_datetime)
    validate_fieldwork_action_messages(context, messages, 'CANCEL')
