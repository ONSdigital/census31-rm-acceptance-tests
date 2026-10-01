from behave import step

from acceptance_tests.utilities.event_helper import (
    get_fieldwork_action_instructions_for_case_ids,
    non_n_case_ids,
)
from acceptance_tests.utilities.test_case_helper import test_helper


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

    # Verify which cases actually received CREATE messages
    case_ids_with_create = {
        str(message['caseId']) for message in context.emitted_fieldwork_action_instructions
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

        has_message = case_id in case_ids_with_create

        if outcome == 'passed' and not has_message:
            failures.append(f"UPRN {uprn} should pass ('{reason}') but no CREATE message was found.")
        elif outcome == 'filtered' and has_message:
            failures.append(
                f"UPRN {uprn} should be filtered ('{reason}') but received a CREATE instruction anyway."
            )

    test_helper.assertFalse(failures, "Field follow-up filtering mismatches:\n" + "\n".join(failures))
