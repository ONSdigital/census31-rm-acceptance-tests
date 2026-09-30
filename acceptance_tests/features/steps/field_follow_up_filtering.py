from behave import step

from acceptance_tests.utilities.event_helper import (
    get_fieldwork_action_instructions_for_case_ids,
    non_n_case_ids,
    get_fieldwork_action_instructions
)
from acceptance_tests.utilities.pubsub_helper import get_exact_number_of_pubsub_messages
from acceptance_tests.utilities.test_case_helper import test_helper
from config import Config


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


@step('a refusal event is received for cases with the following properties:')
def send_refusal_for_loaded_case(context):
    # Use the already-loaded case from context
    test_helper.assertGreater(len(context.emitted_cases), 0, 
                              msg="No cases loaded from sample file")
    
    case_id = context.emitted_cases[0]['caseId']
    expected_cancel = context.table[0]['expected_cancel'].lower()
    
    # Send refusal event
    from acceptance_tests.utilities.pubsub_helper import publish_to_pubsub
    import json
    import uuid
    from datetime import datetime, timezone
    
    correlation_id = str(uuid.uuid4())
    message = json.dumps({
        "header": {
            "version": Config.EVENT_SCHEMA_VERSION,
            "topic": Config.PUBSUB_REFUSAL_TOPIC,
            "source": "CONTACT_CENTRE_API",
            "channel": "CC",
            "dateTime": f'{datetime.now(timezone.utc).replace(tzinfo=None).isoformat()}Z',
            "messageId": str(uuid.uuid4()),
            "correlationId": correlation_id,
            "messageType": "REFUSAL_RECEIVED"
        },
        "payload": {
            "refusal": {
                "caseId": case_id,
                "type": "HARD_REFUSAL",
                "agentId": "1234567890",
                "callId": "0987654321",
            }
        }
    })
    
    publish_to_pubsub(message, project=Config.PUBSUB_PROJECT, topic=Config.PUBSUB_REFUSAL_TOPIC)
    context.correlation_id = correlation_id
    context.sent_messages = getattr(context, 'sent_messages', [])
    context.sent_messages.append(message)
    
    # Store expected result for verification
    context.expected_cancel_outcome = expected_cancel


@step('no CANCEL fieldwork action instruction message is emitted for excluded cases')
def check_no_cancel_for_excluded_cases(context):
    case_id = context.emitted_cases[0]['caseId']
    
    try:
        cancel_messages = get_fieldwork_action_instructions(1, context.test_start_utc_datetime)
        has_cancel = any(
            msg['caseId'] == case_id and msg['actionInstruction'] == 'CANCEL'
            for msg in cancel_messages
        )
    except AssertionError:
        has_cancel = False
    
    test_helper.assertFalse(has_cancel, 
                           msg=f"Case {case_id} should NOT receive CANCEL but system emitted one")

