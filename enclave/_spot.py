"""
Spot contains the Spot specific API and calls an instance of BaseClient to make requests and handle auth.
"""
from typing import Optional

import requests

from . import _baseclient


class Spot:
    def __init__(self, base_client: _baseclient.BaseClient):
        self.bc = base_client

    def get_orders(
        self,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
        market: Optional[str] = None,
        status: Optional[str] = None,
        start_secs: Optional[int] = None,
        end_secs: Optional[int] = None,
    ) -> requests.Response:
        """
        Get orders that meet the optional parameters.

        `GET /v1/orders`

        Request Query Parameters:
        - limit: The number of orders to return (e.g. 1000). Optional.
        - cursor: The cursor to use for pagination (e.g. NQ5WWO3THN3Q====). Optional.
        - market: The market to filter orders by (e.g. AVAX-USDC). Optional.
        - status: The status to filter orders by (e.g. open). Optional.
        - start_secs: The unix start time in seconds to filter orders by (e.g. 1684814400). Optional.
        - end_secs: The unix end time in seconds to filter orders by (e.g. 1672549200). Optional.

        Response:
        ```
        {
            "pageInfo": {
                "nextCursor": "NQ5WWO3THN3Q====",
                "prevCursor": "O4ZTGM3RGM2DG==="
            },
            "result": [
                {
                    "canceledAt": "2022-06-16T12:35:11.123456Z",
                    "clientOrderId": "order123",
                    "createdAt": "2022-06-16T12:35:11.123456Z",
                    "fee": "0.0837",
                    "filledAt": "2022-06-16T12:35:11.123456Z",
                    "filledCost": "8.37465",
                    "filledSize": "5.403",
                    "market": "AVAX-USDC",
                    "orderId": "70a37d8f972f2494837f9dba8364cbb4",
                    "price": "1.55",
                    "side": "buy",
                    "size": "20.30",
                    "status": "open",
                }
            ],
            "success": true
        }
        ```

        Requires: view."""

        query = self.bc.build_params(
            [
                ("limit", limit),
                ("cursor", cursor),
                ("market", market),
                ("status", status),
                ("startTime", start_secs),
                ("endTime", end_secs),
            ]
        )
        return self.bc.get("/v1/orders" + query)

    def get_depth(self, market: str, depth: Optional[int] = None) -> requests.Response:
        """
        Returns the order book in a market (optionally to a depth)

        `GET /v1/depth`

        Request Query Parameters:
        - market: trading market (e.g. AVAX-USDC).
        - depth: maximum number of results to return (e.g. 10). Optional.

        Response:
        ```
        {
            "result": {
                "asks": [["21.11", "1.74"],["21.13","0.23"]],
                "bids": [["21.05","0.34"],["21.02","1.25"]]
            },
            "success": true
        }
        ```

        Requires: view."""

        query = self.bc.build_params([("market", market), ("depth", depth)])
        return self.bc.get("/v1/depth" + query)

    def get_fills(
        self,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
        market: Optional[str] = None,
        start_secs: Optional[int] = None,
        end_secs: Optional[int] = None,
    ) -> requests.Response:
        """
        Get fills that meet the optional parameters.

        `GET /v1/fills`

        Request Query Parameters:
        - limit: The number of orders to return (e.g. 1000). Optional.
        - cursor: The cursor to use for pagination (e.g. NQ5WWO3THN3Q====). Optional.
        - market: The market to filter orders by (e.g. AVAX-USDC). Optional.
        - start_secs: The unix start time in seconds to filter orders by (e.g. 1684814400). Optional.
        - end_secs: The unix end time in seconds to filter orders by (e.g. 1672549200). Optional.

        Response:
        Reverse chronological order of the below.
        ```
        {
            "pageInfo": {
                "nextCursor": "NQ5WWO3THN3Q====",
                "prevCursor": "O4ZTGM3RGM2DG==="
            },
            "result": [
                {
                    "clientOrderId": "order123",
                    "fee": "0.0837",
                    "filledCost": "8.37465",
                    "id": "70a37d8f972f2494837f9dba8364cbb4",
                    "market": "AVAX-USDC",
                    "orderId": "197ec08e001658690721be129e7fa595",
                    "price": "1.55",
                    "side": "buy",
                    "size": "5.403",
                    "time": "2022-06-16T12:35:11.123456Z"
                }
            ],
            "success": true
        }
        ```

        Requires: view."""

        # query = self.bc.build_params(
        #     [
        #         ("limit", limit),
        #         ("cursor", cursor),
        #         ("market", market),
        #         ("startTime", start_secs),
        #         ("endTime", end_secs),
        #     ]
        # )
        query = self.bc.build_params(
            [
                ("limit", limit),
                ("cursor", cursor),
                ("market", market),
                ("startTime", start_secs),
                ("endTime", end_secs),
            ]
        )
        return self.bc.get("/v1/fills" + query)

    """
    Fills by Client Order ID
    Gets fills for individual order by client order ID

    GET /v1/fills/client:{clientOrderID}

    Requires authentication: true
    Required API key permissions: View Only
    Request
    Query parameters
    Name
    Located in
    Description
    Example
    Required
    Schema
    clientOrderID
    path
    client provided ID of order
    "abc123"
    Yes
    string
    """
