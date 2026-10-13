import hashlib
import json
import uuid

from behave import step
from tenacity import retry, wait_fixed, stop_after_delay

from acceptance_tests.utilities.event_helper import get_logged_events_for_case_by_id
from acceptance_tests.utilities.pubsub_helper import publish_to_pubsub
from acceptance_tests.utilities.test_case_helper import test_helper
from config import Config


@step('an eQ receipt with a transaction ID and unrelated case ID is published')
def publish_eq_receipt_with_tx_id(context):
    context.correlation_id = str(uuid.uuid4())
    _publish_eq_receipt(context, context.correlation_id)


@step('an eQ receipt without a transaction ID is published')
def publish_eq_receipt_without_tx_id(context):
    _publish_eq_receipt(context, None)


@step('an eQ receipt with an unknown questionnaire ID is published')
def publish_bad_eq_receipt(context):
    message = json.dumps({'tx_id': str(uuid.uuid4()), 'questionnaire_id': '555555'})
    publish_to_pubsub(message, project=Config.PUBSUB_EQ_RECEIPT_PROJECT,
                      topic=Config.PUBSUB_EQ_RECEIPT_TOPIC)
    context.message_hashes = [hashlib.sha256(message.encode('utf-8')).hexdigest()]
    context.sent_messages.append(message)


def _publish_eq_receipt(context, tx_id):
    case_id = context.emitted_cases[0]['caseId']
    unrelated_case_id = str(uuid.uuid4())
    test_helper.assertNotEqual(unrelated_case_id, case_id)
    receipt = {
        'case_id': unrelated_case_id,
        'questionnaire_id': context.emitted_uacs[0]['questionnaireId'],
    }
    if tx_id:
        receipt['tx_id'] = tx_id

    message = json.dumps(receipt)
    publish_to_pubsub(message, project=Config.PUBSUB_EQ_RECEIPT_PROJECT,
                      topic=Config.PUBSUB_EQ_RECEIPT_TOPIC)
    context.sent_messages.append(message)


@retry(wait=wait_fixed(1), stop=stop_after_delay(30), reraise=True)
def _get_logged_eq_receipt(context):
    receipts = [event for event in get_logged_events_for_case_by_id(context.emitted_cases[0]['caseId'])
                if event['type'] == 'RESPONSE_RECEIVED']
    test_helper.assertEqual(len(receipts), 1, f'Expected exactly one logged eQ receipt, got {receipts}')
    return receipts[0]


@step('the eQ receipt has a generated correlation ID')
def generated_eq_receipt_id(context):
    logged = _get_logged_eq_receipt(context)
    context.correlation_id = str(logged['correlation_id'])
    test_helper.assertEqual(uuid.UUID(context.correlation_id).version, 4)


@step('the eQ receipt audit has the expected correlation ID')
def eq_receipt_audit(context):
    logged = _get_logged_eq_receipt(context)
    test_helper.assertEqual(str(logged['correlation_id']), context.correlation_id)
    test_helper.assertEqual(uuid.UUID(str(logged['message_id'])).version, 4)
    test_helper.assertEqual(logged['channel'], 'EQ')
    test_helper.assertEqual(logged['source'], 'RECEIPT_SERVICE')
    test_helper.assertEqual(logged['date_time'], logged['message_timestamp'])
