# %%
"""
client implements the Enclave API and contains an instance of Cross, Perps, and Spot to make requests.

The Client class is the intended way to interface with the Enclave Markets API.
Modules beginning with an underscore such as _spot are not intended to be used directly.
"""
from __future__ import annotations  # self type only 3.11+

import json
import os
import time
from decimal import Decimal
from typing import List, Optional, Union

from . import _baseclient, _cross, _perps, _spot, models
from .models import Res


class Client:
    """Client defines the common API endpoints and convenience methods,
    as well as a reference to Cross, Perps, and Spot objects to make requests to each.
    It contains a BaseClient object to make requests to the API.

    See the [Enclave docs](https://docs.enclave.market) for more information.

    Usage is Client(...).a_common_endpoint(...) for common endpoints and
    Client(...).cross.a_cross_endpoint(...) for cross endpoints, etc.

    Client can either be initialized with an API key id and secret as strings
    (passed from ENV variable, dotenv file, hardcoded, etc.),
    or from a file using `from_api_file` with the key id on the first line and the secret on the second line.
    """

    def __init__(self, api_key: str, api_secret: str, base_url: str = models.PROD):
        self.bc = _baseclient.BaseClient(api_key, api_secret, base_url)

        self.cross = _cross.Cross(self.bc)
        self.perps = _perps.Perps(self.bc)
        self.spot = _spot.Spot(self.bc)
        
        self.wait_until_ready()

        response = self.authed_hello()
        if response.ok:
            self.account_id = response.json()["result"]
        else:
            raise ValueError(f"Failed to auth and fetch account ID: {response.text}")

    @classmethod
    def from_api_file(cls, api_path: str, base_url: str) -> Client:
        """Create a Client from a file with the key id on the first line and the api secret on the second line."""
        path = os.path.normpath(api_path)
        with open(path, "r", encoding="utf8") as api_file:
            api_key: str = api_file.readline().strip()
            api_secret: str = api_file.readline().strip()

        return cls(api_key, api_secret, base_url)

    # Common REST API
    # We could pass kwargs and have it unpacked into `get`, but keeping it simple this isn't allowed.
    # https://enclave-markets.notion.site/Common-REST-API-9d546fa6282b4bad87ef43d189b9071b

    def wait_until_ready(self, sleep_time: float = 1, fail_after: float = 10) -> bool:
        """Wait for the API to be ready,
        sleeping for `sleep_time` seconds between requests (default 1).
        Optional fail after `fail_after` seconds (default 10).

        Returns True if the API is ready, False if it timed out.
        """
        start = time.time()
        while not self.bc.get("/status").ok:
            if fail_after > 0 and ((time.time() - start) > fail_after):
                return False
            time.sleep(sleep_time)
        return True

    def authed_hello(self) -> Res:
        """Make a request to the authed hello endpoint.

        `GET /authedHello`"""

        return self.bc.get("/authedHello")

    def get_address_book(self) -> Res:
        """Make a request to the address book endpoint.

        `GET /v0/address_book`"""

        return self.bc.get("/v0/address_book")

    def get_markets(self) -> Res:
        """Make a request to the markets endpoint, returns the markets tradeable by the user.

        `GET /v1/markets`"""

        return self.bc.get("/v1/markets")

    def get_balance(self, coin: str) -> Res:
        """Gets balance of a specific asset.

        `POST /v0/get_balance`

        Request:
        `{ "symbol": "COIN" }`
        symbol: str, required."""

        body = f'{{ "symbol": "{coin}" }}'
        return self.bc.post("/v0/get_balance", body=body)

    def get_balances(self) -> Res:
        """Gets balances of all assets in wallet

        `GET /v0/wallet/balances`"""

        return self.bc.get("/v0/wallet/balances")

    def get_deposit_addresses(self, coins: List[str]) -> Res:
        """Gets all provisioned addresses for the coins for an account.

        `POST /v0/wallet/deposit_address/list`

        Request:
        `{ "coins": ["AVAX", "ETH"] }` list of strings of coin symbols, required."""

        body = json.dumps({"coins": coins})
        return self.bc.post("/v0/wallet/deposit_address/list", body=body)

    def get_deposits(self) -> Res:
        """Gets all deposits for an account.
        Reverse chronological array encapsulated in generic response wrapper.

        `GET /v0/wallet/deposits`"""

        return self.bc.get("/v0/wallet/deposits")

    def get_deposit(self, txid: str) -> Res:
        """Gets a deposit by transaction ID.

        `GET /v0/wallet/deposits/<TxID>`"""

        return self.bc.get(f"/v0/wallet/deposits/{txid}")

    # TODO: this is a case where we could have validation. like to check if end is after start and nothing is negative or zero?
    # TODO: this is a response that can't be json encoded by the base class
    def get_deposits_csv(self, *, start_secs: Optional[int] = None, end_secs: Optional[int] = None) -> Res:
        # `*` enforces keyword only arguments
        """Gets deposits for an account within the start and end times (optional)

        `POST /v0/wallet/deposits/csv`"""

        body = {}
        if start_secs is not None:
            body["start_time"] = start_secs
        if end_secs is not None:
            body["end_time"] = end_secs
        return self.bc.post("/v0/wallet/deposits/csv", body=json.dumps(body))

    def get_withdrawals(self) -> Res:
        """Gets all withdrawals for an account.

        `GET /v0/wallet/withdrawals`"""

        return self.bc.get("/v0/wallet/withdrawals")

    def get_withdrawal(self, *, custom_id: Optional[str] = None, internal_id: Optional[str] = None) -> Res:
        """
        Get withdrawal status.
        Exactly one of either custom_id or internal_id must be provided.

        `POST /v0/get_withdrawal_status`

        Request:
        `{"customer_withdrawal_id": custom_id}` if custom_id
        or
        `{"withdrawal_id": internal_id}` if internal_id"""

        if (not any((custom_id, internal_id))) or all((custom_id, internal_id)):
            raise ValueError("Must provide exactly one of custom_id or internal_id")

        body = {"customer_withdrawal_id": custom_id} if custom_id else {"withdrawal_id": str(internal_id)}
        return self.bc.post("/v0/get_withdrawal_status", body=json.dumps(body))

    def get_withdrawal_by_txid(self, txid: str) -> Res:
        """Gets a withdrawal by transaction ID.

        `GET /v0/wallet/withdrawals/<TxID>`"""

        return self.bc.get(f"/v0/wallet/withdrawals/{txid}")

    def get_withdrawals_csv(self, *, start_secs: Optional[int] = None, end_secs: Optional[int] = None) -> Res:
        """Gets withdrawals for an account within the start and end times (optional)

        `POST /v0/wallet/withdrawals/csv`"""

        body = {}
        if start_secs is not None:
            body["start_time"] = start_secs
        if end_secs is not None:
            body["end_time"] = end_secs
        return self.bc.post("/v0/wallet/withdrawals/csv", body=json.dumps(body))

    def provision_address(self, coin: str, wallet: Optional[str] = None) -> Res:
        """Provisions an address for deposit of an asset, wallet is optional and can be main or margin

        `POST /v0/provision_address`

        Request:
        ```
        {
            "symbol": "AVAX",
            "deposit_destination": {
                "id": "327719837281695541",
                "wallet": "main"
            }
        }
        ```"""

        body: dict[str, Union[str, dict[str, str]]] = {"symbol": coin}
        if wallet is not None:
            if wallet not in ["main", "margin"]:
                raise ValueError("wallet must be either 'main' or 'margin'")
            body["deposit_destination"] = {"id": self.account_id, "wallet": wallet}
        return self.bc.post("/v0/provision_address", body=json.dumps(body))

    def withdraw(self, to_address: str, amount: Union[str, Decimal], custom_id: str, coin: str, wallet: Optional[str] = None) -> Res:
        """Initiates a withdrawal, wallet is optional and can be main or margin

        `POST /v0/withdraw`

         Request:
        ```
        {
            "address": "0x074B94d653CBf65D1Bc484F6D41897b38250fbfF",
            "amount": "10",
            "customer_withdrawal_id": "abc123",
            "symbol": "AVAX",
            "from": {
                "id": "327719837281695541",
                "wallet": "main"
            }
        }
        ```"""

        body: dict[str, Union[str, dict[str, str]]] = {
            "address": to_address,
            "amount": str(amount),
            "customer_withdrawal_id": custom_id,
            "symbol": coin,
        }
        if wallet is not None:
            if wallet not in ["main", "margin"]:
                raise ValueError("wallet must be either 'main' or 'margin'")
            body["from"] = {"id": self.account_id, "wallet": wallet}
        return self.bc.post("/v0/withdraw", body=json.dumps(body))
