"""
BaseClient handles basic requests and auth that are common across each Client such as Spot, Perps, Cross.
"""


import requests


class BaseClient:
    def __init__(self, api_key: str, api_secret: str, base_url: str = "https://api.enclave.market"):
        self._key = api_key
        self.__secret = api_secret
        self._base = base_url
        self.s = requests.Session()
