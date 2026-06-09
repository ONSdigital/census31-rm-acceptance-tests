import requests

from config import Config


def reset_notify_stub():
    requests.get(f'{Config.NOTIFY_STUB_SERVICE}/reset')
