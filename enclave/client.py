"""
client is the Enclave SDK and contains an instance of Cross, Perps, and Spot to make requests.

The Client class is the intended way to interface with the SDK.
Modules beginning with an underscore such as _spot are not intended to be used directly.
"""
import json
import os
import time
from decimal import Decimal
from typing import List, Optional, Union

import requests

from . import _baseclient, _cross, _perps, _spot, models

Res = requests.Response


class Client:
    """Client defines the common API endpoints and convenience methods,
    as well as a reference to Cross, Perps, and Spot objects to make requests to each.
    It contains a BaseClient object to make requests to the API.

    See (the Enclave docs)[https://docs.enclave.market] for more information.

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

    @classmethod
    def from_api_file(cls, api_path: str, base_url: str):
        """Create a Client from a file with the key id on the first line and the api secret on the second line."""
        path = os.path.normpath(api_path)
        with open(path, "r", encoding="utf8") as api_file:
            api_key: str = api_file.readline().strip()
            api_secret: str = api_file.readline().strip()

        return cls(api_key, api_secret, base_url)

    # Common REST API
    # We could pass kwargs and have it unpacked into `get`, but keeping it simple this isn't allowed.
    # https://enclave-markets.notion.site/Common-REST-API-9d546fa6282b4bad87ef43d189b9071b

    def wait(self, sleep_time: float = 1, fail_after: float = 10) -> bool:
        """Wait for the API to be ready, sleeping for `sleep_time` seconds between requests (default 1).
        Optional fail after `fail_after` seconds (default 10).

        Returns True if the API is ready, False if it timed out.
        """
        start = time.time()
        while not (self.bc.get("/status").ok):
            if time.time() - start > fail_after:
                return False
            time.sleep(sleep_time)
        return True

    def authed_hello(self) -> Res:
        """Make a request to the authed hello endpoint.

        `GET /authedHello`

        Returns:
        ```
        {
            "result": "ACCOUNT_ID",
            "success": true
        }
        ```

        Requires: view."""

        return self.bc.get("/authedHello")

    def get_address_book(self) -> Res:
        """Make a request to the address book endpoint.

        `GET /v0/address_book`

        Returns:
        ```
        {
            "result": {
                "addressBook": [
                    "0xabc...",
                    "0x123..."
                ]
            },
            "success": true
        }
        ```

        Requires: view."""

        return self.bc.get("/v0/address_book")

    def get_markets(self) -> Res:
        """Make a request to the markets endpoint, returns the markets tradeable by the user.

        `GET /v1/markets`

        Returns:
        ```
        {
            "result": {
                "cross": {
                    "tradingPairs": [
                        {
                            "pair": {
                                "base": "AVAX",
                                "quote": "USDC"
                            },
                            "decimalPlaces": 6
                        },
                        {
                            "pair": {
                                "base": "AAVE",
                                "quote": "USDC"
                            },
                            "decimalPlaces": 6
                        }
                    ]
                },
                "spot": {
                    "tradingPairs": [
                        {
                            "pair": {
                                "base": "AVAX",
                                "quote": "USDC"
                            },
                            "baseIncrement": "0.001",
                            "quoteIncrement": "0.01"
                        },
                        {
                            "pair": {
                                "base": "AVAX",
                                "quote": "ETH"
                            },
                            "baseIncrement": "0.001",
                            "quoteIncrement": "0.000001"
                        }
                    ]
                },
                "tokenConfig": [
                    {
                        "id": "AVAX",
                        "name": "Avalanche",
                        "decimals": 6,
                        "network": "avalanche",
                        "assetType": "native",
                        "nativeAssetName": "avalanche",
                        "coinGeckoId": "avalanche-2",
                        "coinGeckoCurrency": "",
                        "bridgeInfoUrl": "",
                        "description": "",
                        "minOrderSize": "0.01",
                        "maxOrderSize": "28819"
                    },
                    {
                        "id": "USDC",
                        "name": "USD Coin",
                        "decimals": 2,
                        "network": "ethereum",
                        "assetType": "native",
                        "nativeAssetName": "",
                        "coinGeckoId": "usd-coin",
                        "coinGeckoCurrency": "usd",
                        "bridgeInfoUrl": "",
                        "description": "",
                        "minOrderSize": "0.01",
                        "maxOrderSize": "500000"
                    }
                ]
            },
            "success": true
        }
        ```

        Requires: view."""

        return self.bc.get("/v1/markets")

    def get_balance(self, coin: str) -> Res:
        """Gets balance of a specific asset.

        `POST /v0/get_balance`

        Request:
        `{ "symbol": "COIN" }`
        symbol: str, required.

        Response:
        ```
        {
            "result": {
                "accountId": "5577006791947779410",
                "freeBalance": "3000",
                "reservedBalance": "7000",
                "symbol": "AVAX",
                "totalBalance": "10000"
            },
            "success": true
        }
        ```

        Requires: view."""

        body = f'{{ "symbol": "{coin}" }}'
        return self.bc.post("/v0/get_balance", body=body)

    def get_balances(self) -> Res:
        """Gets balances of all assets in wallet

        `GET /v0/wallet/balances`

        Response:
        ```
        {
            "result": [
                {
                    "coin": "AVAX", free": "3000", "reserved": "7000", "total": "10000", "usdValue": "150000"
                },
                {
                    "coin": "AAVE", "total": "0", "reserved": "0", "free": "0", "usdValue": "0"
                }
            ],
            "success": true
        }
        ```

        Requires: view."""

        return self.bc.get("/v0/wallet/balances")

    def get_deposit_addresses(self, coins: List[str]) -> Res:
        """Gets all provisioned addresses for the coins for an account.

        `POST /v0/wallet/deposit_address/list`

        Response:
        ```
        {
            "result": [
                {
                    "address": "0x123...", "coin": "AVAX"
                },
                {
                    "address": "0xabc...", "coin": "USDC"
                }
            ],
            "success": true
        }
        ```

                Requires: view."""

        body = f'{{ "coins": {coins} }}'
        return self.bc.post("/v0/wallet/deposit_address/list", body=body)

    def get_deposits(self) -> Res:
        """Gets all deposits for an account.
        Reverse chronological array encapsulated in generic response wrapper.

        `GET /v0/wallet/deposits`

        Response:
        ```
        {
            "result": [
                {
                    "coin": "AVAX", "currentConfirmations": 25, "requiredConfirmations": 25, "size": "10000", "status": "confirmed",
                    "time": "2019-03-05T09:56:55.728933+00:00", "txid": "0x123abc..."
                },
                {
                    "coin": "AVAX", "currentConfirmations": 10, "requiredConfirmations": 25, "size": "10000", "status": "confirmed",
                    "time": "2019-04-05T09:56:55.728933+00:00", "txid": "0xabc123..."
                }
            ],
            "success": true
        }
        ```

        Requires: view."""

        return self.bc.get("/v0/wallet/deposits")

    def get_deposit(self, txid: str) -> Res:
        """Gets a deposit by transaction ID.

        `GET /v0/wallet/deposits/<TxID>`

        Response:
        ```
        {
            "result": {
                "coin": "AVAX", "currentConfirmations": 25, "requiredConfirmations": 25, "size": "10000", "status": "confirmed",
                "time": "2019-03-05T09:56:55.728933+00:00", "txid": "0x123abc..."
            },
            "success": true
        }
        ```

        Requires: view."""

        return self.bc.get(f"/v0/wallet/deposits/{txid}")

    # TODO: this is a case where we could have validation. like to check if end is after start and nothing is negative or zero?
    # TODO: this is a response that can't be json encoded by the base class
    def get_deposits_csv(self, *, start_secs: Optional[int] = None, end_secs: Optional[int] = None) -> Res:
        # `*` enforces keyword only arguments
        """Gets deposits for an account within the start and end times

        `POST /v0/wallet/deposits/csv`

        Response:
        `CSV formatted text, sorted reverse chronologically`

        Requires: view."""

        body = {}
        if start_secs is not None:
            body["start_time"] = start_secs
        if end_secs is not None:
            body["end_time"] = end_secs
        return self.bc.post("/v0/wallet/deposits/csv", body=json.dumps(body))

    def get_withdrawals(self) -> Res:
        """Gets all withdrawals for an account.

        `GET /v0/wallet/withdrawals`

        Response:
        ```
        {
            "result": [
                {
                    "address": "0x123abc...", "coin": "AVAX", "size": "10000", "status": "WITHDRAWAL_CONFIRMED",
                    "time": "2019-03-05T09:56:55.728933+00:00", "txid": "0xabc123...", "withdrawal_id": "1a2b3c..."
                },
                {
                    "address": "0x456def...", "coin": "AVAX", "size": "10000", "status": "WITHDRAWAL_CONFIRMED",
                    "time": "2019-04-05T09:56:55.728933+00:00", "txid": "0xdef456...", "withdrawal_id": "4d5e6f..."
                }
            ],
            "success": true
        }
        ```

        Requires: view."""

        return self.bc.get("/v0/wallet/withdrawals")

    def get_withdrawal(self, *, custom_id: Optional[str] = None, internal_id: Optional[str] = None) -> Res:
        """
        Get withdrawal status.
        Exactly one of either custom_id or internal_id must be provided.

        `POST /v0/get_withdrawal_status`

        Request:
        `{"customer_withdrawal_id": custom_id}` if custom_id
        or
        `{"withdrawal_id": internal_id}` if internal_id

        Response:
        ```
        {
            "result": {
                "confirmation_number": 1,
                "original_request": {
                    "account_id": "5577006791947779410",
                    "address": "0x064A94c753CBf65D1Bc484F6D41897b38250fbfF",
                    "amount": "10",
                    "customer_withdrawal_id": "abc123",
                    "symbol": "AVAX"
                },
                "txid": "c06638d16869699138ec9d9fa57a6ac4d21068bfafc4211305d636f80b77a2101",
                "withdrawal_id": "06638d16869699138ec9d9fa57a6ac4d21068bfafc4211305d636f80b77a2101",
                "withdrawal_status": "WITHDRAWAL_PENDING"
            },
            "success": true
        }
        ```

        Requires: view."""

        if (not any((custom_id, internal_id))) or all((custom_id, internal_id)):
            raise ValueError("Must provide exactly one of custom_id or internal_id")

        body = {"customer_withdrawal_id": custom_id} if custom_id else {"withdrawal_id": internal_id}
        return self.bc.post("/v0/get_withdrawal_status", body=json.dumps(body))

    def get_withdrawal_by_txid(self, txid: str) -> Res:
        """Gets a withdrawal by transaction ID.

        `GET /v0/wallet/withdrawals/<TxID>`

        Response:
        ```
        {
            "result": {
                "address": "0x123abc...",
                "coin": "AVAX",
                "size": "10000",
                "status": "WITHDRAWAL_CONFIRMED",
                "time": "2019-03-05T09:56:55.728933+00:00", "txid": "0xabc123...", "withdrawal_id": "1a2b3c..."
            },
            "success": true
        }
        ```

        Requires: view."""

        return self.bc.get(f"/v0/wallet/withdrawals/{txid}")

    def get_withdrawals_csv(self, *, start_secs: Optional[int] = None, end_secs: Optional[int] = None) -> Res:
        """Gets withdrawals for an account within the start and end times

        `POST /v0/wallet/withdrawals/csv`

        Response:
        `CSV formatted text, sorted reverse chronologically`

        Requires: view."""

        body = {}
        if start_secs is not None:
            body["start_time"] = start_secs
        if end_secs is not None:
            body["end_time"] = end_secs
        return self.bc.post("/v0/wallet/withdrawals/csv", body=json.dumps(body))

    def provision_address(self, coin: str) -> Res:
        """Provisions an address for deposit of an asset

        `POST /v0/provision_address`

        Request:
        `{"symbol": "AVAX"}`

        Response:
        ```
        {
            "result": {
                "accountId": "5572106791847779410", "address": "0x074B94d653CBf65D1Bc484F6D41897b38250fbfF", "symbol": "AVAX"
            },
            "success": true
        }
        ```

        Requires: view + transfer."""

        body = f'{{ "symbol": "{coin}" }}'
        return self.bc.post("/v0/provision_address", body=body)

    def withdraw(self, to_address: str, amount: Union[str, Decimal], custom_id: str, coin: str) -> Res:
        """Initiates a withdrawal

        `POST /v0/withdraw`

        Request:
        ```
        {
            "address": "0x074B94d653CBf65D1Bc484F6D41897b38250fbfF",
            "amount": "10",
            "customer_withdrawal_id": "abc123",
            "symbol": "AVAX"
        }
        ```

        Response:
        ```
        {
            "result": {
                "customer_withdrawal_id": "abc123",
                "withdrawal_id": "41ff4b35112ccfa3e466f302c914f323f5687e048a8e2fd82bcdcdcb9eb47571",
                "withdrawal_status": "WITHDRAWAL_PENDING",
            },
            "success": true
        }
        ```

        Requires: view + transfer."""

        body = {}
        body.update(
            {
                "address": to_address,
                "amount": str(amount),
                "customer_withdrawal_id": custom_id,
                "symbol": coin,
            }
        )
        return self.bc.post("/v0/withdraw", body=json.dumps(body))
