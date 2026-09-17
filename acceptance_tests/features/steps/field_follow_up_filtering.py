import json
import uuid
from datetime import datetime, timezone

from behave import step

from acceptance_tests.utilities.pubsub_helper import get_matching_pubsub_message_acking_others, publish_to_pubsub
from acceptance_tests.utilities.test_case_helper import test_helper
from config import Config


@step('field follow-up messages are checked for the following cases:')
def check_expected_cases(context):
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
            failures.append(f"UPRN {uprn} should pass ('{reason}') but no message was found.")
        elif outcome == 'filtered' and has_message:
            failures.append(
                f"UPRN {uprn} should be filtered ('{reason}') but received a CREATE instruction anyway."
            )

    test_helper.assertFalse(failures, "CN-80 filtering mismatches:\n" + "\n".join(failures))
