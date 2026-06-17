import requests
from tenacity import retry, wait_fixed, stop_after_delay

from acceptance_tests.utilities.audit_trail_helper import get_unique_user_email
from acceptance_tests.utilities.test_case_helper import test_helper
from config import Config


def quarantine_bad_messages(bad_message_hashes):
    for message_hash in bad_message_hashes:
        skip_request = {
            "messageHash": message_hash,
            "skippingUser": get_unique_user_email()
        }

        response = requests.post(f"{Config.EXCEPTION_MANAGER_URL}/skipmessage", json=skip_request)
        response.raise_for_status()


def get_bad_messages():
    response = requests.get(f'{Config.EXCEPTION_MANAGER_URL}/badmessages')
    response.raise_for_status()

    return response.json()


def quarantine_bad_messages_check_and_reset(message_hashes):
    quarantine_bad_messages(message_hashes)
    check_bad_messages_are_quarantined(message_hashes)
    requests.get(f'{Config.EXCEPTION_MANAGER_URL}/reset')


@retry(wait=wait_fixed(1), stop=stop_after_delay(30))
def check_bad_messages_are_quarantined(expected_quarantined_message_hashes):
    response = requests.get(f'{Config.EXCEPTION_MANAGER_URL}/skippedmessages')
    response.raise_for_status()
    all_quarantined_messages = response.json()
    all_quarantined_messages_hashes = [quarantined_message for quarantined_message in all_quarantined_messages]

    test_helper.assertTrue(set(expected_quarantined_message_hashes) <= set(all_quarantined_messages_hashes),
                           msg=f'Did not find all expected quarantined messages. '
                               f'Expected {expected_quarantined_message_hashes}, '
                               f'all quarantined messages {all_quarantined_messages_hashes}')
