"""
Client is the Enclave SDK and contains an instance of Cross, Perps, and Spot to make requests to each.
"""
import os

from . import _baseclient, _cross, _perps, _spot


class Client:
    def __init__(self, api_key: str, api_secret: str, base_url: str = "https://api.enclave.market"):
        self.base_client = _baseclient.BaseClient(api_key, api_secret, base_url)

        self.cross = _cross.Cross(self.base_client)
        self.perps = _perps.Perps(self.base_client)
        self.spot = _spot.Spot(self.base_client)

    @classmethod
    def from_api_file(cls, api_path: str, base_url: str):
        """Create a Client from a file with the key id on the first line and the api secret on the second line."""

        path = os.path.normpath(api_path)
        with open(path, "r", encoding="utf8") as api_file:
            api_key: str = api_file.readline().strip()
            api_secret: str = api_file.readline().strip()
        return cls(api_key, api_secret, base_url)

    def _request(self):
        ...

    def hello(self):
        ...

    def authed_hello(self):
        ...
