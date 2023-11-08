"""
BaseClient handles basic requests and auth that are common across Spot, Perps, and Cross.
"""


import hashlib
import hmac
import time
import urllib.parse as urlparse
from typing import Any, Dict, Final, List, Optional, Tuple, Union

import requests
import requests.auth

from . import models

DEFAULT_TIMEOUT_SECS: Final[float] = 10

OptDict = Optional[dict]


class BaseClient:
    """A base client has a requests.Session and handles basic requests and auth."""

    def __init__(self, api_key: str, api_secret: str, base_url: str):
        self._base_url = base_url
        self.s = requests.Session()
        self.s.auth = ApiAuth(api_key, api_secret)
        self.s.headers.update({"user-agent": "enclave-python"})

    def _request(
        self,
        method: str,
        path: str,
        body: str = "",
        params: OptDict = None,
        headers: OptDict = None,
        timeout: float = DEFAULT_TIMEOUT_SECS,
    ) -> requests.Response:
        method = method.upper()
        if method not in models.VERBS:
            raise ValueError(f"Unsupported HTTP verb {method=}.")

        headers = headers if headers else {}

        url: str = urlparse.urljoin(self._base_url, path).strip("/")

        return self.s.request(method, url, data=body, params=params, headers=headers, timeout=timeout)

    def get(
        self,
        path: str,
        body: str = "",
        params: OptDict = None,
        headers: OptDict = None,
        timeout: float = DEFAULT_TIMEOUT_SECS,
    ) -> requests.Response:
        return self._request(models.GET, path, body, params, headers, timeout)

    def post(
        self,
        path: str,
        body: str = "",
        params: OptDict = None,
        headers: OptDict = None,
        timeout: float = DEFAULT_TIMEOUT_SECS,
    ) -> requests.Response:
        return self._request(models.POST, path, body, params, headers, timeout)

    def delete(
        self,
        path: str,
        body: str = "",
        params: OptDict = None,
        headers: OptDict = None,
        timeout: float = DEFAULT_TIMEOUT_SECS,
    ) -> requests.Response:
        return self._request(models.DELETE, path, body, params, headers, timeout)

    def put(
        self,
        path: str,
        body: str = "",
        params: OptDict = None,
        headers: OptDict = None,
        timeout: float = DEFAULT_TIMEOUT_SECS,
    ) -> requests.Response:
        return self._request(models.PUT, path, body, params, headers, timeout)

    # @staticmethod
    # def build_params(params: Union[Dict[str, Any], List[Tuple[str, Any]]]) -> str:
    #     """Builds a query string from a dict or of params.
    #     Filters None values from the params.

    #     If there aren't non None params, returns an empty string, otherwise return ?param=value&param2=value etc.
    #     """
    #     if isinstance(params, dict):  # make both into list of tuples
    #         params = list(params.items())

    #     query = urlparse.urlencode(  # Concat and encode.
    #         [(k, v) for k, v in params if v is not None]  # Filter None values.
    #     )
    #     return f"?{query}" if query else ""


class ApiAuth(requests.auth.AuthBase):
    """This class handles API authentication for the requests.Session.
    Before every request the call method is invoked which calculates the auth hash and updates the headers.

    See
    https://enclave-markets.notion.site/Rest-API-Authentication-3956dcfecbdc48269031cf052926c90d#1d48123af71945b48e2c56a32a3eb7a3
    for API Authentication details.
    """

    def __init__(self, api_key: str, api_secret: str):
        self._key = api_key
        self.__secret = api_secret

    def __call__(self, r: requests.PreparedRequest) -> requests.PreparedRequest:
        parsed = urlparse.urlsplit(r.path_url, allow_fragments=False)
        clean_path = parsed.path
        if parsed.query:
            clean_path += f"?{parsed.query}"

        timestamp = int(time.time() * 1_000)  # time returns seconds, server expects ms.
        body = r.body if r.body else ""

        mac = hmac.new(self.__secret.encode(), f"{str(timestamp)}{r.method}{clean_path}{body}".encode(), hashlib.sha256)

        r.headers.update(
            {
                "ENCLAVE-KEY-ID": self._key,
                "ENCLAVE-TIMESTAMP": str(timestamp),
                "ENCLAVE-SIGN": mac.hexdigest(),
            }
        )

        return r
