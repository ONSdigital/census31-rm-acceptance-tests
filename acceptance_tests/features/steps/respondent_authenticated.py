import json
import uuid
from datetime import datetime, timezone

from behave import step

from acceptance_tests.utilities.pubsub_helper import publish_to_pubsub
from config import Config


@step('a RESPONDENT_AUTHENTICATED event is received')
def send_respondent_authenticated(context):
    context.correlation_id = str(uuid.uuid4())
    context.originating_user = "test@test.com"
    message = _send_respondent_authenticated_msg(context.correlation_id, context.originating_user,
                                                 context.emitted_uacs[0]['qid'])
    context.sent_messages.append(message)


def _send_respondent_authenticated_msg(correlation_id, originating_user, qid):
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
                "messageType": "RESPONDENT_AUTHENTICATED",
            },
            "payload": {
                "respondentAuthenticated": {
                    "questionnaireId": qid
                }
            }
        }
    )

    publish_to_pubsub(message, project=Config.PUBSUB_PROJECT, topic=Config.PUBSUB_SURVEY_LAUNCHED_TOPIC)
    return message
