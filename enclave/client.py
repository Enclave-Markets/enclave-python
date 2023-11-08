"""
client is the Enclave SDK and contains an instance of Cross, Perps, and Spot to make requests to each.
"""
import json
import os
from decimal import Decimal
from typing import List, Optional, Union

import requests

from . import _baseclient, _cross, _perps, _spot, models


class Client:
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
    # https://enclave-markets.notion.site/Common-REST-API-9d546fa6282b4bad87ef43d189b9071b
    # We could pass kwargs and have it unpacked into `get`, but keeping it simple this isn't allowed.

    def authed_hello(self) -> requests.Response:
        """Make a request to the authed hello endpoint.

        `GET /authedHello`

        Response:
        ```
        {
            "result": "ACCOUNT_ID",
            "success": true
        }
        ```

        Requires: view."""

        return self.bc.get("/authedHello")

    def get_address_book(self) -> requests.Response:
        """Make a request to the address book endpoint.

        `GET /v0/address_book`

        Response:
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

    def get_markets(self) -> requests.Response:
        """Make a request to the markets endpoint, returns the markets tradeable by the user.

        `GET /v1/markets`

        Response:
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

    def get_balance(self, coin: str) -> requests.Response:
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

    def get_balances(self) -> requests.Response:
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

    def get_deposit_addresses(self, coins: List[str]) -> requests.Response:
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

    def get_deposits(self) -> requests.Response:
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

    def get_deposit(self, txid: str) -> requests.Response:
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
    def get_deposits_csv(
        self, *, start_secs: Optional[int] = None, end_secs: Optional[int] = None
    ) -> requests.Response:
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

    def get_withdrawals(self) -> requests.Response:
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

    def get_withdrawal(self, txid: str) -> requests.Response:
        """Gets a withdrawal by transaction ID.

        `GET /v0/wallet/withdrawals/<TxID>`

        Response:
        ```
        {
            "result": {
                "address": "0x123abc...", "coin": "AVAX", "size": "10000", "status": "WITHDRAWAL_CONFIRMED",
                "time": "2019-03-05T09:56:55.728933+00:00", "txid": "0xabc123...", "withdrawal_id": "1a2b3c..."
            },
            "success": true
        }
        ```

        Requires: view."""

        return self.bc.get(f"/v0/wallet/withdrawals/{txid}")

    def get_withdrawals_csv(
        self, *, start_secs: Optional[int] = None, end_secs: Optional[int] = None
    ) -> requests.Response:
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

    def provision_address(self, coin: str) -> requests.Response:
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

    def withdraw(self, to_address: str, amount: Union[str, Decimal], custom_id: str, coin: str) -> requests.Response:
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
