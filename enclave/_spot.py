"""
Spot implements the Spot specific API and calls an instance of BaseClient to make requests and handle auth.
"""
import json
from decimal import Decimal
from typing import Optional

from . import _baseclient, models
from .models import Res


class Spot:
    """Spot contains the Spot specific API and calls an instance of BaseClient to make requests and handle auth.

    Designed to be used as `Client(...).spot.a_spot_endpoint(...)`
    and not imported directly.

    See the Spot API docs
    https://enclave-markets.notion.site/Spot-REST-API-2a929f6266ff45aaa559bc8a3f34a308"""

    def __init__(self, base_client: _baseclient.BaseClient):
        self.bc = base_client

    def get_orders(
        self,
        *,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
        market: Optional[str] = None,
        status: Optional[str] = None,
        start_secs: Optional[int] = None,
        end_secs: Optional[int] = None,
    ) -> Res:
        """
        Get orders that meet the optional parameters.

        `GET /v1/orders`

        Request Query Parameters:
        - limit: The number of orders to return (e.g. 1000). Optional.
        - cursor: The cursor to use for pagination (e.g. NQ5WWO3THN3Q====). Optional.
        - market: The market to filter orders by (e.g. AVAX-USDC). Optional.
        - status: The status to filter orders by (e.g. open). Optional.
        - start_secs: The unix start time in seconds to filter orders by (e.g. 1684814400). Optional.
        - end_secs: The unix end time in seconds to filter orders by (e.g. 1672549200). Optional."""

        query = {
            "limit": limit,
            "cursor": cursor,
            "market": market,
            "status": status,
            "startTime": start_secs,
            "endTime": end_secs,
        }
        return self.bc.get("/v1/orders", params=query)

    def get_order(self, *, custom_id: Optional[str] = None, internal_id: Optional[str] = None) -> Res:
        """
        Get an order by customer or internal ID. Exactly one of custom_id or internal_id must be provided.

        `GET /v1/orders/{orderID}` if internal ID
        or
        `GET /v1/orders/client:{clientOrderID}` if customer ID


        Request Path Parameters:
        - custom_id: The client order ID to retrieve (e.g. abc123). Optional.
        - internal_id: The internal order ID to retrieve (e.g. 197ec08e001658690721be129e7fa595). Optional."""

        if (not any((custom_id, internal_id))) or all((custom_id, internal_id)):
            raise ValueError("Must provide exactly one of custom_id or internal_id")

        path = f"client:{custom_id}" if custom_id else str(internal_id)

        return self.bc.get(f"/v1/orders/{path}")

    def get_orders_csv(
        self,
        *,
        market: Optional[str] = None,
        status: Optional[str] = None,
        start_secs: Optional[int] = None,
        end_secs: Optional[int] = None,
    ) -> Res:
        """
        Export CSV of orders that meet the optional parameters.

        `GET /v1/orders/csv`

        Request Query Parameters:
        - market: The market to filter orders by (e.g. AVAX-USDC). Optional.
        - status: The status to filter orders by (e.g. open). Optional.
        - start_secs: The unix start time in seconds to filter orders by (e.g. 1684814400). Optional.
        - end_secs: The unix end time in seconds to filter orders by (e.g. 1672549200). Optional."""

        query = {
            "market": market,
            "status": status,
            "startTime": start_secs,
            "endTime": end_secs,
        }
        return self.bc.get("/v1/orders/csv", params=query)

    def get_depth(self, market: str, *, depth: Optional[int] = None) -> Res:
        """
        Returns the order book in a market (optionally to a depth)

        `GET /v1/depth`

        Request Query Parameters:
        - market: trading market (e.g. AVAX-USDC).
        - depth: maximum number of results to return (e.g. 10). Optional."""

        query = {"market": market, "depth": depth}
        return self.bc.get("/v1/depth", params=query)

    def get_fills(
        self,
        *,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
        market: Optional[str] = None,
        start_secs: Optional[int] = None,
        end_secs: Optional[int] = None,
    ) -> Res:
        """
        Get fills that meet the optional parameters.

        `GET /v1/fills`

        Request Query Parameters:
        - limit: The number of orders to return (e.g. 1000). Optional.
        - cursor: The cursor to use for pagination (e.g. NQ5WWO3THN3Q====). Optional.
        - market: The market to filter orders by (e.g. AVAX-USDC). Optional.
        - start_secs: The unix start time in seconds to filter orders by (e.g. 1684814400). Optional.
        - end_secs: The unix end time in seconds to filter orders by (e.g. 1672549200). Optional.
        """

        query = {
            "limit": limit,
            "cursor": cursor,
            "market": market,
            "startTime": start_secs,
            "endTime": end_secs,
        }
        return self.bc.get("/v1/fills", params=query)

    def get_fills_by_id(self, *, custom_id: Optional[str] = None, internal_id: Optional[str] = None) -> Res:
        """
        Fills by Order ID
        Exactly one of custom_id (clientOrderID) or internal_id (orderID) must be provided.

        `GET /v1/fills/client:{clientOrderID}` if custom_id
        or
        `GET /v1/orders/{orderID}/fills` if internal_id
        """

        if (not any((custom_id, internal_id))) or all((custom_id, internal_id)):
            raise ValueError("Must provide exactly one of custom_id or internal_id")

        path = f"/v1/fills/client:{custom_id}" if custom_id else f"/v1/orders/{internal_id}/fills"

        return self.bc.get(path)

    # TODO: maybe move * after market? in general force keyword params?
    def get_fills_csv(
        self, market: Optional[str] = None, *, start_secs: Optional[int] = None, end_secs: Optional[int] = None
    ) -> Res:
        """
        Export CSV of filled orders that meet the optional parameters.

        `GET /v1/fills/csv`

        Request Query Parameters:
        - market: The market to filter orders by (e.g. AVAX-USDC). Optional.
        - start_secs: The unix start time in seconds to filter orders by (e.g. 1684814400). Optional.
        - end_secs: The unix end time in seconds to filter orders by (e.g. 1672549200). Optional.

        Response:
        `CSV formatted text, sorted reverse chronologically`

        Requires: view."""

        query = {
            "market": market,
            "startTime": start_secs,
            "endTime": end_secs,
        }
        return self.bc.get("/v1/fills/csv", params=query)

    def cancel_orders(self, market: Optional[str] = None) -> Res:
        """
        Cancel all orders (optionally per market).

        `DELETE /v1/orders`

        Request Query Parameters:
        - market: The market to cancel all orders in (e.g. AVAX-USDC). Optional.
        If no market is provided, all orders for all markets will be cancelled.

        Response:
        None"""

        return self.bc.delete("/v1/orders", params={"market": market})

    def cancel_order(self, *, custom_id: Optional[str] = None, internal_id: Optional[str] = None) -> Res:
        """
        Cancel an order by customer or internal ID. Exactly one of custom_id or internal_id must be provided.

        `DELETE /v1/orders/{orderID}` if internal ID
        or
        `DELETE /v1/orders/client:{clientOrderID}` if customer ID


        Request Path Parameters:
        - custom_id: The client order ID to cancel (e.g. abc123). Optional.
        - internal_id: The internal order ID to cancel (e.g. 197ec08e001658690721be129e7fa595). Optional.
        """
        if (not any((custom_id, internal_id))) or all((custom_id, internal_id)):
            raise ValueError("Must provide exactly one of custom_id or internal_id")

        path = f"client:{custom_id}" if custom_id else str(internal_id)

        return self.bc.delete(f"/v1/orders/{path}")

    def new_order(
        self,
        market: str,
        price: Decimal,
        side: str,
        size: Decimal,
        *,
        custom_id: Optional[str] = None,
        quote_size: Optional[Decimal] = None,
        order_type: Optional[str] = None,
        time_in_force: Optional[str] = None,
        post_only: Optional[bool] = None,
    ) -> Res:
        """Creates a spot order.

        Limit or market orders can be created by changing the “type” field.
        For market orders, the quantity specified must always be in terms of the quantity given up,
        so for sells specify a (base) `size`, and for buys specify `quoteSize`

        `POST /v1/orders`

        Request Body Parameters:
        - market: trading market pair (e.g. AVAX-USDC).
        - price: limit price.  Must be aligned with quoteIncrement from /v1/markets (e.g. 1.55).
        - side: buy or sell (e.g. "buy").
        - size: the amount of base currency to buy or sell.  Must be aligned with baseIncrement from /v1/markets (e.g. 20.30).

        - custom_id: Order id provided by client. Alphanumeric and underscores and dashes. <= 64 characters (e.g. "order123"). Optional.
        - quote_size: Order quantity based in quote currency. Can only be set for market order buys (e.g. 13.0967). Optional.
        - order_type: The order type, “limit” or “market” (e.g. "limit"). Optional, defaults to “limit”.
        - time_in_force: “GTC” or “IOC” - Good until canceled / Immediate or cancel. Cannot be set for market orders (e.g. "IOC"). Optional, defaults to “GTC”.
        - post_only: Whether an order should be prohibited from filling on placement (e.g. True). Optional, defaults to False.
        """

        if side not in models.SIDES:
            raise ValueError(f"Unsupported side {side=}. Must be one of {models.SIDES}.")

        body = {
            "market": market,
            "price": str(price),
            "side": side,
            "size": str(size),
            "clientOrderId": custom_id,
            "quoteSize": str(quote_size) if quote_size else None,
            "type": order_type,
            "timeInForce": time_in_force,
            "postOnly": post_only,
        }
        body_filtered = {k: v for k, v in body.items() if v is not None}  # filter None

        return self.bc.post("/v1/orders", body=json.dumps(body_filtered))
