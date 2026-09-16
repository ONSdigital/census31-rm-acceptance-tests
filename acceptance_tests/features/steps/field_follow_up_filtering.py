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
        uprn, outcome, reason = row['case_id'], row['outcome'].lower(), row['reason']
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


@step('a receipted CASE_UPDATE is published for UPRN "{uprn}"')
def publish_receipted_case_update(context, uprn):
    selected_case = next(
        (case for case in context.emitted_cases if str(case.get('address', {}).get('uprn')) == uprn),
        None,
    )
    test_helper.assertIsNotNone(selected_case, f"Could not find an emitted case for UPRN {uprn}.")

    context.emitted_cases = [selected_case]
    context.correlation_id = str(uuid.uuid4())
    context.originating_user = Config.API_USER_EMAIL

    receipted_case = {**selected_case, 'receiptReceived': True}
    message = json.dumps(
        {
            'header': {
                'version': Config.EVENT_SCHEMA_VERSION,
                'topic': Config.PUBSUB_CASE_UPDATE_TOPIC,
                'source': 'CASE_PROCESSOR',
                'channel': 'RM',
                'dateTime': f'{datetime.now(timezone.utc).replace(tzinfo=None).isoformat()}Z',
                'messageId': str(uuid.uuid4()),
                'correlationId': context.correlation_id,
                'originatingUser': context.originating_user,
                'messageType': 'CASE_UPDATE',
                'fieldActionInstruction': 'UPDATE',
            },
            'payload': {'caseUpdate': receipted_case},
        }
    )

    publish_to_pubsub(message, project=Config.PUBSUB_PROJECT, topic=Config.PUBSUB_CASE_UPDATE_TOPIC)
    context.sent_messages.append(message)


@step('no fieldwork action instruction is sent for the receipted case')
def check_no_fieldwork_instruction_for_receipted_case(context):
    case_id = str(context.emitted_cases[0]['caseId'])

    def is_update_for_receipted_case(message):
        if str(message.get('caseId')) != case_id:
            return False, f"Case ID {message.get('caseId')} does not match {case_id}"
        if message.get('actionInstruction') != 'UPDATE':
            return False, f"Action instruction {message.get('actionInstruction')} is not UPDATE"
        return True, None

    with test_helper.assertRaises(AssertionError):
        get_matching_pubsub_message_acking_others(
            subscription=Config.PUBSUB_FIELDWORK_ACTION_INSTRUCTION_SUBSCRIPTION,
            message_matcher=is_update_for_receipted_case,
            timeout=3,
            test_start_time=context.test_start_utc_datetime,
        )
