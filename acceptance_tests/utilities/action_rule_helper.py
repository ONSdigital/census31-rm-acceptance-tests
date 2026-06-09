from datetime import datetime, timezone

from acceptance_tests.utilities import iap_requests
from config import Config

ACTION_RULES_URL = f'{Config.SUPPORT_TOOL_API_URL}/actionRules'


def create_export_file_action_rule(collex_id, classifiers, pack_code):
    body = {
        'type': 'EXPORT_FILE',
        'packCode': pack_code,
        'triggerDateTime': f'{datetime.now(timezone.utc).replace(tzinfo=None).isoformat()}Z',
        'classifiers': classifiers,
        'collectionExerciseId': collex_id
    }

    response = iap_requests.make_request(method='POST', url=ACTION_RULES_URL, json=body)
    response.raise_for_status()
    action_rule_id = str(response.text.strip('"'))
    return action_rule_id


def setup_deactivate_uac_action_rule(collex_id):
    body = {
        'type': 'DEACTIVATE_UAC',
        'packCode': None,
        'triggerDateTime': f'{datetime.now(timezone.utc).replace(tzinfo=None).isoformat()}Z',
        'classifiers': '',
        'collectionExerciseId': collex_id
    }

    response = iap_requests.make_request(method='POST', url=ACTION_RULES_URL, json=body)
    response.raise_for_status()
    action_rule_id = str(response.text.strip('"'))
    return action_rule_id


def set_eq_flush_action_rule(collex_id):
    body = {
        'type': 'EQ_FLUSH',
        'packCode': None,
        'triggerDateTime': f'{datetime.now(timezone.utc).replace(tzinfo=None).isoformat()}Z',
        'classifiers': '',
        'collectionExerciseId': collex_id,
    }

    response = iap_requests.make_request(method='POST', url=ACTION_RULES_URL, json=body)
    response.raise_for_status()
