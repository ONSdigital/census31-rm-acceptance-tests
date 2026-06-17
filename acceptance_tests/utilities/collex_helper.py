from datetime import datetime

from acceptance_tests.utilities import iap_requests
from acceptance_tests.utilities.event_helper import get_collection_exercise_update_by_name
from acceptance_tests.utilities.test_case_helper import test_helper
from config import Config


def add_collex(survey_id, test_start_time, start_date, end_date):
    collex_name = 'test collex ' + datetime.now().strftime("%m/%d/%Y, %H:%M:%S")

    url = f'{Config.SUPPORT_TOOL_API_URL}/collectionExercises'
    body = {'name': collex_name,
            'surveyId': survey_id,
            'reference': "MVP012021",
            'startDate': f'{start_date.isoformat()}',
            'endDate': f'{end_date.isoformat()}',
            'metadata': {'test': 'passed'},
            }

    response = iap_requests.make_request(method='POST', url=url, json=body)
    response.raise_for_status()

    collex_id = response.json()

    collection_exercise_update_event = get_collection_exercise_update_by_name(collex_name, test_start_time)
    test_helper.assertEqual(collection_exercise_update_event['name'], collex_name,
                            'Unexpected collection exercise name')
    test_helper.assertEqual(collection_exercise_update_event['surveyId'], survey_id,
                            'Unexpected survey ID')
    test_helper.assertEqual(collection_exercise_update_event['reference'], "MVP012021",
                            'Unexpected reference')

    parsed_start_date = datetime.fromisoformat(collection_exercise_update_event['startDate'])
    parsed_end_date = datetime.fromisoformat(collection_exercise_update_event['endDate'])

    test_helper.assertEqual(parsed_start_date, start_date, 'Invalid or missing start date')
    test_helper.assertEqual(parsed_end_date, end_date, 'Invalid or missing end date')

    test_helper.assertEqual(collection_exercise_update_event['metadata'], {'test': 'passed'},
                            'Unexpected metadata')

    return collex_id
