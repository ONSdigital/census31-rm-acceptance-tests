import uuid

import requests
from behave import step

from acceptance_tests.utilities import iap_requests
from acceptance_tests.utilities.audit_trail_helper import get_unique_user_email
from acceptance_tests.utilities.event_helper import get_emitted_survey_update_by_id
from acceptance_tests.utilities.notify_helper import check_sms_fulfilment_response
from acceptance_tests.utilities.test_case_helper import test_helper
from config import Config


@step('fulfilments are authorised for sms template "{template_name}"')
def authorise_sms_pack_code(context, template_name):
    context.template = context.sms_templates[template_name]['template']
    context.pack_code = context.sms_packcodes[template_name]['pack_code']
    context.notify_template_id = context.sms_packcodes[template_name]['notify_template_id']
    context.expected_questionnaire_type = context.sms_packcodes[template_name]['questionnaire_type']

    url = f'{Config.SUPPORT_TOOL_API_URL}/fulfilmentSurveySmsTemplates'
    body = {
        'surveyId': context.survey_id,
        'packCode': context.pack_code
    }

    response = iap_requests.make_request(method='POST', url=url, json=body)
    response.raise_for_status()

    survey_update_event = get_emitted_survey_update_by_id(context.survey_id, context.test_start_utc_datetime)

    allowed_sms_fulfilments = survey_update_event['allowedSmsFulfilments']
    test_helper.assertEqual(len(allowed_sms_fulfilments), 1,
                            'Unexpected number of allowedSmsFulfilments')
    test_helper.assertEqual(allowed_sms_fulfilments[0]['packCode'], context.pack_code,
                            'Unexpected allowedSmsFulfilments packCode')


@step('a request has been made for a UAC by SMS from phone number "{phone_number}"')
@step('a request has been made for a replacement UAC by SMS from phone number "{phone_number}"'
      ' with personalisation {personalisation:json}')
def request_replacement_uac_by_sms(context, phone_number, personalisation=None):
    context.phone_number = phone_number
    context.correlation_id = str(uuid.uuid4())
    context.originating_user = get_unique_user_email()

    url = f'{Config.NOTIFY_SERVICE_API}sms-fulfilment'
    body = {
        "header": {
            "source": "CC",
            "channel": "CC",
            "correlationId": context.correlation_id,
            "originatingUser": context.originating_user,
            "messageType": "SMS_FULFILMENT"
        },
        "payload": {
            "smsFulfilment": {
                "caseId": context.emitted_cases[0]['caseId'],
                "phoneNumber": context.phone_number,
                "packCode": context.pack_code,
                'uacMetadata': {"waveOfContact": "1"}
            }
        }
    }

    if personalisation:
        context.fulfilment_personalisation = body['payload']['smsFulfilment']['personalisation'] = personalisation

    response = requests.post(url, json=body)
    response.raise_for_status()

    context.fulfilment_response_json = response.json()

    check_sms_fulfilment_response(context.fulfilment_response_json, context.template)


@step('the UAC_UPDATE message matches the SMS fulfilment UAC')
def check_uac_message_matches_sms_uac(context):
    test_helper.assertEqual(context.emitted_uacs[0]['uacHash'], context.fulfilment_response_json['uacHash'],
                            f"Failed to 1st match uacHash, "
                            f"context.emitted_uacs: {context.emitted_uacs} "
                            f" context.fulfilment_response_json {context.fulfilment_response_json}")

    test_helper.assertEqual(context.emitted_uacs[0]['qid'], context.fulfilment_response_json['qid'],
                            f"Failed to 1st match qid, "
                            f"context.emitted_uacs: {context.emitted_uacs} "
                            f"context.fulfilment_response_json {context.fulfilment_response_json}")
    test_helper.assertEqual(context.emitted_uacs[0]['qid'][:2], context.expected_questionnaire_type)

    # Validate Welsh questionnaire type if present in context
    if hasattr(context, 'expected_welsh_questionnaire_type') and context.expected_welsh_questionnaire_type:
        if 'welsh_qid' in context.emitted_uacs[0] and context.emitted_uacs[0]['welsh_qid']:
            test_helper.assertEqual(context.emitted_uacs[0]['welsh_qid'][:2], context.expected_welsh_questionnaire_type)
