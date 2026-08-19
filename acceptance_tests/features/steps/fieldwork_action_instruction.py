from behave import step

from acceptance_tests.utilities.event_helper import get_emitted_cases, get_fieldwork_action_instructions_for_case_ids
from acceptance_tests.utilities.pubsub_helper import get_exact_number_of_pubsub_messages
from acceptance_tests.utilities.test_case_helper import test_helper
from config import Config


def _is_n_region(region: str) -> bool:
    return bool(region) and region.upper().startswith('N')


def _is_ignored_region(region: str) -> bool:
    return not region or _is_n_region(region)


def _case_ids(emitted_cases):
    return {case['caseId'] for case in emitted_cases if case.get('address')}


def _non_n_case_ids(emitted_cases):
    return {
        case['caseId']
        for case in emitted_cases
        if case.get('address') and not _is_ignored_region(case['address'].get('region'))
    }


def _ignored_case_ids(emitted_cases):
    return {
        case['caseId']
        for case in emitted_cases
        if case.get('address') and _is_ignored_region(case['address'].get('region'))
    }


@step('CREATE fieldwork action instruction messages are emitted for all non-N region cases')
def check_create_action_instruction_messages_emitted(context):
    expected_case_ids = _non_n_case_ids(context.emitted_cases)
    test_helper.assertNotEqual(
        len(expected_case_ids),
        0,
        msg='This scenario expects emitted cases outside the N region from sample loading')

    context.emitted_fieldwork_action_instructions = getattr(context, 'emitted_fieldwork_action_instructions', None)
    if context.emitted_fieldwork_action_instructions is None:
        context.emitted_fieldwork_action_instructions = get_fieldwork_action_instructions_for_case_ids(
            expected_case_ids,
            context.test_start_utc_datetime)

    actual_case_ids = {message['caseId'] for message in context.emitted_fieldwork_action_instructions}
    test_helper.assertSetEqual(expected_case_ids, actual_case_ids,
                               msg=f'Expected action-instruction case IDs {expected_case_ids}, got {actual_case_ids}')

    for action_instruction in context.emitted_fieldwork_action_instructions:
        test_helper.assertEqual(action_instruction['actionInstruction'], 'CREATE')


@step('no fieldwork action instruction messages are sent for N region cases')
def check_no_create_action_instruction_messages_emitted_for_ignored_regions(context):
    expected_case_ids = _ignored_case_ids(context.emitted_cases)
    test_helper.assertNotEqual(
        len(expected_case_ids),
        0,
        msg='This scenario expects emitted cases in N regions from sample loading')

    # Try to pull one action instruction and expect none for this N-only scenario.
    with test_helper.assertRaises(AssertionError):
        get_exact_number_of_pubsub_messages(
            Config.PUBSUB_FIELDWORK_ACTION_INSTRUCTION_SUBSCRIPTION,
            expected_msg_count=1,
            timeout=3,
            test_start_time=context.test_start_utc_datetime)


@step('the emitted CREATE fieldwork action instruction messages contain expected case and address fields')
def check_create_action_instruction_fields(context):
    cases_by_id = {case['caseId']: case for case in context.emitted_cases}

    for action_instruction in context.emitted_fieldwork_action_instructions:
        expected_case = cases_by_id[action_instruction['caseId']]
        expected_address = expected_case['address']

        test_helper.assertEqual(action_instruction['surveyName'], 'CENSUS')
        test_helper.assertEqual(action_instruction['caseRef'], expected_case['caseRef'])
        test_helper.assertEqual(action_instruction['addressType'], expected_address['addressType'])
        test_helper.assertEqual(action_instruction['addressLevel'], expected_address['addressLevel'])
        test_helper.assertEqual(action_instruction['uprn'], expected_address['uprn'])
        test_helper.assertEqual(action_instruction['estabUprn'], expected_address['estabUprn'])
        test_helper.assertEqual(action_instruction['postcode'], expected_address['postcode'])


@step('CASE_UPDATE messages are emitted where "{case_field}" is "{expected_field_value}" for all loaded cases')
def check_case_update_messages_for_loaded_cases(context, case_field, expected_field_value):
    expected_case_ids = _case_ids(context.emitted_cases)

    emitted_case_updates = get_emitted_cases(
        expected_msg_count=len(expected_case_ids),
        test_start_time=context.test_start_utc_datetime,
        originating_user_email=context.originating_user)

    actual_case_ids = {case_update['caseId'] for case_update in emitted_case_updates}
    test_helper.assertSetEqual(
        expected_case_ids,
        actual_case_ids,
        msg=f'Expected case update IDs {expected_case_ids}, got {actual_case_ids}')

    for case_update in emitted_case_updates:
        test_helper.assertEqual(str(case_update[case_field]), expected_field_value,
                                msg=f'Expected field "{case_field}" to be "{expected_field_value}" in '
                                    f'case update {case_update}')
