"""
client is the Enclave SDK and contains an instance of Cross, Perps, and Spot to make requests to each.
"""

from . import _baseclient, _cross, _perps, _spot


class Client:
    def __init__(self, api_key: str, api_secret: str, base_url: str) -> None:
        base = _baseclient.BaseClient(api_key, api_secret, base_url)
        self.cross = _cross.Cross(base)
        self.perps = _perps.Perps(base)
        self.cross = _spot.Spot(base)
