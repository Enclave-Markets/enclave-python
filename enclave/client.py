"""
Client is the Enclave SDK and contains an instance of Cross, Perps, and Spot to make requests to each.
"""
import json
import os
from decimal import Decimal
from typing import List, Optional, Union

import requests

from . import _baseclient, _cross, _perps, _spot, models


class Client:
    def __init__(self, api_key: str, api_secret: str, base_url: str = models.PROD):
        self.baseclient = _baseclient.BaseClient(api_key, api_secret, base_url)

        self.cross = _cross.Cross(self.baseclient)
        self.perps = _perps.Perps(self.baseclient)
        self.spot = _spot.Spot(self.baseclient)

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

    def authed_hello(self) -> requests.Response:
        """Make a request to the authed hello endpoint.

        `GET /authedHello`

        Returns:
            `{'success': true, 'result': 'ACCOUNT_ID'}`

        We could pass kwargs and have it unpacked into `get`, but keeping it simple this isn't allowed.

        Requires: view."""

        return self.baseclient.get("/authedHello")

    def get_address_book(self) -> requests.Response:
        """Make a request to the address book endpoint.

        `GET /v0/address_book`

        Returns:
            `{
            'success': true,
            'result': {"addressBook": ["0xabc...", "0x123..." ]}
            }`


        Requires: view.
        """

        return self.baseclient.get("/v0/address_book")

    def get_markets(self) -> requests.Response:
        """Make a request to the markets endpoint, returns the markets tradeable by the user.

                `GET /v1/markets`

                Returns:
                `{
                "success": true,
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
                    },
                    {
                       "pair": {
                          "base": "BTC.b",
                          "quote": "USDC"
                       },
                       "decimalPlaces": 6
                    },
                    {
                       "pair": {
                          "base": "ETH",
                          "quote": "USDC"
                       },
                       "decimalPlaces": 6
                    },
                    {
                       "pair": {
                          "base": "LINK",
                          "quote": "USDC"
                       },
                       "decimalPlaces": 6
                    },
                    {
                       "pair": {
                          "base": "WBTC",
                          "quote": "USDC"
                       },
                       "decimalPlaces": 6
                    },
                    {
                       "pair": {
                          "base": "AVAX",
                          "quote": "USDCa"
                       },
                       "decimalPlaces": 6
                    },
                    {
                       "pair": {
                          "base": "BTC.b",
                          "quote": "USDCa"
                       },
                       "decimalPlaces": 6
                    },
                    {
                       "pair": {
                          "base": "ETH",
                          "quote": "USDCa"
                       },
                       "decimalPlaces": 6
                    },
                    {
                       "pair": {
                          "base": "WBTC",
                          "quote": "USDCa"
                       },
                       "decimalPlaces": 6
                    },
                    {
                       "pair": {
                          "base": "AVAX",
                          "quote": "ETH"
                       },
                       "decimalPlaces": 6
                    },
                    {
                       "pair": {
                          "base": "AVAX",
                          "quote": "BTC.b"
                       },
                       "decimalPlaces": 6
                    },
                    {
                       "pair": {
                          "base": "AVAX",
                          "quote": "WBTC"
                       },
                       "decimalPlaces": 6
                    },
                    {
                       "pair": {
                          "base": "AAVE",
                          "quote": "AVAX"
                       },
                       "decimalPlaces": 6
                    },
                    {
                       "pair": {
                          "base": "AAVE",
                          "quote": "BTC.b"
                       },
                       "decimalPlaces": 6
                    },
                    {
                       "pair": {
                          "base": "AAVE",
                          "quote": "ETH"
                       },
                       "decimalPlaces": 6
                    },
                    {
                       "pair": {
                          "base": "ETH",
                          "quote": "BTC.b"
                       },
                       "decimalPlaces": 6
                    },
                    {
                       "pair": {
                          "base": "ETH",
                          "quote": "WBTC"
                       },
                       "decimalPlaces": 6
                    },
                    {
                       "pair": {
                          "base": "LINK",
                          "quote": "AVAX"
                       },
                       "decimalPlaces": 6
                    },
                    {
                       "pair": {
                          "base": "LINK",
                          "quote": "BTC.b"
                       },
                       "decimalPlaces": 6
                    },
                    {
                       "pair": {
                          "base": "LINK",
                          "quote": "ETH"
                       },
                       "decimalPlaces": 6
                    },
                    {
                       "pair": {
                          "base": "WOOL",
                          "quote": "ETH"
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
                    },
                    {
                       "pair": {
                          "base": "ETH",
                          "quote": "USDC"
                       },
                       "baseIncrement": "0.00001",
                       "quoteIncrement": "1"
                    },
                    {
                       "pair": {
                          "base": "WBTC",
                          "quote": "USDC"
                       },
                       "baseIncrement": "0.000001",
                       "quoteIncrement": "1"
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
                    "id": "ETH",
                    "name": "Ethereum",
                    "decimals": 6,
                    "network": "ethereum",
                    "assetType": "native",
                    "nativeAssetName": "ethereum",
                    "coinGeckoId": "ethereum",
                    "coinGeckoCurrency": "eth",
                    "bridgeInfoUrl": "",
                    "description": "",
                    "minOrderSize": "0.001",
                    "maxOrderSize": "328"
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
                 },
                 {
                    "id": "LINK",
                    "name": "Chainlink",
                    "decimals": 6,
                    "network": "ethereum",
                    "assetType": "native",
                    "nativeAssetName": "chainlink",
                    "coinGeckoId": "chainlink",
                    "coinGeckoCurrency": "link",
                    "bridgeInfoUrl": "",
                    "description": "",
                    "minOrderSize": "0.01",
                    "maxOrderSize": "71650"
                 },
                 {
                    "id": "WBTC",
                    "name": "Wrapped Bitcoin",
                    "decimals": 6,
                    "network": "ethereum",
                    "assetType": "wrapped",
                    "nativeAssetName": "bitcoin",
                    "coinGeckoId": "wrapped-bitcoin",
                    "coinGeckoCurrency": "btc",
                    "bridgeInfoUrl": "",
                    "description": "",
                    "minOrderSize": "0.001",
                    "maxOrderSize": "25"
                 },
                 {
                    "id": "AAVE",
                    "name": "Aave",
                    "decimals": 6,
                    "network": "ethereum",
                    "assetType": "native",
                    "nativeAssetName": "aave",
                    "coinGeckoId": "aave",
                    "coinGeckoCurrency": "aave",
                    "bridgeInfoUrl": "",
                    "description": "",
                    "minOrderSize": "0.001",
                    "maxOrderSize": "1250"
                 },
                 {
                    "id": "USDCa",
                    "name": "USD Coin on Avalanche",
                    "decimals": 2,
                    "network": "avalanche",
                    "assetType": "native",
                    "nativeAssetName": "United States Dollar",
                    "coinGeckoId": "usd-coin",
                    "coinGeckoCurrency": "usd",
                    "bridgeInfoUrl": "",
                    "description": "",
                    "minOrderSize": "0.01",
                    "maxOrderSize": "500000"
                 },
                 {
                    "id": "BTC.b",
                    "name": "Bridged Bitcoin",
                    "decimals": 4,
                    "network": "avalanche",
                    "assetType": "bridged",
                    "nativeAssetName": "bitcoin",
                    "coinGeckoId": "wrapped-bitcoin",
                    "coinGeckoCurrency": "btc",
                    "bridgeInfoUrl": "https://support.avax.network/en/articles/6081464-core-extension-how-do-i-bridge-bitcoin-btc",
                    "description": "Bitcoin that is bridged to the Avalanche network",
                    "minOrderSize": "0.001",
                    "maxOrderSize": "25"
                 },
                 {
                    "id": "WOOL",
                    "name": "Wolf Game Wool",
                    "decimals": 6,
                    "network": "ethereum",
                    "assetType": "native",
                    "nativeAssetName": "wool",
                    "coinGeckoId": "wool",
                    "coinGeckoCurrency": "wool",
                    "bridgeInfoUrl": "",
                    "description": "",
                    "minOrderSize": "100",
                    "maxOrderSize": "100000000"
                 }
              ],
              "blockchainNetwork": [
                 {
                    "type": "ethereum",
                    "coin": "ETH",
                    "testnetName": "Ethereum Goerli testnet",
                    "mainnetName": "Ethereum mainnet",
                    "testnetBlockExplorerBaseUrl": "https://goerli.etherscan.io",
                    "mainnetBlockExplorerBaseUrl": "https://etherscan.io"
                 },
                 {
                    "type": "avalanche",
                    "coin": "AVAX",
                    "testnetName": "Avalanche Fuji testnet",
                    "mainnetName": "Avalanche mainnet",
                    "testnetBlockExplorerBaseUrl": "https://testnet.snowtrace.io",
                    "mainnetBlockExplorerBaseUrl": "https://snowtrace.io"
                 }
              ]
           }
        }`
        Requires: view."""
        return self.baseclient.get("/v1/markets")

    def get_coin_balance(self, coin: str) -> requests.Response:
        """Gets balance of a specific asset.

        `POST /v0/get_balance`

        Request:
        `{ "symbol": "COIN" }`
        symbol: str, required.

        Response:
        `{"success": true
        "result": {
        "accountId": "5577006791947779410",
        "freeBalance": "3000",
        "reservedBalance": "7000",
        "symbol": "AVAX",
        "totalBalance": "10000"
        },
        }`

        Requires: view.
        """

        body = f'{{ "symbol": "{coin}" }}'
        return self.baseclient.post("/v0/get_balance", body=body)

    def get_balances(self) -> requests.Response:
        """Gets balances of all assets in wallet

        `GET /v0/wallet/balances`

        Response:
        `{ "success": true,
        "result": [
        { "coin": "AVAX", free": "3000", "reserved": "7000", "total": "10000", "usdValue": "150000"},
        {"coin": "AAVE", "total": "0", "reserved": "0", "free": "0", "usdValue": "0"}
        ]
        }`
        """

        return self.baseclient.get("/v0/wallet/balances")

    def get_deposit_addresses(self, coins: List[str]) -> requests.Response:
        """Gets all provisioned addresses for an account.

        `POST /v0/wallet/deposit_address/list`

        """
        body = f'{{ "coins": "{coins}" }}'
        return self.baseclient.post("/v0/get_balance", body=body)

    def get_deposits(self) -> requests.Response:
        """Gets all deposits for an account.
        Reverse chronological array encapsulated in generic response wrapper.

        `GET /v0/wallet/deposits`
        """
        return self.baseclient.get("/v0/wallet/deposits")

    def get_deposit(self, txid: str) -> requests.Response:
        """Gets a deposit by transaction ID.

        `GET /v0/wallet/deposits/<TxID>`

        """
        return self.baseclient.get(f"/v0/wallet/deposits/{txid}")

    # TODO: this is a case where we could have validation. like to check if end is after start and nothing is negative or zero?
    def get_deposits_csv(
        self, *, start_secs: Optional[int] = None, end_secs: Optional[int] = None  # `*` enforces keyword only arguments
    ) -> requests.Response:  # TODO: this is a response that can't be json encoded by the base class
        """Gets deposits for an account within the start and end times

        `POST /v0/wallet/deposits/csv`

        Response:
        `CSV formatted text, sorted reverse chronologically`
        """
        body = {}
        if start_secs is not None:
            body["start_time"] = start_secs
        if end_secs is not None:
            body["end_time"] = end_secs
        return self.baseclient.post("/v0/wallet/deposits/csv", body=json.dumps(body))

    def get_withdrawals(self) -> requests.Response:
        """Gets all withdrawals for an account.

        `GET /v0/wallet/withdrawals`
        """

        return self.baseclient.get("/v0/wallet/withdrawals")

    def get_withdrawal(self, txid: str) -> requests.Response:
        """Gets a withdrawal by transaction ID.

        `GET /v0/wallet/withdrawals/<TxID>`
        """

        return self.baseclient.get(f"/v0/wallet/withdrawals/{txid}")

    def get_withdrawals_csv(
        self, *, start_secs: Optional[int] = None, end_secs: Optional[int] = None
    ) -> requests.Response:
        """Gets withdrawals for an account within the start and end times

        POST /v0/wallet/withdrawals/csv"""

        body = {}
        if start_secs is not None:
            body["start_time"] = start_secs
        if end_secs is not None:
            body["end_time"] = end_secs
        return self.baseclient.post("/v0/wallet/withdrawals/csv", body=json.dumps(body))

    def provision_address(self, coin: str) -> requests.Response:
        """Provisions an address for deposit of an asset

        `POST /v0/provision_address`

        Request:
        `{"coin": "AVAX"}`
        """
        body = f'{{ "symbol": "{coin}" }}'
        return self.baseclient.post("/v0/provision_address", body=body)

    def withdraw(self, to_address: str, amount: Union[str, Decimal], custom_id: str, coin: str) -> requests.Response:
        """Initiates a withdrawal

        `POST /v0/withdraw`
        """
        body = {}
        body.update(
            {
                "address": to_address,
                "amount": str(amount),
                "customer_withdrawal_id": custom_id,
                "symbol": coin,
            }
        )
        return self.baseclient.post("/v0/withdraw", body=json.dumps(body))
