import hashlib
import json
import uuid
from datetime import datetime, timezone

from behave import step

from acceptance_tests.utilities.audit_trail_helper import add_random_suffix_to_email
from acceptance_tests.utilities.pubsub_helper import publish_to_pubsub
from config import Config


@step('an SURVEY_LAUNCHED event is received')
def send_survey_launched(context):
    _set_survey_launched_message_context(context)
    message = _send_survey_launched_msg(context.correlation_id, context.originating_user,
                                        context.emitted_uacs[0]['qid'])
    context.sent_messages.append(message)


@step('SURVEY_LAUNCHED events are received for all emitted UACs')
def send_survey_launched_for_all_emitted_uacs(context):
    _set_survey_launched_message_context(context)

    for emitted_uac in context.emitted_uacs:
        message = _send_survey_launched_msg(context.correlation_id, context.originating_user, emitted_uac['qid'])
        context.sent_messages.append(message)


def _set_survey_launched_message_context(context):
    context.correlation_id = str(uuid.uuid4())
    context.originating_user = "test@test.com"


@step('a bad Survey Launched event is put on the topic')
def bad_survey_launched_put_on_topic(context):
    context.originating_user = add_random_suffix_to_email(context.scenario_name)
    message = _send_survey_launched_msg(str(uuid.uuid4()), context.originating_user, "555555")
    context.message_hashes = [hashlib.sha256(message.encode('utf-8')).hexdigest()]
    context.sent_messages.append(message)


def _send_survey_launched_msg(correlation_id, originating_user, qid):
    message = json.dumps(
        {
            "header": {
                "version": Config.EVENT_SCHEMA_VERSION,
                "topic": Config.PUBSUB_SURVEY_LAUNCHED_TOPIC,
                "source": "RH",
                "channel": "RH",
                "dateTime": f'{datetime.now(timezone.utc).replace(tzinfo=None).isoformat()}Z',
                "messageId": str(uuid.uuid4()),
                "correlationId": correlation_id,
                "originatingUser": originating_user,
                "messageType": "SURVEY_LAUNCHED",
            },
            "payload": {
                "surveyLaunched": {
                    "questionnaireId": qid
                }
            }
        }
    )

    publish_to_pubsub(message, project=Config.PUBSUB_PROJECT, topic=Config.PUBSUB_SURVEY_LAUNCHED_TOPIC)
    return message
