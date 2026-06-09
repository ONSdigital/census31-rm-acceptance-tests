import logging
import random
import string
import uuid

from acceptance_tests.utilities import iap_requests
from requests.exceptions import HTTPError
from config import Config
from structlog import wrap_logger

logger = wrap_logger(logging.getLogger(__name__))


def create_template(create_url, pack_code, template, notify_template_id=None, export_file_destination=None):
    body = {
        'template': template,
        'packCode': pack_code,
        'description': "Test description",
        'metadata': {"foo": "bar"}
    }
    if notify_template_id:
        body['notifyTemplateId'] = notify_template_id
        body['notifyServiceRef'] = "test_service"

    if export_file_destination:
        body['exportFileDestination'] = export_file_destination

    try:
        response = iap_requests.make_request(method='POST', url=create_url, json=body)
        response.raise_for_status()
    except HTTPError:
        # If the template already exists, log and carry on
        logger.info(f'Template: {template} with pack code: {pack_code} already exists.')


def create_export_file_template(template, export_file_destination=Config.SUPPLIER_DEFAULT_TEST):
    pack_code = generate_pack_code('PRINT_')
    url = f'{Config.SUPPORT_TOOL_API_URL}/exportFileTemplates'
    create_template(url, pack_code, template, export_file_destination=export_file_destination)
    return pack_code


def create_sms_template(template):
    pack_code = generate_pack_code('SMS_')
    notify_template_id = str(uuid.uuid4())
    url = f'{Config.SUPPORT_TOOL_API_URL}/smsTemplates'
    create_template(url, pack_code, template, notify_template_id=notify_template_id)
    return pack_code, notify_template_id


def create_email_template(template, template_name=None):
    if template_name == 'his_survey_test':
        # HIS email templates must have a specific pack_code
        pack_code = 'MNE_EN_HMS'
    else:
        pack_code = generate_pack_code('EMAIL_')
    notify_template_id = str(uuid.uuid4())
    url = f'{Config.SUPPORT_TOOL_API_URL}/emailTemplates'
    create_template(url, pack_code, template, notify_template_id=notify_template_id)
    return pack_code, notify_template_id


def generate_pack_code(pack_code_prefix):
    # By using a unique random pack_code we have better filter options
    # We can change/remove this if we get UACS differently or a better solution is found
    return pack_code_prefix + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
