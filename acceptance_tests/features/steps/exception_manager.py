import hashlib
import uuid

import requests
from behave import step
from tenacity import retry, wait_fixed, stop_after_delay

from acceptance_tests.utilities.exception_manager_helper import quarantine_bad_messages_check_and_reset
from acceptance_tests.utilities.pubsub_helper import publish_to_pubsub
from acceptance_tests.utilities.test_case_helper import test_helper
from config import Config

ALL_INCOMING_TOPICS = [Config.PUBSUB_RECEIPT_TOPIC, Config.PUBSUB_REFUSAL_TOPIC, Config.PUBSUB_INVALID_CASE_TOPIC,
                       Config.PUBSUB_DEACTIVATE_UAC_TOPIC, Config.PUBSUB_PRINT_FULFILMENT_TOPIC]


@step("a bad json msg is sent to every topic consumed by RM")
def put_a_bad_msg_on_every_topic_on(context):
    context.message_hashes = []

    for topic in ALL_INCOMING_TOPICS:
        message = 'not even close to json' + str(uuid.uuid4())

        publish_to_pubsub(message,
                          Config.PUBSUB_PROJECT,
                          topic)

        context.message_hashes.append(hashlib.sha256(message.encode('utf-8')).hexdigest())
        context.sent_messages.append(message)


@step('each bad msg is seen by exception manager with the message containing "{expected_exception_msg}"')
def look_for_each_bad_msg(context, expected_exception_msg):
    for message_hash in context.message_hashes:
        _check_message_exception_as_expected(message_hash, expected_exception_msg)

    response = requests.get(f'{Config.EXCEPTION_MANAGER_URL}/badmessages/summary')
    response.raise_for_status()
    bad_messages = response.json()

    test_helper.assertEqual(len(bad_messages), len(context.message_hashes),
                            msg='actual number of bad msgs does not match expected number of hashes'
                                f'bad_messages: {bad_messages}, context.message_hashes: {context.message_hashes}')


@retry(wait=wait_fixed(1), stop=stop_after_delay(30))
def _check_message_exception_as_expected(bad_message_hash, expected_exception):
    response = requests.get(f'{Config.EXCEPTION_MANAGER_URL}/badmessage/{bad_message_hash}')
    response.raise_for_status()
    message_details = response.json()

    test_helper.assertIn(expected_exception, message_details[0]['exceptionReport']['exceptionMessage'],
                         msg='Exception manager 1st exception message differs from expected message'
                         f'All message_details from exception manager: {message_details}')

    test_helper.assertGreater(message_details[0]['stats']['seenCount'], 1,
                              msg='Seen count is not greater than 1'
                              f'All message_details from exception manager: {message_details}')


@step('a bad message appears in exception manager with exception message containing "{expected_exception_msg}"')
def bad_message_appears_in_exception_manager(context, expected_exception_msg):
    look_for_each_bad_msg(context, expected_exception_msg)


@step("each bad msg can be successfully quarantined")
def each_bad_msg_can_be_successfully_quarantined(context):
    quarantine_bad_messages_check_and_reset(context.message_hashes)
