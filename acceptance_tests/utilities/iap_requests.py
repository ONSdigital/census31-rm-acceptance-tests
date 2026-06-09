import requests
from google.auth.transport.requests import Request
from google.oauth2 import id_token

from config import Config


def make_request(method: str = "GET", url: str = None,
                 iap_client_id: str = Config.SUPPORT_TOOL_IAP_CLIENT_ID, **kwargs) -> requests.Response:
    """Make an IAP authorized request if IAP config is present
    Kwargs:
      method: The request method to use
              ('GET', 'OPTIONS', 'HEAD', 'POST', 'PUT', 'PATCH', 'DELETE')
      url: The Identity-Aware Proxy-protected URL to fetch.
      iap_client_id: (Optional) The IAP Client ID to use for authentication. If not configured, it will fall back on
                     a regular, unauthenticated request. Defaults to the configured Support Tool Client if present.
      **kwargs: Any of the parameters defined for the request function:
                https://github.com/requests/requests/blob/master/requests/api.py
    """
    if iap_client_id:
        return _make_iap_request(method, url, iap_client_id, **kwargs)
    return requests.request(method, url, **kwargs)


def _make_iap_request(method: str = 'GET', url: str = None, iap_client_id: str = None, **kwargs) -> requests.Response:
    """Makes a request to an application protected by Identity-Aware Proxy.
    Args:
      method: The request method to use
              ('GET', 'OPTIONS', 'HEAD', 'POST', 'PUT', 'PATCH', 'DELETE')
      url: The Identity-Aware Proxy-protected URL to fetch.
      **kwargs: Any of the parameters defined for the request function:
                https://github.com/requests/requests/blob/master/requests/api.py
                If no timeout is provided, it is set to 90 by default.
    Returns:
      The requests Response object return by the requests call
    """

    # Set the default timeout, if missing
    if 'timeout' not in kwargs:
        kwargs['timeout'] = 90

    # Obtain an OpenID Connect (OIDC) token from metadata server or using service account.
    open_id_connect_token = id_token.fetch_id_token(Request(), iap_client_id)

    # Initialise headers if none are passed in the kwargs
    if 'headers' not in kwargs:
        kwargs['headers'] = {}

    # Set an authorization header containing "Bearer " followed by a
    # Google-issued OpenID Connect token for the service account.
    kwargs['headers']['Proxy-Authorization'] = f'Bearer {open_id_connect_token}'

    return requests.request(method, url, **kwargs)
