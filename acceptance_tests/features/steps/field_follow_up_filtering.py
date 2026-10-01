from behave import step

from acceptance_tests.utilities.event_helper import (
    get_fieldwork_action_instructions_for_case_ids,
    non_n_case_ids,
    get_fieldwork_action_instructions,
)
from acceptance_tests.utilities.test_case_helper import test_helper


def validate_fieldwork_action_messages(context, messages, message_type):
    """
    Common validation pattern for fieldwork action instruction messages.

    Args:
        context: Behave context with emitted_cases and table
        messages: List of fieldwork action instruction messages
        message_type: String for error messages (e.g., 'CREATE', 'CANCEL')
    """
    case_ids_with_message = {
        str(message['caseId']) for message in messages
    }
    case_ids_by_uprn = {
        str(case['address']['uprn']): str(case['caseId']) for case in context.emitted_cases
    }

    failures = []
    for row in context.table:
        uprn, outcome, reason = row['uprn'], row['outcome'].lower(), row['reason']
        case_id = case_ids_by_uprn.get(uprn)
        if case_id is None:
            failures.append(f"UPRN {uprn} ('{reason}') was not found in the emitted cases.")
            continue

        has_message = case_id in case_ids_with_message

        if outcome == 'passed' and not has_message:
            failures.append(f"UPRN {uprn} should pass ('{reason}') but no {message_type} message was found.")
        elif outcome == 'filtered' and has_message:
            failures.append(
                f"UPRN {uprn} should be filtered ('{reason}') but received a {message_type} instruction anyway."
            )

    test_helper.assertFalse(failures, "Field follow-up filtering mismatches:\n" + "\n".join(failures))


@step('field follow-up messages are checked for the following cases:')
def check_expected_cases(context):
    # Get all non-N region cases for CREATE message retrieval
    expected_case_ids = non_n_case_ids(context.emitted_cases)

    # Retrieve ACTUAL fieldwork action instructions from system
    context.emitted_fieldwork_action_instructions = getattr(context, 'emitted_fieldwork_action_instructions', None)
    if context.emitted_fieldwork_action_instructions is None:
        context.emitted_fieldwork_action_instructions = get_fieldwork_action_instructions_for_case_ids(
            expected_case_ids,
            context.test_start_utc_datetime
        )

    validate_fieldwork_action_messages(context, context.emitted_fieldwork_action_instructions, 'CREATE')


@step('CANCEL fieldwork action instruction messages are validated for the following cases:')
def check_cancel_action_instruction_for_cases(context):
    # Check if any cases are expected to pass (emit CANCEL)
    should_have_messages = any(
        row['outcome'].lower() == 'passed' for row in context.table
    )

    if should_have_messages:
        emitted_cancel_messages = get_fieldwork_action_instructions(1, context.test_start_utc_datetime)
    else:
        # All cases filtered - expect no CANCEL messages
        with test_helper.assertRaises(AssertionError):
            get_fieldwork_action_instructions(1, context.test_start_utc_datetime)
        emitted_cancel_messages = []

    validate_fieldwork_action_messages(context, emitted_cancel_messages, 'CANCEL')


