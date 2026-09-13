import hashlib
import json
import uuid
from datetime import datetime, timezone

from behave import step

from acceptance_tests.utilities.pubsub_helper import publish_to_pubsub
from config import Config


@step('a Receipt event is received')
def send_receipt_received(context):
    context.correlation_id = str(uuid.uuid4())
    message = _send_receipt_received_msg(context.correlation_id,
                                         context.emitted_uacs[0]['questionnaireId'])
    context.sent_messages.append(message)


@step('a bad Receipt event is put on the topic')
def bad_receipt_received_put_on_topic(context):
    message = _send_receipt_received_msg(str(uuid.uuid4()), "555555")
    context.message_hashes = [hashlib.sha256(message.encode('utf-8')).hexdigest()]
    context.sent_messages.append(message)


def _send_receipt_received_msg(correlation_id, qid):
    message = json.dumps(
        {
            "header": {
                "version": Config.EVENT_SCHEMA_VERSION,
                "topic": Config.PUBSUB_RECEIPT_TOPIC,
                "source": "RECEIPT_SERVICE",
                "channel": "EQ",
                "dateTime": f'{datetime.now(timezone.utc).replace(tzinfo=None).isoformat()}Z',
                "messageId": str(uuid.uuid4()),
                "correlationId": correlation_id,
                "messageType": "RECEIPT",
            },
            "payload": {
                "receipt": {
                    "qid": qid
                }
            }
        }
    )

    publish_to_pubsub(message, project=Config.PUBSUB_PROJECT, topic=Config.PUBSUB_RECEIPT_TOPIC)
    return message
