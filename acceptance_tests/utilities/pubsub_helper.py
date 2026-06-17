import json
import logging
import time
from datetime import datetime
from typing import Callable, Mapping, Optional

from google.api_core.exceptions import DeadlineExceeded
from google.cloud import pubsub_v1
from structlog import wrap_logger
from tenacity import retry, wait_fixed, stop_after_delay, TryAgain

from acceptance_tests.utilities.test_case_helper import test_helper
from config import Config

logger = wrap_logger(logging.getLogger(__name__))

subscriptions = [Config.PUBSUB_OUTBOUND_SURVEY_SUBSCRIPTION,
                 Config.PUBSUB_OUTBOUND_COLLECTION_EXERCISE_SUBSCRIPTION,
                 Config.PUBSUB_OUTBOUND_UAC_SUBSCRIPTION,
                 Config.PUBSUB_OUTBOUND_CASE_SUBSCRIPTION,
                 Config.PUBSUB_CLOUD_TASK_QUEUE_AT_SUBSCRIPTION, ]


def publish_to_pubsub(message, project, topic, **kwargs):
    publisher = pubsub_v1.PublisherClient()

    topic_path = publisher.topic_path(project, topic)

    future = publisher.publish(topic_path, data=message.encode('utf-8'), **kwargs)

    future.result(timeout=30)


@retry(reraise=True, wait=wait_fixed(1), stop=stop_after_delay(60))
def purge_outbound_topics_with_retry():
    subscriptions_with_leftover_messages = purge_outbound_topics()

    if subscriptions_with_leftover_messages:
        logger.warn(
            f'There are left over messages on the following subscriptions: {subscriptions_with_leftover_messages}, '
            f'see logs above for details. This might be caused by messages published when the Pub/Sub service is in a '
            f'cold state. Will retry purging the leftover messages a few times until giving up and forcing a failure')
        raise TryAgain(f'Failed to purge messages from the following subscriptions: '
                       f'{subscriptions_with_leftover_messages}')


def purge_outbound_topics():
    subscriptions_with_leftover_messages = []

    for subscription_to_purge in subscriptions:
        if _purge_subscription(subscription_to_purge):
            subscriptions_with_leftover_messages.append(subscription_to_purge)

    return subscriptions_with_leftover_messages


def _purge_subscription(subscription):
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(Config.PUBSUB_PROJECT, subscription)

    return _ack_all_on_subscription(subscriber, subscription_path)


def _ack_all_on_subscription(subscriber, subscription_path):
    max_messages_per_attempt = 100

    try:
        response = subscriber.pull(subscription=subscription_path, max_messages=max_messages_per_attempt, timeout=2)
    except Exception:
        return

    messages = response.received_messages
    if messages:
        ack_ids = [message.ack_id for message in messages]
        logger.error(f'The following leftover messages exist on {subscription_path}: {messages}')
        subscriber.acknowledge(subscription=subscription_path, ack_ids=ack_ids)

    # It's possible (though unlikely) that they could be > max_messages on the topic so keep deleting till empty
    if len(response.received_messages) == max_messages_per_attempt:
        _ack_all_on_subscription(subscriber, subscription_path)

    return messages


def is_message_from_before_scenario(message, test_start_time):
    if not message.get('header'):
        return False
    if not message['header'].get('dateTime'):
        logger.warn('Found message header with no dateTime', message=message)
        return False
    message_datetime = datetime.fromisoformat(message['header']['dateTime'])
    return message_datetime < test_start_time


def _pull_exact_number_of_messages(subscriber, subscription_path, expected_msg_count, timeout,
                                   test_start_time=None):
    # Synchronously pull messages one at at time until we either hit the expected number or the timeout passes.
    scenario_messages = []
    deadline = time.time() + timeout

    # The PubSub subscriber client does not wait the full duration of its timeout before returning if it finds just
    # at least one message. To work around this, we loop pulling messages repeatedly within our own timeout to allow
    # the full time for all the expected messages to be published and pulled
    while len(scenario_messages) < expected_msg_count and time.time() < deadline:
        try:
            response = subscriber.pull(subscription=subscription_path, max_messages=expected_msg_count, timeout=1)
        except DeadlineExceeded:
            continue

        for message in (json.loads(message.message.data) for message in response.received_messages):
            if is_message_from_before_scenario(message, test_start_time):
                # Ignore messages from before the test start time, to avoid cross contamination from early scenarios
                logger.warn('Ignoring and acking a message from before this scenario', message=message)
                continue

            scenario_messages.append(message)

        # Ack all received messages, including any we're ignoring
        if response.received_messages:
            subscriber.acknowledge(subscription=subscription_path,
                                   ack_ids=[message.ack_id for message in response.received_messages])

    test_helper.assertEqual(len(scenario_messages), expected_msg_count,
                            f'Expected to pull exactly {expected_msg_count} message(s) from '
                            f'subscription {subscription_path} but found {len(scenario_messages)} '
                            f'within the {timeout} second timeout')
    return scenario_messages


def get_exact_number_of_pubsub_messages(subscription, expected_msg_count, timeout=Config.PUBSUB_DEFAULT_PULL_TIMEOUT,
                                        test_start_time: datetime = None):
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(Config.PUBSUB_PROJECT, subscription)
    received_messages = _pull_exact_number_of_messages(subscriber, subscription_path, expected_msg_count, timeout,
                                                       test_start_time=test_start_time)
    subscriber.close()
    return received_messages


def get_matching_pubsub_message_acking_others(subscription,
                                              message_matcher: Callable[[Mapping], tuple[bool, Optional[str]]],
                                              test_start_time,
                                              timeout=Config.PUBSUB_DEFAULT_PULL_TIMEOUT):
    """
    Pull and ack all pubsub messages on the given subscription within the timeout, until a match is found

    Args:
        subscription: PubSub subscription name
        message_matcher: A function object which takes the parsed message contents and returns a tuple,
            the first element being a bool indicating if the message matches, the second being a string used only if
            the message does not match, describing the non match to aid logging
        test_start_time: the test start datetime (tz aware)
        timeout: Default from config, The length of time to attempt to pull a matching message for, will fail the test
            if the timeout is reached.
    """
    return get_matching_pubsub_messages_acking_others(subscription,
                                                      message_matcher,
                                                      test_start_time,
                                                      number_of_messages=1,
                                                      timeout=timeout)[0]


def get_matching_pubsub_messages_acking_others(subscription,
                                               message_matcher: Callable[[Mapping], tuple[bool, Optional[str]]],
                                               test_start_time,
                                               number_of_messages: int = 1,
                                               timeout=Config.PUBSUB_DEFAULT_PULL_TIMEOUT):
    """
    Pull and ack all pubsub messages on the given subscription within the timeout,
    until the specified number of matches is found

    Args:
        number_of_messages:
        subscription: PubSub subscription name
        message_matcher: A function object which takes the parsed message contents and returns a tuple,
            the first element being a bool indicating if the message matches, the second being a string used only if
            the message does not match, describing the non match to aid logging
        test_start_time: the test start datetime (tz aware)
        number_of_messages: Default = 1, the number of matching messages to pull
        timeout: Default from config, The length of time to attempt to pull a matching message for, will fail the test
            if the timeout is reached.
    """
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(Config.PUBSUB_PROJECT, subscription)
    deadline = time.time() + timeout
    matching_messages = []

    # The PubSub subscriber client does not wait the full duration of its timeout before returning if it finds just
    # at least one message. To work around this, we loop pulling messages repeatedly within our own timeout to allow
    # the full time for all the expected messages to be published and pulled
    while len(matching_messages) < number_of_messages and time.time() < deadline:

        try:
            response = subscriber.pull(subscription=subscription_path, max_messages=1, timeout=1)
        except DeadlineExceeded:
            continue

        if not response.received_messages:
            # Keep trying to pull if we didn't receive a message
            continue

        received_message = response.received_messages[0]  # We have pulled only 1 max_messages
        parsed_message = json.loads(received_message.message.data)
        message_match, failure_description = message_matcher(parsed_message)

        if message_match and is_message_from_before_scenario(parsed_message, test_start_time):
            # Ignore messages from before the test start time, to avoid cross contamination from early scenarios
            logger.warn('Ignoring and acking a message from before this scenario', message=parsed_message)

        elif message_match:
            matching_messages.append(parsed_message)

        else:
            logger.warn(f'Acking non matching message on subscription {subscription_path}, '
                        f'failed match description: {failure_description}')

        subscriber.acknowledge(subscription=subscription_path,
                               ack_ids=[message.ack_id for message in response.received_messages])

    if len(matching_messages) != number_of_messages:
        test_helper.fail(
            f'Expected to pull {number_of_messages} matching message(s) on subscription {subscription_path} '
            f'but found {len(matching_messages)} matches within the {timeout} second timeout, '
            f'found messages: {matching_messages}'
        )

    return matching_messages
