from datetime import datetime
from functools import partial
from typing import Mapping

from acceptance_tests.utilities import iap_requests
from acceptance_tests.utilities.pubsub_helper import get_matching_pubsub_message_acking_others
from acceptance_tests.utilities.test_case_helper import test_helper
from config import Config


def add_survey(test_start_time,
               sample_has_header_row=True, sample_file_separator='|'):
    survey_name = 'test survey ' + datetime.now().strftime("%m/%d/%Y, %H:%M:%S")

    url = f'{Config.SUPPORT_TOOL_API_URL}/surveys'

    body = {"name": survey_name,
            "sampleWithHeaderRow": sample_has_header_row,
            "sampleSeparator": sample_file_separator,
            "metadata": {'foo': 'bar'}}

    response = iap_requests.make_request(method='POST', url=url, json=body)
    response.raise_for_status()

    survey_id = response.json()

    survey_update_event = get_emitted_survey_update(survey_name, test_start_time)
    test_helper.assertEqual(survey_update_event['name'], survey_name,
                            'Unexpected survey name')

    test_helper.assertEqual(survey_update_event['metadata'], {'foo': 'bar'},
                            'Unexpected metadata')

    return survey_id


def get_emitted_survey_update(expected_survey_name, test_start_time):
    # Build the matcher with the current expected survey name
    survey_name_matcher = partial(_survey_name_message_matcher, expected_survey_name=expected_survey_name)

    message_received = get_matching_pubsub_message_acking_others(Config.PUBSUB_OUTBOUND_SURVEY_SUBSCRIPTION,
                                                                 survey_name_matcher, test_start_time)

    return message_received['payload']['surveyUpdate']


def _survey_name_message_matcher(message: Mapping, expected_survey_name=None) -> (bool, str):
    if message['payload']['surveyUpdate']['name'] == expected_survey_name:
        return True, ''
    return False, f'Actual survey name "{message["payload"]["surveyUpdate"]["name"]}" ' \
                  f'does not match expected "{expected_survey_name}"'
