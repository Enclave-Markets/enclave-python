# %%
"""
BaseClient handles basic requests and auth that are common across each Client such as Spot, Perps, Cross.
"""


import hashlib
import hmac
import os
import time
import urllib.parse as urlparse
from typing import Final

import requests
import requests.auth

# from requests import models
from . import models

DEFAULT_TIMEOUT: Final[float] = 10


class BaseClient:
    """A base client has a requests.Session and handles basic requests and auth."""

    def __init__(self, api_key: str, api_secret: str, base_url: str):
        self._base = base_url
        self.s = requests.Session()
        self.s.auth = ApiAuth(api_key, api_secret)

    def _request(
        self, method: str, path: str, body: str = "", headers: dict = None, timeout: float = DEFAULT_TIMEOUT
    ) -> requests.Response:
        method = method.upper()
        if method not in models.VERBS:
            raise ValueError(f"Unsupported HTTP verb {method=}.")

        headers = headers if headers else {}

        url: str = urlparse.urljoin(self._base, path).strip("/")

        return self.s.request(method, url, data=body, headers=headers, timeout=timeout)

    def get(
        self, path: str, body: str = "", headers: dict = None, timeout: float = DEFAULT_TIMEOUT
    ) -> requests.Response:
        return self._request(models.GET, path, body, headers, timeout)

    def post(
        self, path: str, body: str = "", headers: dict = None, timeout: float = DEFAULT_TIMEOUT
    ) -> requests.Response:
        return self._request(models.POST, path, body, headers, timeout)

    def delete(
        self, path: str, body: str = "", headers: dict = None, timeout: float = DEFAULT_TIMEOUT
    ) -> requests.Response:
        return self._request(models.DELETE, path, body, headers, timeout)

    def put(
        self, path: str, body: str = "", headers: dict = None, timeout: float = DEFAULT_TIMEOUT
    ) -> requests.Response:
        return self._request(models.PUT, path, body, headers, timeout)


class ApiAuth(requests.auth.AuthBase):
    """This class handles API authentication for the requests.Session.
    Before every request the call method is invoked which calculates the auth hash and updates the headers."""

    def __init__(self, api_key: str, api_secret: str):
        self._key = api_key
        self.__secret = api_secret

    def __call__(self, r):
        parsed = urlparse.urlsplit(r.path_url, allow_fragments=False)
        clean_path = f'{parsed.path}{"?" if parsed.query else ""}{parsed.query}'

        timestamp = int(time.time() * 1_000)
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


class EnclaveResponse:
    def __init__(self, response_code: int, response_data):
        self.code = response_code
        self.data = response_data
