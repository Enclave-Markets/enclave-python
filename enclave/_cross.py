"""
cross contains the Cross specific API and calls an instance of BaseClient to make requests and handle auth.
"""

import json
import re
from decimal import Decimal
from typing import Optional

from . import _baseclient
from .models import Res


class Cross:
    """Cross contains the Cross specific API and calls an instance of BaseClient to make requests and handle auth.

    Designed to be used as `Client(...).cross.a_cross_endpoint(...)` and not initialized directly.

    See the [Enclave Cross Docs](https://enclave-markets.notion.site/Cross-REST-API-4326701d5c0048f7b9eb51ac15e711ce).
    """

    def __init__(self, base_client: _baseclient.BaseClient):
        self.bc = base_client

    def add_order(
        self,
        pair: str,
        side: str,
        size: Decimal,
        *,
        cancel_above: Optional[Decimal] = None,
        cancel_below: Optional[Decimal] = None,
        customer_order_id: Optional[str] = None,
        expiration_unix_secs: Optional[int] = None,
    ) -> Res:
        """
        Adds an order to the crossing network.

        Note: In Enclave Cross, there is no price submitted on the order and all orders happen at the oracle price. Because of this, the size specifies how much of the currency you will be giving up to acquire the other currency. This is different than typical limit order books.

        `POST /v0/add_order`

        Request body parameters:
        - pair: the currency pair to trade (e.g. AVAX/ETH, separator can be /,_,-).
        - side: BUY or SELL.
        - size: If side is “BUY”, this is the amount of quote currency to spend. If side is “SELL”, this is the amount of base currency to sell. E.g. for BTC/USD, if you place a buy order of size 1, that means you will be buying BTC, and spending $1 to get it. If you place a sell order of size 1, that means you will sell 1 BTC.

        - cancel_above: max price at which the order should be filled, will be canceled if oracle price exceeds this (e.g. "22000"). Optional.
        - cancel_below: min price at which the order should be filled, will be canceled if oracle price goes lower than this (e.g. "18000"). Optional.
        - customer_order_id: an order ID that the customer can pass in for their own reference (e.g. "abc123"). Optional.
        - expiration_unix_secs: when the placed order will expire and be automatically cancelled, in seconds from the unix epoch. Must be less than a year in the future. A value of 0 is ignored. Optional.
        """
        base, quote = re.split(r"[-/_]", pair)
        body = {
            "orderCategory": "CN",
            "pair": {"base": base, "quote": quote},
            "side": side,
            "size": str(size),
            "cancelAbove": str(cancel_above) if cancel_above else None,
            "cancelBelow": str(cancel_below) if cancel_below else None,
            "customerOrderId": customer_order_id,
            "expirationUnix": expiration_unix_secs,
        }
        body_filtered = {k: v for k, v in body.items() if v is not None}  # filter None

        return self.bc.post("/v0/add_order", body=json.dumps(body_filtered))

    def cancel_order(self, *, internal_order_id: Optional[str] = None, customer_order_id: Optional[str] = None) -> Res:
        """Cancels an order by either the internal order ID or the customer order ID. Exactly one of these must be provided.

        `POST /v0/cancel_order`

        Request body parameters:
        - internal_order_id: The order ID returned on order creation (e.g. "5577006791947779410"). Optional.
        - customer_order_id: The order ID passed by the user on placement (e.g. "abc123"). Optional.
        """
        body = {}
        if customer_order_id and not internal_order_id:
            body = {"customerOrderId": customer_order_id}
        elif internal_order_id and not customer_order_id:
            body = {"internalOrderId": internal_order_id}
        else:
            raise ValueError("Must provide exactly one of customer_order_id or internal_order_id")

        return self.bc.post("/v0/cancel_order", body=json.dumps(body))

    def get_order_status(
        self, *, internal_order_id: Optional[str] = None, customer_order_id: Optional[str] = None
    ) -> Res:
        """
        Gets the status of a placed order by either the internal order ID or the customer order ID. Exactly one of these must be provided.

        `POST /v0/get_order_status`

        Request body parameters:
        - internal_order_id: The order ID returned on order creation (e.g. "5577006791947779410"). Optional.
        - customer_order_id: The order ID passed by the user on placement (e.g. "abc123"). Optional.
        """
        body = {}
        if customer_order_id and not internal_order_id:
            body = {"customerOrderId": customer_order_id}
        elif internal_order_id and not customer_order_id:
            body = {"internalOrderId": internal_order_id}
        else:
            raise ValueError("Must provide exactly one of customer_order_id or internal_order_id")

        return self.bc.post("/v0/get_order_status", body=json.dumps(body))

    def get_open_orders(self) -> Res:
        """Returns all open orders for an account

        `GET /v0/orders`"""
        return self.bc.get("/v0/orders")

    def get_order_history(self) -> Res:
        """Returns all orders for an account

        `GET /v0/orders/history`"""
        return self.bc.get("/v0/orders/history")

    def get_order(self, *, internal_order_id: Optional[str] = None, customer_order_id: Optional[str] = None) -> Res:
        """Returns the order with the provided ID

        `GET /v0/orders/{internal_order_id}` if internal_order_id
        or
        `GET /v0/orders/client:{customer_order_id}` if customer_order_id."""

        if (not any((customer_order_id, internal_order_id))) or all((customer_order_id, internal_order_id)):
            raise ValueError("Must provide exactly one of customer_order_id or internal_order_id")

        path = f"client:{customer_order_id}" if customer_order_id else internal_order_id

        return self.bc.get(f"/v0/orders/{path}")

    def get_fills_by_id(
        self, *, internal_order_id: Optional[str] = None, customer_order_id: Optional[str] = None
    ) -> Res:
        """Fills by Order ID

        Returns the fills associated with the order with the provided ID, sorted by time.

        `GET /v0/orders/{internal_order_id}/fills` if internal_order_id
        or
        `GET /v0/orders/client:{customer_order_id}/fills` if customer_order_id."""

        if (not any((customer_order_id, internal_order_id))) or all((customer_order_id, internal_order_id)):
            raise ValueError("Must provide exactly one of customer_order_id or internal_order_id")

        path = f"client:{customer_order_id}" if customer_order_id else internal_order_id

        return self.bc.get(f"/v0/orders/{path}/fills")

    def get_fills(
        self,
        *,
        limit: Optional[int] = None,
        start_ms: Optional[int] = None,
        end_ms: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> Res:
        """Returns all fills for an account

        `GET /v0/fills`

        Request query parameters:
        - limit: maximum number of results to return (e.g. 1000). Optional.
        - start_ms: UTC time of fill in UTC milliseconds (e.g. 1666209371000). Optional.
        - endTime: UTC time of fill in milliseconds (e.g. 1666203390000). Optional.
        - cursor: pagination cursor (e.g. NQ5WWO3THN3Q====). Optional.
        """

        query = {
            "limit": limit,
            "startTime": start_ms,
            "endTime": end_ms,
            "cursor": cursor,
        }

        return self.bc.get("/v0/fills", params=query)

    def get_fills_csv(self, *, start_secs: Optional[int] = None, end_secs: Optional[int] = None) -> Res:
        """
        Gets CSV formatted fills for an account within the start and end times

        `POST /v0/fills/csv`

        Request body parameters:
        - start_secs: Start time in Unix time seconds to filter results (e.g. 1666203390). Optional.
        - end_secs: End time in Unix time seconds to filter results (e.g. 1666209371). Optional.
        """
        body = {}
        if start_secs is not None:
            body["start_time"] = start_secs
        if end_secs is not None:
            body["end_time"] = end_secs

        return self.bc.post("/v0/fills/csv", body=json.dumps(body))

    def get_price(self, pair: str) -> Res:
        """Gets the price of a specific trading pair

        `POST /v0/price`

        Request body parameters:
        - pair: the currency pair to trade (e.g. AVAX-ETH, separator can be /,_,-).
        """
        base, quote = re.split(r"[-/_]", pair)
        body = {
            "pair": {"base": base, "quote": quote},
        }

        return self.bc.post("/v0/price", body=json.dumps(body))

    def get_prices(self) -> Res:
        """Gets the prices of all trading pairs

        `GET /v0/prices`"""
        return self.bc.get("/v0/prices")
