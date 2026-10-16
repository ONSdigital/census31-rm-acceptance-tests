import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import pgpy
from behave import step
from google.cloud import storage
from tenacity import retry, retry_if_exception_type, stop_after_delay, wait_fixed

from acceptance_tests.utilities.sample_field_helper import sample_field_mapper
from acceptance_tests.utilities.test_case_helper import test_helper
from config import Config

MANIFEST_SCHEMA_VERSION = 1
EXPECTED_MANIFEST_PACK_CODE_COUNT = 24
EXPORT_FILE_SUFFIX = '.csv.gpg'
MANIFEST_FILE_SUFFIX = f'{EXPORT_FILE_SUFFIX}.manifest'
DEFAULT_MANIFEST_METADATA = {'dataset': '', 'description': ''}
# These pack codes exist in manifest metadata but are not represented by export file templates.
MANIFEST_ONLY_PACK_CODES = {'P_RL_1RL3CE', 'P_RL_2RL3CE'}

# Selected pack codes with explicit metadata assertions for additional coverage.
MANIFEST_ASSERTED_PACK_CODE_METADATA = {
    'P_IC_ICL1': {'dataset': 'CS10-CS5.1', 'description': 'Initial Invitation Contact Letter - England'},
    'P_IC_ICL2B': {'dataset': 'CS10-CS5.1', 'description': 'Initial Invitation Contact Letter - Wales (Bi-lingual)'},
    'P_IC_ICL3': {'dataset': 'CS10-CS5.1', 'description': 'Household Initial Invitation Contact Letter - Scotland'},
    'P_IC_ICL3A': {'dataset': 'CS10-CS5.1', 'description': 'CE Initial Invitation Contact Letter - Scotland'}
}


@step('the classifier is expected to export treatment codes "{exported_codes}" and filter "{filtered_codes}"')
def setup_treatment_code_expectations(context, exported_codes, filtered_codes):
    """Store expected exported and filtered treatment codes from scenario"""
    context.exported_treatment_codes = [code.strip() for code in exported_codes.split(',')]
    context.filtered_treatment_codes = [code.strip() for code in filtered_codes.split(',')]


@step('only cases with expected treatment codes are exported')
def validate_treatment_codes_in_export(context):
    """Validate that only cases matching exported treatment codes appear in the export,
    and cases with filtered codes are correctly excluded"""
    if not hasattr(context, 'exported_treatment_codes'):
        return  # Skip if treatment codes not set (for UAC templates)

    # Separate cases into those that should be exported vs filtered
    exported_cases = [case for case in context.emitted_cases
                      if case.get('treatmentCode') in context.exported_treatment_codes]
    filtered_cases = [case for case in context.emitted_cases
                      if case.get('treatmentCode') in context.filtered_treatment_codes]

    # Get the actual export file content
    supplier = _get_context_export_supplier_or_default(context)
    actual_export_file_rows = get_export_file_rows(context.test_start_utc_datetime, context.pack_code,
                                                   supplier=supplier)

    # Extract caseRefs from actual export file (skip header row)
    actual_export_caserefs = set()
    for row in actual_export_file_rows[1:]:  # Skip header
        row_data = next(csv.reader([row]))
        if row_data:  # Ensure non-empty row
            # Assuming caseRef is in a predictable column (typically column 1)
            caseref = row_data[1] if len(row_data) > 1 else None
            if caseref:
                actual_export_caserefs.add(caseref)

    # Assert exported cases are in the export
    for case in exported_cases:
        caseref = case.get('caseRef')
        test_helper.assertIn(caseref, actual_export_caserefs,
                             f"Case {caseref} with treatment code {case.get('treatmentCode')} "
                             f"should be exported but was not found in export file")

    # Assert filtered cases are NOT in the export
    for case in filtered_cases:
        caseref = case.get('caseRef')
        test_helper.assertNotIn(caseref, actual_export_caserefs,
                                f"Case {caseref} with treatment code {case.get('treatmentCode')} "
                                f"should have been filtered out but was found in export file")


@step("an export file is created with correct rows")
def check_export_file(context):
    template = context.template
    pack_code = context.pack_code
    emitted_uacs = context.emitted_uacs if hasattr(context, 'emitted_uacs') else None
    contact = context.contact if hasattr(context, 'contact') else None
    context.export_supplier = Config.SUPPLIER_CENSUS_PRINT

    test_helper.assertFalse(('__uac__' in template or '__qid__' in template) and not emitted_uacs,
                            'Export file template expects UACs or QIDs but no corresponding emitted_uacs found in '
                            f'the scenario context, emitted_uacs {emitted_uacs}')

    welsh_error_message = (
        'Export file template expects welsh UACs or QIDs but no corresponding welsh emitted_uacs found in '
        f'the scenario context, emitted_uacs {emitted_uacs}'
    )
    test_helper.assertFalse(('__welsh_uac__' in template or '__welsh_qid__' in template) and not emitted_uacs,
                            welsh_error_message)

    supplier = _get_context_export_supplier_or_default(context)

    actual_export_file_rows = get_export_file_rows(context.test_start_utc_datetime, context.pack_code,
                                                   supplier=supplier)

    uacs_from_actual_export_file = (
        (_get_unhashed_uacs_from_actual_export_file(actual_export_file_rows, template, "__uac__")
         if "__uac__" in template else ())
        + (_get_unhashed_uacs_from_actual_export_file(actual_export_file_rows, template, "__welsh_uac__")
           if "__welsh_uac__" in template else ())
    )
    if '__uac__' in template or '__welsh_uac__' in template:
        # Read the ACTUAL header from the actual export file (already sanitised by service)
        actual_header_line = actual_export_file_rows[0]
        actual_headers = next(csv.reader([actual_header_line]))

        # Generate expected data rows using the template for logic and actual headers for output
        # This avoids duplicating the header sanitisation logic
        expected_export_file_rows = generate_expected_export_file_rows(
            template, actual_headers, context.emitted_cases, emitted_uacs, uacs_from_actual_export_file,
            contact, pack_code, context.expected_questionnaire_type,
            context.expected_welsh_questionnaire_type
        )
        check_export_file_matches_expected(actual_export_file_rows, expected_export_file_rows)
    else:
        # For no-UAC templates (postcards), validate row contents match expected
        actual_header_line = actual_export_file_rows[0]
        actual_headers = next(csv.reader([actual_header_line]))

        expected_export_file_rows = generate_expected_export_file_rows(
            template, actual_headers, context.emitted_cases, None, (),
            contact, pack_code, context.expected_questionnaire_type,
            context.expected_welsh_questionnaire_type
        )
        check_export_file_matches_expected(actual_export_file_rows, expected_export_file_rows)

    check_manifest_file(context, supplier, actual_export_file_rows)


@step('an export file template has been created with template "{template_name}"')
def create_export_file_template(context, template_name):
    context.template = context.export_file_templates[template_name]['template']
    context.pack_code = context.export_file_packcodes[template_name]['pack_code']
    context.expected_questionnaire_type = context.export_file_packcodes[template_name][
        'questionnaire_type']
    context.expected_welsh_questionnaire_type = context.export_file_packcodes[template_name][
        'welsh_questionnaire_type']


@step('manifest metadata mappings cover all configured 2027 pack codes')
def check_manifest_metadata_pack_code_coverage(context):
    template_pack_codes = set(context.export_file_packcodes.keys())
    expected_pack_codes = template_pack_codes.union(MANIFEST_ONLY_PACK_CODES)
    actual_pack_codes = set(context.manifest_pack_code_metadata.keys())

    test_helper.assertEqual(EXPECTED_MANIFEST_PACK_CODE_COUNT, len(expected_pack_codes),
                            'Unexpected number of configured 2027 manifest pack codes')

    missing_pack_codes = sorted(expected_pack_codes - actual_pack_codes)
    unexpected_pack_codes = sorted(actual_pack_codes - expected_pack_codes)

    test_helper.assertEqual([], missing_pack_codes,
                            f'Manifest metadata missing expected pack codes: {missing_pack_codes}')
    test_helper.assertEqual([], unexpected_pack_codes,
                            f'Manifest metadata contains unexpected pack codes: {unexpected_pack_codes}')

    for pack_code, expected_manifest_metadata in MANIFEST_ASSERTED_PACK_CODE_METADATA.items():
        actual_manifest_metadata = context.manifest_pack_code_metadata.get(pack_code)
        test_helper.assertEqual(expected_manifest_metadata, actual_manifest_metadata,
                                f'Unexpected manifest metadata for pack code {pack_code}')


def _get_context_export_supplier_or_default(context) -> str:
    return context.export_supplier if hasattr(context, 'export_supplier') else Config.SUPPLIER_DEFAULT_TEST


def _get_uac_matching_case_id(uac_update_events, case_id, questionnaire_type):
    for uac_dto in uac_update_events:
        if uac_dto['caseId'] == case_id and uac_dto['questionnaireId'][:2] == questionnaire_type:
            return uac_dto

    test_helper.fail(f"Couldn't find event with case ID: {case_id} in UAC_UPDATE events. "
                     f"Full uac_update_events list: {uac_update_events}")


def get_uac_hash_by_case_id(uac_update_events, case_id, questionnaire_type):
    matching_uac_dto = _get_uac_matching_case_id(uac_update_events, case_id, questionnaire_type)

    if matching_uac_dto:
        return matching_uac_dto['uacHash']


def get_qid_by_case_id(uac_update_events, case_id, questionnaire_type):
    matching_uac_dto = _get_uac_matching_case_id(uac_update_events, case_id, questionnaire_type)

    if matching_uac_dto:
        return matching_uac_dto['questionnaireId']


def _get_unhashed_uacs_from_actual_export_file(actual_export_file_rows, template, uac_field):
    export_file_reader = csv.DictReader(actual_export_file_rows, fieldnames=template, delimiter=',')
    next(export_file_reader, None)  # Exclude header row
    return tuple(export_file_row[uac_field] for export_file_row in export_file_reader)


def generate_expected_export_file_rows(
        template: List, actual_headers: List, cases: List, uac_update_events: List, expected_uacs: Iterable[str],
        contact: Dict, pack_code: str, questionnaire_type, welsh_questionnaire_type):
    """
    Generate expected export file rows.

    Uses actual headers from the actual export file (which may be sanitised)
    to avoid duplicating sanitisation logic. Uses template for field-to-data mapping.
    """
    hashed_uac_to_uac = {
        hashlib.sha256(uac.encode('utf-8')).hexdigest(): uac
        for uac in expected_uacs
    }

    # Use actual headers from the actual export file (no sanitisation duplication)
    export_file_rows = [format_expected_export_file_row(actual_headers)]
    for case in cases:
        export_row_components = []
        for field in template:
            if field == '__uac__':
                hashed_uac = get_uac_hash_by_case_id(uac_update_events, case['caseId'], questionnaire_type)
                export_row_components.append(hashed_uac_to_uac[hashed_uac])
            elif field == '__qid__':
                qid = get_qid_by_case_id(uac_update_events, case['caseId'], questionnaire_type)
                export_row_components.append(qid)
            elif field == '__welsh_uac__':
                hashed_uac = get_uac_hash_by_case_id(uac_update_events, case['caseId'], welsh_questionnaire_type)
                export_row_components.append(hashed_uac_to_uac[hashed_uac])
            elif field == '__welsh_qid__':
                qid = get_qid_by_case_id(uac_update_events, case['caseId'], welsh_questionnaire_type)
                export_row_components.append(qid)
            elif field.startswith('__request__'):
                export_row_components.append(contact[field.split('.')[1]])
            elif field.startswith('__caseref__'):
                export_row_components.append(case['caseRef'])
            elif field.startswith('__pack_code__'):
                export_row_components.append(pack_code)
            else:

                export_row_components.append(
                    case["address"][sample_field_mapper(field)] if not case.get(sample_field_mapper(field)) else case[
                        sample_field_mapper(field)])
        export_file_rows.append(format_expected_export_file_row(export_row_components))
    return export_file_rows


def format_expected_export_file_row(export_row_components: Iterable[str]):
    # The export file format is comma separated and always double quote wrapped CSV
    return ','.join(f'"{component}"' for component in export_row_components)


def check_export_file_matches_expected(actual_export_file, expected_export_file):
    test_helper.assertEqual(actual_export_file[0], expected_export_file[0],
                            'Export file header row did not match expected')

    actual_export_file.sort()
    expected_export_file.sort()

    test_helper.assertEqual(actual_export_file, expected_export_file, 'Export file contents did not match expected')


def check_manifest_file(context, supplier, actual_export_file_rows):
    manifest_json = get_manifest_json(context.test_start_utc_datetime, context.pack_code, supplier=supplier)
    expected_manifest_metadata = _get_expected_manifest_metadata(context, context.pack_code)
    actual_export_file_name = get_export_file_name(context.test_start_utc_datetime,
                                                   context.pack_code,
                                                   supplier=supplier,
                                                   suffix=EXPORT_FILE_SUFFIX)
    actual_manifest_file_name = get_manifest_file_name(context.test_start_utc_datetime,
                                                       context.pack_code,
                                                       supplier=supplier)
    expected_manifest_file_name = f'{actual_export_file_name}.manifest'

    test_helper.assertEqual(MANIFEST_SCHEMA_VERSION, manifest_json['schemaVersion'],
                            'Unexpected manifest schemaVersion')
    test_helper.assertEqual(expected_manifest_metadata['dataset'], manifest_json['dataset'],
                            'Unexpected manifest dataset value')
    test_helper.assertEqual(expected_manifest_metadata['description'], manifest_json['description'],
                            'Unexpected manifest description value')
    test_helper.assertEqual('ONS_RM', manifest_json['sourceName'], 'Unexpected manifest sourceName')
    test_helper.assertNotIn('packCode', manifest_json, 'Manifest should not contain packCode')
    test_helper.assertNotIn('destination', manifest_json, 'Manifest should not contain destination')

    test_helper.assertEqual(actual_export_file_name, manifest_json['files'][0]['name'],
                            'Manifest file entry name should match export filename')
    test_helper.assertEqual(expected_manifest_file_name, actual_manifest_file_name,
                            'Manifest filename should append .manifest to the full export filename')
    test_helper.assertTrue(actual_manifest_file_name.endswith(MANIFEST_FILE_SUFFIX),
                           f'Manifest filename should end with {MANIFEST_FILE_SUFFIX}')
    test_helper.assertEqual('./', manifest_json['files'][0]['relativePath'],
                            'Unexpected manifest files relativePath')

    actual_row_count_excluding_header = len(actual_export_file_rows) - 1
    test_helper.assertEqual(actual_row_count_excluding_header, manifest_json['files'][0]['rows'],
                            'Manifest files rows count does not match exported rows')


def _get_expected_manifest_metadata(context, pack_code) -> Dict:
    return context.manifest_pack_code_metadata.get(pack_code, DEFAULT_MANIFEST_METADATA)


def get_datetime_from_export_file_name(export_file_name: str, prefix: str, suffix: str) -> datetime:
    raw_datetime = export_file_name[len(prefix):-len(suffix)]  # Strip off the prefix and suffix
    return datetime.strptime(raw_datetime, '%Y-%m-%dT%H-%M-%S').replace(tzinfo=timezone.utc)


def get_export_files_local(after_datetime: datetime, pack_code: str, export_file_destination: str, suffix: str):
    destination_path = Path(Config.FILE_UPLOAD_DESTINATION).joinpath(export_file_destination)
    prefix = f'{pack_code}_'
    export_files = destination_path.glob(f'{prefix}*{suffix}')

    return tuple(
        export_file for export_file in export_files
        if get_datetime_from_export_file_name(export_file.name, prefix, suffix) >= after_datetime
    )


def get_export_file_contents_local(after_datetime: datetime, pack_code: str, export_file_destination: str,
                                   suffix: str) -> Optional[str]:
    export_files_after_datetime = get_export_files_local(after_datetime, pack_code, export_file_destination, suffix)

    if len(export_files_after_datetime) == 0:
        return

    assert len(export_files_after_datetime) == 1, (f'Found more than one export file'
                                                   f' with expected pack code {pack_code},'
                                                   f' found files: {export_files_after_datetime}'
                                                   f' in destination: {Config.FILE_UPLOAD_DESTINATION}')

    return export_files_after_datetime[0].read_text()


def get_export_file_name_local(after_datetime: datetime, pack_code: str, export_file_destination: str,
                               suffix: str) -> Optional[str]:
    export_files_after_datetime = get_export_files_local(after_datetime, pack_code, export_file_destination, suffix)

    if len(export_files_after_datetime) == 0:
        return

    assert len(export_files_after_datetime) == 1, (f'Found more than one export file'
                                                   f' with expected pack code {pack_code},'
                                                   f' found files: {export_files_after_datetime}'
                                                   f' in destination: {Config.FILE_UPLOAD_DESTINATION}')

    return export_files_after_datetime[0].name


def get_export_files_bucket(after_datetime: datetime, pack_code: str, export_file_destination: str, suffix: str):
    storage_client = storage.Client()
    storage_bucket = storage_client.get_bucket(Config.FILE_UPLOAD_DESTINATION)

    destination_and_pack_code_prefix = f'{export_file_destination}/{pack_code}_'
    return tuple(
        blob for blob in storage_bucket.list_blobs(prefix=destination_and_pack_code_prefix)
        if blob.name.endswith(suffix)
        and get_datetime_from_export_file_name(blob.name, destination_and_pack_code_prefix, suffix) >= after_datetime
    )


def get_export_file_contents_bucket(after_datetime: datetime, pack_code: str, export_file_destination: str,
                                    suffix: str) -> Optional[str]:
    export_files_after_datetime = get_export_files_bucket(after_datetime, pack_code, export_file_destination, suffix)

    if len(export_files_after_datetime) == 0:
        return

    assert len(export_files_after_datetime) == 1, (f'Found more than one export file'
                                                   f' with expected pack code {pack_code},'
                                                   f' found files: {export_files_after_datetime}'
                                                   f' in destination: {Config.FILE_UPLOAD_DESTINATION}')

    matching_export_file_blob = export_files_after_datetime[0]
    export_file_bytes = matching_export_file_blob.download_as_bytes()
    return export_file_bytes.decode()


def get_export_file_name_bucket(after_datetime: datetime, pack_code: str, export_file_destination: str,
                                suffix: str) -> Optional[str]:
    export_files_after_datetime = get_export_files_bucket(after_datetime, pack_code, export_file_destination, suffix)

    if len(export_files_after_datetime) == 0:
        return

    assert len(export_files_after_datetime) == 1, (f'Found more than one export file'
                                                   f' with expected pack code {pack_code},'
                                                   f' found files: {export_files_after_datetime}'
                                                   f' in destination: {Config.FILE_UPLOAD_DESTINATION}')

    return export_files_after_datetime[0].name.split('/')[-1]


def get_export_file_contents(after_datetime: datetime, pack_code: str, export_file_destination: str,
                             suffix=EXPORT_FILE_SUFFIX) -> Optional[str]:
    if Config.FILE_UPLOAD_MODE == 'LOCAL':
        return get_export_file_contents_local(after_datetime, pack_code, export_file_destination, suffix)
    return get_export_file_contents_bucket(after_datetime, pack_code, export_file_destination, suffix)


@retry(retry=retry_if_exception_type(FileNotFoundError), wait=wait_fixed(1), stop=stop_after_delay(120))
def get_export_file_name(after_datetime: datetime, pack_code: str,
                         supplier=Config.SUPPLIER_DEFAULT_TEST, suffix=EXPORT_FILE_SUFFIX) -> str:
    export_file_destination = Config.EXPORT_FILE_DESTINATIONS_CONFIG[supplier].get('exportDirectory')

    if Config.FILE_UPLOAD_MODE == 'LOCAL':
        export_file_name = get_export_file_name_local(after_datetime, pack_code, export_file_destination, suffix)
    else:
        export_file_name = get_export_file_name_bucket(after_datetime, pack_code, export_file_destination, suffix)

    if not export_file_name:
        raise FileNotFoundError

    return export_file_name


def get_manifest_file_name(after_datetime: datetime, pack_code: str,
                           supplier=Config.SUPPLIER_DEFAULT_TEST) -> str:
    return get_export_file_name(after_datetime, pack_code, supplier=supplier, suffix=MANIFEST_FILE_SUFFIX)


def decrypt_export_file_contents(export_file_contents: str) -> List[str]:
    decrypted_contents = decrypt_message(export_file_contents)
    return decrypted_contents.rstrip().split('\n')


@retry(retry=retry_if_exception_type(FileNotFoundError), wait=wait_fixed(1), stop=stop_after_delay(120))
def get_export_file_rows(after_datetime: datetime, pack_code: str, supplier=Config.SUPPLIER_DEFAULT_TEST) -> List[str]:
    export_file_destination = Config.EXPORT_FILE_DESTINATIONS_CONFIG[supplier].get('exportDirectory')
    encrypted_export_file_contents = get_export_file_contents(after_datetime, pack_code,
                                                              export_file_destination)
    if not encrypted_export_file_contents:
        raise FileNotFoundError

    decrypted_export_file_rows = decrypt_export_file_contents(encrypted_export_file_contents)

    return decrypted_export_file_rows


@retry(retry=retry_if_exception_type(FileNotFoundError), wait=wait_fixed(1), stop=stop_after_delay(120))
def get_manifest_json(after_datetime: datetime, pack_code: str, supplier=Config.SUPPLIER_DEFAULT_TEST) -> Dict:
    export_file_destination = Config.EXPORT_FILE_DESTINATIONS_CONFIG[supplier].get('exportDirectory')
    manifest_file_contents = get_export_file_contents(after_datetime,
                                                      pack_code,
                                                      export_file_destination,
                                                      suffix=MANIFEST_FILE_SUFFIX)

    if not manifest_file_contents:
        raise FileNotFoundError

    return json.loads(manifest_file_contents)


def decrypt_message(message: str) -> str:
    our_key, _ = pgpy.PGPKey.from_file(Config.OUR_EXPORT_FILE_DECRYPTION_KEY)
    with our_key.unlock(Config.OUR_EXPORT_FILE_DECRYPTION_KEY_PASSPHRASE):
        encrypted_text_message = pgpy.PGPMessage.from_blob(message)
        message_text = our_key.decrypt(encrypted_text_message)

        return message_text.message


@step("the export file header row is sanitised according to:")
def verify_export_file_headers_sanitised_with_table(context):

    supplier = _get_context_export_supplier_or_default(context)
    actual_export_file_rows = get_export_file_rows(context.test_start_utc_datetime, context.pack_code,
                                                   supplier=supplier)

    if not actual_export_file_rows:
        test_helper.fail("No export file rows returned")

    # Read the ACTUAL headers from the ACTUAL export file (first line)
    actual_header_line = actual_export_file_rows[0]
    actual_headers = next(csv.reader([actual_header_line]))

    # Parse the table into list of dicts
    expected_mappings = [row for row in context.table]

    # Verify count
    test_helper.assertEqual(
        len(expected_mappings), len(actual_headers),
        f"Expected {len(expected_mappings)} headers but got {len(actual_headers)}. "
        f"Expected: {[m['template_key'] for m in expected_mappings]}, "
        f"Actual: {actual_headers}"
    )

    # Verify each mapping by position
    for position, expected_mapping in enumerate(expected_mappings):
        expected_template_key = expected_mapping['template_key']
        expected_header_name = expected_mapping['header_name']
        actual_header = actual_headers[position]

        test_helper.assertEqual(
            expected_header_name, actual_header,
            f"Position {position}: Expected header '{expected_header_name}' "
            f"(from template key '{expected_template_key}') but got '{actual_header}'"
        )
