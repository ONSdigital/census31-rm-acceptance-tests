import json
import os
from pathlib import Path


class Config:
    EVENT_SCHEMA_VERSION = "0.5.0"  # noqa: F841

    RESOURCE_FILE_PATH = Path(os.getenv('RESOURCE_FILE_PATH') or Path(__file__).parent.joinpath('resources'))

    PUBSUB_PROJECT = os.getenv('PUBSUB_PROJECT', 'our-project')

    PUBSUB_RECEIPT_TOPIC = os.getenv('PUBSUB_RECEIPT_TOPIC', 'event_receipt')
    PUBSUB_REFUSAL_TOPIC = os.getenv('PUBSUB_REFUSAL_TOPIC', 'event_refusal')
    PUBSUB_INVALID_CASE_TOPIC = os.getenv('PUBSUB_INVALID_CASE_TOPIC',
                                          'event_invalid-case')
    PUBSUB_PRINT_FULFILMENT_TOPIC = os.getenv('PUBSUB_PRINT_FULFILMENT_TOPIC', 'event_print-fulfilment')
    PUBSUB_EQ_LAUNCH_TOPIC = os.getenv('PUBSUB_EQ_LAUNCH_TOPIC',  # noqa: F841
                                       'event_eq-launch')  # noqa: F841
    PUBSUB_DEACTIVATE_UAC_TOPIC = os.getenv('PUBSUB_DEACTIVATE_UAC_TOPIC', 'event_deactivate-uac')
    PUBSUB_OUTBOUND_UAC_SUBSCRIPTION = os.getenv('PUBSUB_OUTBOUND_UAC_SUBSCRIPTION', 'event_uac-update_rh_at')
    PUBSUB_OUTBOUND_CASE_SUBSCRIPTION = os.getenv('PUBSUB_OUTBOUND_CASE_SUBSCRIPTION', 'event_case-update_rh_at')
    PUBSUB_OUTBOUND_SURVEY_SUBSCRIPTION = os.getenv('PUBSUB_OUTBOUND_SURVEY_SUBSCRIPTION', 'event_survey-update_rh_at')
    PUBSUB_OUTBOUND_COLLECTION_EXERCISE_SUBSCRIPTION = os.getenv('PUBSUB_OUTBOUND_COLLECTION_EXERCISE_SUBSCRIPTION',
                                                                 'event_collection-exercise-update_rh_at')
    PUBSUB_NEW_CASE_TOPIC = os.getenv('PUBSUB_NEW_CASE_TOPIC', 'event_new-case')  # noqa: F841
    PUBSUB_CLOUD_TASK_QUEUE_AT_SUBSCRIPTION = os.getenv('PUBSUB_CLOUD_TASK_QUEUE_AT_SUBSCRIPTION',
                                                        'cloud_task_queue_at')
    PUBSUB_DEFAULT_PULL_TIMEOUT = int(os.getenv('PUBSUB_DEFAULT_PULL_TIMEOUT', 120))

    DB_USERNAME = os.getenv('DB_USERNAME', 'appuser')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')
    DB_HOST_CASE = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '6432')
    DB_NAME = os.getenv('DB_NAME', 'rm')
    DB_CASE_CERTIFICATES = os.getenv('DB_CASE_CERTIFICATES', '')

    EXCEPTIONMANAGER_CONNECTION_HOST = os.getenv('EXCEPTIONMANAGER_CONNECTION_HOST', 'localhost')
    EXCEPTIONMANAGER_CONNECTION_PORT = os.getenv('EXCEPTIONMANAGER_CONNECTION_PORT', '8666')
    EXCEPTION_MANAGER_URL = f'http://{EXCEPTIONMANAGER_CONNECTION_HOST}:{EXCEPTIONMANAGER_CONNECTION_PORT}'

    # Providing an IAP client ID will switch the tests to attempt to make all support tool requests with IAP auth,
    # This uses the default auth available in the environment
    SUPPORT_TOOL_IAP_CLIENT_ID = os.getenv('SUPPORT_TOOL_IAP_CLIENT_ID')

    # Note that for the ATs to go via IAP the protocol must be set to HTTPS in the Pod config
    SUPPORT_TOOL_BASE_URL = os.getenv("SUPPORT_TOOL_BASE_URL", "http://localhost:9999")

    SUPPORT_TOOL_API_URL = f"{SUPPORT_TOOL_BASE_URL}/api"

    # Allow the URL used for UI navigation to be set differently, since the browser driver cannot support IAP auth
    SUPPORT_TOOL_UI_URL = os.getenv('SUPPORT_TOOL_UI_URL', SUPPORT_TOOL_BASE_URL)  # noqa: F841

    NOTIFY_SERVICE_HOST = os.getenv('NOTIFY_SERVICE_HOST', 'localhost')
    NOTIFY_SERVICE_PORT = os.getenv('NOTIFY_SERVICE_PORT', '8162')
    NOTIFY_SERVICE_API = f'http://{NOTIFY_SERVICE_HOST}:{NOTIFY_SERVICE_PORT}/'  # noqa: F841

    NOTIFY_STUB_HOST = os.getenv('NOTIFY_STUB_HOST', 'localhost')
    NOTIFY_STUB_PORT = os.getenv('NOTIFY_STUB_PORT', '8917')
    NOTIFY_STUB_SERVICE = f'http://{NOTIFY_STUB_HOST}:{NOTIFY_STUB_PORT}'

    EXPORT_FILE_DESTINATION_CONFIG_JSON_PATH = Path(
        os.getenv('EXPORT_FILE_DESTINATION_CONFIG_JSON_PATH') or Path(__file__).parents[1].joinpath(
            'census31-rm-docker-dev',
            'dummy_destination_config.json'))
    EXPORT_FILE_DESTINATIONS_CONFIG = json.loads(
        EXPORT_FILE_DESTINATION_CONFIG_JSON_PATH.read_text()) \
        if EXPORT_FILE_DESTINATION_CONFIG_JSON_PATH and EXPORT_FILE_DESTINATION_CONFIG_JSON_PATH.exists() else None
    FILE_UPLOAD_DESTINATION = os.getenv('FILE_UPLOAD_DESTINATION', str(Path.home().joinpath('Documents/export_files')))
    FILE_UPLOAD_MODE = os.getenv('FILE_UPLOAD_MODE', 'LOCAL')
    OUR_EXPORT_FILE_DECRYPTION_KEY = os.getenv(
        'OUR_EXPORT_FILE_DECRYPTION_KEY',
        str(Path(__file__).parents[1].joinpath('census31-rm-docker-dev', 'dummy_keys',
                                               'dummy-key-census-rm-test-private.asc'))
    )
    OUR_EXPORT_FILE_DECRYPTION_KEY_PASSPHRASE = os.getenv('OUR_EXPORT_FILE_DECRYPTION_KEY_PASSPHRASE',
                                                          'dummy-census-rm-test')

    API_USER_EMAIL = os.getenv('API_USER_EMAIL', 'dummy@fake-email.com')

    CODE_GUIDE_MARKDOWN_FILE_PATH = Path(
        os.getenv('CODE_GUIDE_MARKDOWN_FILE_PATH') or Path(__file__).parent.joinpath('CODE_GUIDE.md'))

    SAMPLE_FILES_PATH = RESOURCE_FILE_PATH.joinpath('sample_files')

    SUPPLIER_INTERNAL_REPROGRAPHICS = os.getenv('SUPPLIER_INTERNAL_REPROGRAPHICS', 'internal_reprographics')
    SUPPLIER_DEFAULT_TEST = os.getenv('SUPPLIER_DEFAULT_TEST', 'test_supplier')
