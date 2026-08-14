import requests
from tenacity import retry, wait_fixed, stop_after_delay

from acceptance_tests.utilities.test_case_helper import test_helper
from config import Config


@retry(wait=wait_fixed(1), stop=stop_after_delay(30))
def check_notify_api_called_with_correct_phone_number_and_template_id(phone_number, notify_template_id):
    response = requests.get(f'{Config.NOTIFY_STUB_SERVICE}/log/sms')
    test_helper.assertEqual(response.status_code, 200, "Unexpected status code")
    response_json = response.json()
    test_helper.assertEqual(len(response_json), 1, f"Incorrect number of responses, response json {response_json}")
    test_helper.assertEqual(response_json[0]["phone_number"], phone_number, "Incorrect phone number, "
                                                                            f'response json {response_json}')
    test_helper.assertEqual(response_json[0]["template_id"], notify_template_id,
                            f"Incorrect Gov Notify template Id, response json {response_json}")

    return response_json[0]


def reset_notify_stub():
    requests.get(f'{Config.NOTIFY_STUB_SERVICE}/reset')
