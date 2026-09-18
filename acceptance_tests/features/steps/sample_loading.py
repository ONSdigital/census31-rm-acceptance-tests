from datetime import datetime, timezone, timedelta

from behave import step

from acceptance_tests.utilities.collex_helper import add_collex
from acceptance_tests.utilities.event_helper import get_emitted_cases, get_fieldwork_action_instructions_for_case_ids, \
    non_n_case_ids
from acceptance_tests.utilities.file_to_process_upload_helper import upload_and_process_file_by_api
from acceptance_tests.utilities.survey_helper import add_survey
from acceptance_tests.utilities.test_case_helper import test_helper
from acceptance_tests.utilities.validation_rule_helper import get_sample_rows_and_generate_open_validation_rules
from config import Config


def get_emitted_cases_and_check_against_sample(sample_rows, test_start_time):
    emitted_cases = get_emitted_cases(len(sample_rows), test_start_time)
    unmatched_sample_rows = sample_rows.copy()
    for emitted_case in emitted_cases:
        matched_row = get_matching_sample_row(emitted_case, unmatched_sample_rows)
        unmatched_sample_rows.remove(matched_row)

    return emitted_cases


def get_matching_sample_row(emitted_case, sample_rows):
    for sample_row in sample_rows:
        if (sample_row["ESTAB_UPRN"] == emitted_case["address"]["estabUprn"] and
                sample_row["ADDRESS_LINE1"] == emitted_case["address"]["addressLine1"] and
                sample_row["UPRN"] == emitted_case["address"]["uprn"] and
                sample_row["ADDRESS_LEVEL"] == emitted_case["address"]["addressLevel"]):
            return sample_row

    test_helper.fail(f"Could not find matching row in the sample data for case: {emitted_case}")


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

    context.sample_rows = sample_rows
    context.emitted_cases = get_emitted_cases_and_check_against_sample(sample_rows, context.test_start_utc_datetime)
    non_n_emitted_case_ids = non_n_case_ids(context.emitted_cases)

    if non_n_emitted_case_ids:
        context.emitted_fieldwork_action_instructions = get_fieldwork_action_instructions_for_case_ids(
            non_n_emitted_case_ids,
            context.test_start_utc_datetime)

        for action_instruction in context.emitted_fieldwork_action_instructions:
            test_helper.assertEqual(action_instruction['actionInstruction'], 'CREATE')
    else:
        context.emitted_fieldwork_action_instructions = []


@step('the outbound CASE_UPDATE events contain the expected sample data')
def check_outbound_case_update_events(context):
    address_fields = {
        "abpCode": "ABP_CODE",
        "addressLevel": "ADDRESS_LEVEL",
        "addressLine1": "ADDRESS_LINE1",
        "addressLine2": "ADDRESS_LINE2",
        "addressLine3": "ADDRESS_LINE3",
        "addressType": "ADDRESS_TYPE",
        "estabType": "ESTAB_TYPE",
        "estabUprn": "ESTAB_UPRN",
        "latitude": "LATITUDE",
        "longitude": "LONGITUDE",
        "organisationName": "ORGANISATION_NAME",
        "postcode": "POSTCODE",
        "townName": "TOWN_NAME",
        "uprn": "UPRN",
    }
    case_fields = {
        "caseType": "ADDRESS_TYPE",
        "fieldCoordinatorId": "FIELDCOORDINATOR_ID",
        "fieldOfficerId": "FIELDOFFICER_ID",
        "htcDigital": "HTC_DIGITAL",
        "htcWillingness": "HTC_WILLINGNESS",
        "lad": "LAD",
        "lsoa": "LSOA",
        "msoa": "MSOA",
        "oa": "OA",
        "printBatch": "PRINT_BATCH",
        "treatmentCode": "TREATMENT_CODE",
    }

    for emitted_case in context.emitted_cases:
        sample_row = get_matching_sample_row(emitted_case, context.sample_rows)

        for event_field, sample_field in address_fields.items():
            test_helper.assertEqual(
                emitted_case["address"][event_field],
                sample_row[sample_field],
                f'CASE_UPDATE address field "{event_field}" did not match sample row {sample_row}')

        for event_field, sample_field in case_fields.items():
            test_helper.assertEqual(
                emitted_case[event_field],
                sample_row[sample_field],
                f'CASE_UPDATE field "{event_field}" did not match sample row {sample_row}')

        sample_region = sample_row["REGION"]
        emitted_region = emitted_case["address"]["region"]
        test_helper.assertGreater(
            len(sample_region),
            1,
            f'Test sample region must contain more than one character, but was "{sample_region}"')
        test_helper.assertEqual(
            emitted_region,
            sample_region[0],
            f'CASE_UPDATE region must be the leading character of sample region "{sample_region}"')
        test_helper.assertEqual(
            len(emitted_region),
            1,
            f'CASE_UPDATE region must contain one character, but was "{emitted_region}"')
