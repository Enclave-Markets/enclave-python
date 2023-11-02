"""
Spot contains the Spot specific API and calls an instance of BaseClient to make requests and handle auth.
"""
from . import _baseclient


class Spot:
    def __init__(self, base_client: _baseclient.BaseClient):
        self.bc = base_client
