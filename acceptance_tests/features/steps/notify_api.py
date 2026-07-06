import hashlib

from behave import step

from acceptance_tests.utilities.fulfilment_helper import build_expected_fulfilment_personalisation
from acceptance_tests.utilities.notify_helper import check_notify_api_called_with_correct_phone_number_and_template_id
from acceptance_tests.utilities.test_case_helper import test_helper


@step("notify api was called with the correct SMS template and values")
def check_sms_notify_api_call(context):
    notify_api_call = check_notify_api_called_with_correct_phone_number_and_template_id(context.phone_number,
                                                                                        context.notify_template_id)
    emitted_uac = context.emitted_uacs[0] if hasattr(context, 'emitted_uacs') else None
    request_personalisation = getattr(context, 'fulfilment_personalisation', {})

    check_notify_api_call(notify_api_call, context.template, context.emitted_cases[0], emitted_uac,
                          request_personalisation)


def check_notify_api_call(notify_api_call, template, case, emitted_uac, request_personalisation):
    expected_uac_hash = emitted_uac['uacHash'] if '__uac__' in template else None
    expected_qid = emitted_uac['qid'] if '__qid__' in template else None

    expected_personalisation = build_expected_fulfilment_personalisation(template, case,
                                                                         request_personalisation,
                                                                         expected_uac_hash, expected_qid)

    actual_personalisation = notify_api_call.get('personalisation', {}).copy()

    # We only have the uac hash to check against, so amend the actual values with the hash
    if '__uac__' in actual_personalisation.keys():
        actual_personalisation['__uac_hash__'] = hashlib.sha256(
            actual_personalisation['__uac__'].encode()).hexdigest()
        actual_personalisation.pop('__uac__')

    test_helper.assertDictEqual(actual_personalisation, expected_personalisation,
                                'Actual personalisation in notify API call must match expected')
