from datetime import datetime
from functools import partial
from typing import Mapping, List, Optional

from tenacity import retry, wait_fixed, stop_after_delay

from acceptance_tests.utilities.database_helper import open_cursor
from acceptance_tests.utilities.pubsub_helper import get_exact_number_of_pubsub_messages, \
    get_matching_pubsub_message_acking_others, get_matching_pubsub_messages_acking_others
from acceptance_tests.utilities.test_case_helper import test_helper
from config import Config


def get_emitted_cases(expected_msg_count=1, test_start_time: datetime = None,
                      originating_user_email: str = Config.API_USER_EMAIL) -> List[Mapping]:
    messages_received = get_exact_number_of_pubsub_messages(
        Config.PUBSUB_OUTBOUND_CASE_SUBSCRIPTION, expected_msg_count, test_start_time=test_start_time)

    case_payloads = []
    for message_received in messages_received:
        test_helper.assertEqual(message_received['header']['originatingUser'], originating_user_email,
                                f'Unexpected originating user, all of messages_received: {messages_received}')
        case_payloads.append(message_received['payload']['caseUpdate'])

    return case_payloads


def get_fieldwork_action_instructions(expected_msg_count: int, test_start_time: datetime = None) -> List[Mapping]:
    return get_exact_number_of_pubsub_messages(
        Config.PUBSUB_FIELDWORK_ACTION_INSTRUCTION_SUBSCRIPTION,
        expected_msg_count,
        test_start_time=test_start_time)


def get_fieldwork_action_instructions_for_case_ids(case_ids: set[str], test_start_time: datetime) -> List[Mapping]:
    messages = get_fieldwork_action_instructions(len(case_ids), test_start_time)
    actual_case_ids = {message['caseId'] for message in messages}
    test_helper.assertSetEqual(case_ids, actual_case_ids,
                               msg=f'Expected action-instruction case IDs {case_ids}, got {actual_case_ids}')
    return messages


def _match_message_by_correlation_id(message: Mapping, correlation_id: str = None) -> (bool, Optional[str]):
    if (message_cid := message['header']['correlationId']) != correlation_id:
        return False, f'Message correlation ID "{message_cid}" does not match expected "{correlation_id}"'
    return True, None


def get_emitted_case_update_by_correlation_id(correlation_id: str, originating_user: Optional[str],
                                              test_start_time: datetime):
    message_received = get_matching_pubsub_message_acking_others(Config.PUBSUB_OUTBOUND_CASE_SUBSCRIPTION,
                                                                 partial(_match_message_by_correlation_id,
                                                                         correlation_id=correlation_id),
                                                                 test_start_time)

    if originating_user:
        test_helper.assertEqual(message_received['header']['originatingUser'], originating_user,
                                'Unexpected originating user')

    return message_received['payload']['caseUpdate']


def get_emitted_uac_update(correlation_id: str, originating_user: Optional[str], test_start_time: datetime):
    message_received = get_matching_pubsub_message_acking_others(Config.PUBSUB_OUTBOUND_UAC_SUBSCRIPTION,
                                                                 partial(_match_message_by_correlation_id,
                                                                         correlation_id=correlation_id),
                                                                 test_start_time)

    if originating_user:
        test_helper.assertEqual(message_received['header']['originatingUser'], originating_user,
                                'Unexpected originating user')

    return message_received['payload']['uacUpdate']


def get_uac_update_events(expected_number: int, correlation_id: str, originating_user: Optional[str],
                          test_start_time: datetime):
    messages_received = get_matching_pubsub_messages_acking_others(Config.PUBSUB_OUTBOUND_UAC_SUBSCRIPTION,
                                                                   partial(_match_message_by_correlation_id,
                                                                           correlation_id=correlation_id),
                                                                   test_start_time,
                                                                   number_of_messages=expected_number)

    uac_payloads = []

    for uac_event in messages_received:
        if originating_user:
            test_helper.assertEqual(uac_event['header']['originatingUser'], originating_user,
                                    f'Unexpected originating user,  full messages received {messages_received}')

        uac_payloads.append(uac_event['payload']['uacUpdate'])

    return uac_payloads


def _match_uac_linked_to_case_in_set(message: Mapping, case_ids: set = None):
    if (case_id := message['payload']['uacUpdate']['caseId']) not in case_ids:
        return False, f'Uac linked to unexpected case ID "{case_id}", expected one of {case_ids}'
    return True, None


def get_uac_update_events_matching_cases(cases: List[Mapping], test_start_time: datetime):
    messages_received = get_matching_pubsub_messages_acking_others(Config.PUBSUB_OUTBOUND_UAC_SUBSCRIPTION,
                                                                   partial(_match_uac_linked_to_case_in_set,
                                                                           case_ids={case['caseId'] for case in cases}),
                                                                   test_start_time,
                                                                   number_of_messages=len(cases))

    uac_payloads = []

    for uac_event in messages_received:
        uac_payloads.append(uac_event['payload']['uacUpdate'])

    return uac_payloads


def get_number_of_uac_update_events(expected_number: int, test_start_time: datetime):
    messages_received = get_exact_number_of_pubsub_messages(Config.PUBSUB_OUTBOUND_UAC_SUBSCRIPTION,
                                                            expected_msg_count=expected_number,
                                                            test_start_time=test_start_time)
    return [uac_event['payload']['uacUpdate'] for uac_event in messages_received]


def get_emitted_survey_update_by_id(survey_id: str, test_start_time: datetime):
    def match_survey_id(message, expected_survey_id: str = None):
        if message_survey_id := message['payload']['surveyUpdate']['surveyId'] != expected_survey_id:
            return False, (f'Failed match on message survey ID, found "{message_survey_id}",'
                           f' expected {expected_survey_id}')
        return True, None

    message_received = get_matching_pubsub_message_acking_others(Config.PUBSUB_OUTBOUND_SURVEY_SUBSCRIPTION,
                                                                 partial(match_survey_id,
                                                                         expected_survey_id=survey_id),
                                                                 test_start_time)

    return message_received['payload']['surveyUpdate']


def get_collection_exercise_update_by_name(collex_name: str, test_start_time: datetime):
    def collex_name_matcher(message, expected_collex_name=None):
        message_collex_name = message['payload']['collectionExerciseUpdate']['name']
        return (True, None) if message_collex_name == expected_collex_name else \
            (False, f'Collection exercise name "{message_collex_name}" did not match expected "{expected_collex_name}"')

    message_received = get_matching_pubsub_message_acking_others(
        Config.PUBSUB_OUTBOUND_COLLECTION_EXERCISE_SUBSCRIPTION,
        partial(collex_name_matcher, expected_collex_name=collex_name), test_start_time)

    return message_received['payload']['collectionExerciseUpdate']


def get_logged_case_events_by_type(case_id: str, type_filter: str):
    events = get_logged_events_for_case_by_id(case_id)

    logged_event_of_type = []

    for event in events:
        if event['type'] == type_filter:
            logged_event_of_type.append(event)

    return logged_event_of_type


def check_uac_update_msgs_emitted_with_qid_active_and_field_equals_value(emitted_cases: List[Mapping],
                                                                         correlation_id: str,
                                                                         active: bool,
                                                                         field_to_test: str,
                                                                         expected_value: bool,
                                                                         test_start_time: datetime):
    emitted_uacs = get_uac_update_events(len(emitted_cases), correlation_id, None, test_start_time=test_start_time)
    _check_uacs_updated_match_cases(emitted_uacs, emitted_cases)
    _check_new_uacs_are_as_expected(emitted_uacs, active, field_to_test, expected_value)

    return emitted_uacs


def check_uac_update_msgs_emitted_for_cases_with_qid_active_and_field_equals_value(emitted_cases: List[Mapping],
                                                                                   active: bool,
                                                                                   field_to_test: str,
                                                                                   expected_value: bool,
                                                                                   test_start_time: datetime):
    emitted_uacs = get_uac_update_events_matching_cases(emitted_cases, test_start_time=test_start_time)
    _check_uacs_updated_match_cases(emitted_uacs, emitted_cases)
    _check_new_uacs_are_as_expected(emitted_uacs, active, field_to_test, expected_value)

    return emitted_uacs


def _check_uacs_updated_match_cases(uac_update_events: List[Mapping], cases: List[Mapping]):
    test_helper.assertSetEqual(set(uac['caseId'] for uac in uac_update_events),
                               set(case['caseId'] for case in cases),
                               'The UAC updated events should be linked to the given set of case IDs')


def _check_new_uacs_are_as_expected(emitted_uacs: List[Mapping], active: bool, field_to_test: str = None,
                                    expected_value: bool = None):
    for uac in emitted_uacs:
        test_helper.assertEqual(uac['active'], active, f"UAC {uac} active status doesn't equal expected {active}")

        if field_to_test:
            test_helper.assertEqual(uac[field_to_test], expected_value,
                                    f"UAC {uac} field {field_to_test} doesn't equal expected {expected_value}")


@retry(wait=wait_fixed(1), stop=stop_after_delay(30))
def check_if_event_types_are_exact_match(expected_logged_event_types: list[str], case_id: str):
    logged_events = get_logged_events_for_case_by_id(case_id)
    actual_logged_event_types = [event['type'] for event in logged_events]

    test_helper.assertCountEqual(expected_logged_event_types, actual_logged_event_types,
                                 msg=f"Actual logged event types {actual_logged_event_types} "
                                     f"did not match expected {expected_logged_event_types}")


def get_logged_events_for_case_by_id(case_id: str) -> list[dict]:
    with open_cursor() as cur:
        cur.execute(
            "select * from cases.event where caze_id = %s OR uac_qid_link_id in \
             (select id from cases.uac_qid_link where cases.uac_qid_link.caze_id = %s)",
            (case_id, case_id))

        columns = [col[0] for col in cur.description]
        results = [dict(zip(columns, row)) for row in cur.fetchall()]
        return results
