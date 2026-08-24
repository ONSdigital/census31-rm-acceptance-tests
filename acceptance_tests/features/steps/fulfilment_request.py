import json
import uuid
from datetime import datetime, timezone

from behave import step

from acceptance_tests.utilities import iap_requests
from acceptance_tests.utilities.audit_trail_helper import add_random_suffix_to_email, get_unique_user_email
from acceptance_tests.utilities.event_helper import get_emitted_survey_update_by_id
from acceptance_tests.utilities.pubsub_helper import publish_to_pubsub
from acceptance_tests.utilities.test_case_helper import test_helper
from config import Config


@step('a print fulfilment has been requested')
@step('a print fulfilment with personalisation {personalisation:json} has been requested')
def request_print_fulfilment_step(context):
    context.correlation_id = str(uuid.uuid4())
    context.originating_user = add_random_suffix_to_email(context.scenario_name)
    message_dict = {
        "header": {
            "version": Config.EVENT_SCHEMA_VERSION,
            "topic": Config.PUBSUB_FULFILMENT_REQUEST_TOPIC,
            "source": "RH",
            "channel": "RH",
            "dateTime": f'{datetime.now(timezone.utc).replace(tzinfo=None).isoformat()}Z',
            "messageId": str(uuid.uuid4()),
            "correlationId": context.correlation_id,
            "originatingUser": context.originating_user,
            "messageType": "FULFILMENT_REQUEST",
        },
        "payload": {
            "fulfilmentRequest": {
                "caseId": context.emitted_cases[0]['caseId'],
                "fulfilmentCode": context.pack_code,
                "contact": {
                    "title": "Mr.",
                    "forename": "Joe",
                    "surname": "Bloggs"
                }
            }
        }
    }
    message = json.dumps(message_dict)
    publish_to_pubsub(message, project=Config.PUBSUB_PROJECT, topic=Config.PUBSUB_FULFILMENT_REQUEST_TOPIC)
    context.sent_messages.append(message)


@step("export file fulfilments are triggered to be exported")
def print_fulfilments_trigger_step(context):
    url = (f'{Config.SUPPORT_TOOL_API_URL}/fulfilmentNextTriggers'
           f'?triggerDateTime={datetime.now(timezone.utc).replace(microsecond=0).replace(tzinfo=None).isoformat()}Z')

    response = iap_requests.make_request(method='POST', url=url)
    response.raise_for_status()


@step('fulfilments are authorised for the export file template "{template_name}"')
def authorise_pack_code(context, template_name):
    context.template = context.export_file_templates[template_name]['template']
    context.pack_code = context.export_file_packcodes[template_name]['pack_code']
    context.expected_questionnaire_type = context.export_file_packcodes[template_name]['questionnaire_type']
    context.expected_welsh_questionnaire_type = context.export_file_packcodes[template_name]['welsh_questionnaire_type']
    url = f'{Config.SUPPORT_TOOL_API_URL}/fulfilmentSurveyExportFileTemplates'
    body = {
        'surveyId': context.survey_id,
        'packCode': context.pack_code
    }

    response = iap_requests.make_request(method='POST', url=url, json=body)
    response.raise_for_status()

    survey_update_event = get_emitted_survey_update_by_id(context.survey_id, context.test_start_utc_datetime)

    allowed_print_fulfilments = survey_update_event['allowedPrintFulfilments']
    test_helper.assertEqual(len(allowed_print_fulfilments), 1,
                            'Unexpected number of allowedPrintFulfilments')
    test_helper.assertEqual(allowed_print_fulfilments[0]['packCode'], context.pack_code,
                            'Unexpected allowedPrintFulfilments packCode')


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
def request_uac_by_sms_fulfilment(context, phone_number):
    context.phone_number = phone_number
    context.correlation_id = str(uuid.uuid4())
    context.originating_user = get_unique_user_email()

    message_dict = {
        "header": {
            "version": Config.EVENT_SCHEMA_VERSION,
            "topic": Config.PUBSUB_FULFILMENT_REQUEST_TOPIC,
            "source": "RH",
            "channel": "RH",
            "dateTime": f'{datetime.now(timezone.utc).replace(tzinfo=None).isoformat()}Z',
            "messageId": str(uuid.uuid4()),
            "correlationId": context.correlation_id,
            "originatingUser": context.originating_user,
            "messageType": "FULFILMENT_REQUEST",
        },
        "payload": {
            "fulfilmentRequest": {
                "caseId": context.emitted_cases[0]['caseId'],
                "fulfilmentCode": context.pack_code,
                "contact": {
                    "telNo": context.phone_number
                }
            }
        }
    }

    message = json.dumps(message_dict)
    publish_to_pubsub(message, project=Config.PUBSUB_PROJECT, topic=Config.PUBSUB_FULFILMENT_REQUEST_TOPIC)
    context.sent_messages.append(message)


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
