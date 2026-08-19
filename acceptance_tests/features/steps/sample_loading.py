from datetime import datetime, timezone, timedelta

from behave import step

from acceptance_tests.utilities.collex_helper import add_collex
from acceptance_tests.utilities.event_helper import get_emitted_cases, get_fieldwork_action_instructions_for_case_ids
from acceptance_tests.utilities.file_to_process_upload_helper import upload_and_process_file_by_api
from acceptance_tests.utilities.survey_helper import add_survey
from acceptance_tests.utilities.test_case_helper import test_helper
from acceptance_tests.utilities.validation_rule_helper import get_sample_rows_and_generate_open_validation_rules
from config import Config


def get_emitted_cases_and_check_against_sample(sample_rows, test_start_time):
    emitted_cases = get_emitted_cases(len(sample_rows), test_start_time)
    unmatched_sample_rows = sample_rows.copy()
    for emitted_case in emitted_cases:
        matched_row = None
        for sample_row in unmatched_sample_rows:
            if (sample_row["ESTAB_UPRN"] == emitted_case["address"]["estabUprn"] and
                    sample_row["ADDRESS_LINE1"] == emitted_case["address"]["addressLine1"] and
                    sample_row["UPRN"] == emitted_case["address"]["uprn"] and
                    sample_row["ADDRESS_LEVEL"] == emitted_case["address"]["addressLevel"]):
                matched_row = sample_row
                break

        if matched_row:
            unmatched_sample_rows.remove(matched_row)
        else:
            test_helper.fail(f"Could not find matching row in the sample data for case: {emitted_case} "
                             f"all emitted cases: {emitted_cases}")

    return emitted_cases


def _non_n_case_ids(emitted_cases):
    return {
        case['caseId']
        for case in emitted_cases
        if case.get('address')
        and case['address'].get('region')
        and not case['address']['region'].upper().startswith('N')
    }


@step('sample file "{sample_file_name}" is loaded successfully')
def load_sample(context, sample_file_name):
    sample_file_path = Config.SAMPLE_FILES_PATH.joinpath(sample_file_name)
    sample_rows = get_sample_rows_and_generate_open_validation_rules(sample_file_path)

    context.survey_id = add_survey(context.test_start_utc_datetime)

    collection_exercise_start_date = datetime.now(timezone.utc)
    context.collex_end_date = collection_exercise_start_date + timedelta(days=2)
    context.collex_id = add_collex(context.survey_id,
                                   context.test_start_utc_datetime, collection_exercise_start_date,
                                   context.collex_end_date)

    upload_and_process_file_by_api(context.collex_id, sample_file_path, 'SAMPLE')

    context.emitted_cases = get_emitted_cases_and_check_against_sample(sample_rows, context.test_start_utc_datetime)
    context.non_n_emitted_case_ids = _non_n_case_ids(context.emitted_cases)

    if context.non_n_emitted_case_ids:
        context.emitted_fieldwork_action_instructions = get_fieldwork_action_instructions_for_case_ids(
            context.non_n_emitted_case_ids,
            context.test_start_utc_datetime)

        for action_instruction in context.emitted_fieldwork_action_instructions:
            test_helper.assertEqual(action_instruction['actionInstruction'], 'CREATE')
    else:
        context.emitted_fieldwork_action_instructions = []
