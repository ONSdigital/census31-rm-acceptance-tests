from behave import step

from acceptance_tests.utilities.event_helper import (
    get_fieldwork_action_instructions,
    get_fieldwork_action_instructions_for_case_ids,
)
from acceptance_tests.utilities.test_case_helper import test_helper


def _non_n_case_ids(emitted_cases):
    return {
        case['caseId']
        for case in emitted_cases
        if case.get('address') and case['address'].get('region') != 'N'
    }


@step('CREATE fieldwork action instruction messages are emitted for all non-N region cases')
def check_create_action_instruction_messages_emitted(context):
    expected_case_ids = _non_n_case_ids(context.emitted_cases)

    context.emitted_fieldwork_action_instructions = get_fieldwork_action_instructions_for_case_ids(
        expected_case_ids,
        context.test_start_utc_datetime)

    for action_instruction in context.emitted_fieldwork_action_instructions:
        test_helper.assertEqual(action_instruction['actionInstruction'], 'CREATE')


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


@step('no fieldwork action instruction messages are emitted for N region cases')
def check_no_action_instruction_for_nisra_cases(context):
    non_n_case_count = len(_non_n_case_ids(context.emitted_cases))
    test_helper.assertEqual(
        non_n_case_count,
        0,
        msg='This scenario expects only N-region emitted cases from sample loading')

    get_fieldwork_action_instructions(0, context.test_start_utc_datetime)

