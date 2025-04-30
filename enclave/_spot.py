"""
spot implements the Spot specific API and calls an instance of BaseClient to make requests and handle auth.
"""
import json
from decimal import Decimal
from typing import Optional, List

from . import _baseclient
from .models import Res


class Spot:
    """Spot contains the Spot specific API and calls an instance of BaseClient to make requests and handle auth.

    Designed to be used as `Client(...).spot.a_spot_endpoint(...)`
    and not imported directly.

    See the
    [Spot API docs](https://enclave-markets.notion.site/Spot-REST-API-2a929f6266ff45aaa559bc8a3f34a308)
    """

    def __init__(self, base_client: _baseclient.BaseClient):
        self.bc = base_client

    def get_orders(
        self,
        *,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
        market: Optional[str] = None,
        status: Optional[str] = None,
        start_ms: Optional[int] = None,
        end_ms: Optional[int] = None,
    ) -> Res:
        """
        Get orders that meet the optional parameters.

        `GET /v1/orders`

        Request Query Parameters:
        - limit: The number of orders to return (e.g. 1000). Optional.
        - cursor: The cursor to use for pagination (e.g. NQ5WWO3THN3Q====). Optional.
        - market: The market to filter orders by (e.g. AVAX-USDC). Optional.
        - status: The status to filter orders by (e.g. open). Optional.
        - start_ms: The unix start time in milliseconds to filter orders by (e.g. 1684814400000). Optional.
        - end_ms: The unix end time in milliseconds to filter orders by (e.g. 1672549200000). Optional."""

        query = {
            "limit": limit,
            "cursor": cursor,
            "market": market,
            "status": status,
            "startTime": start_ms,
            "endTime": end_ms,
        }
        return self.bc.get("/v1/orders", params=query)

    def get_order(self, *, client_order_id: Optional[str] = None, order_id: Optional[str] = None) -> Res:
        """
        Get an order by client order ID or internal order ID. Exactly one of client_order_id or order_id must be provided.

        `GET /v1/orders/{orderID}` if order_id (internal)
        or
        `GET /v1/orders/client:{clientOrderID}` if client_order_id.


        Request Path Parameters:
        - client_order_id: The client order ID to retrieve (e.g. abc123). Optional.
        - order_id: The internal order ID to retrieve (e.g. 197ec08e001658690721be129e7fa595). Optional."""

        if (not any((client_order_id, order_id))) or all((client_order_id, order_id)):
            raise ValueError("Must provide exactly one of client_order_id or order_id")

        path = f"client:{client_order_id}" if client_order_id else str(order_id)

        return self.bc.get(f"/v1/orders/{path}")

    def get_orders_csv(
        self,
        *,
        market: Optional[str] = None,
        status: Optional[str] = None,
        start_ms: Optional[int] = None,
        end_ms: Optional[int] = None,
    ) -> Res:
        """
        Export CSV of orders that meet the optional parameters.

        `GET /v1/orders/csv`

        Request Query Parameters:
        - market: The market to filter orders by (e.g. AVAX-USDC). Optional.
        - status: The status to filter orders by (e.g. open). Optional.
        - start_ms: The unix start time in milliseconds to filter orders by (e.g. 1684814400000). Optional.
        - end_ms: The unix end time in milliseconds to filter orders by (e.g. 1672549200000). Optional."""

        query = {
            "market": market,
            "status": status,
            "startTime": start_ms,
            "endTime": end_ms,
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
        start_ms: Optional[int] = None,
        end_ms: Optional[int] = None,
    ) -> Res:
        """
        Get fills that meet the optional parameters.

        `GET /v1/fills`

        Request Query Parameters:
        - limit: The number of orders to return (e.g. 1000). Optional.
        - cursor: The cursor to use for pagination (e.g. NQ5WWO3THN3Q====). Optional.
        - market: The market to filter orders by (e.g. AVAX-USDC). Optional.
        - start_ms: The unix start time in milliseconds to filter orders by (e.g. 1684814400000). Optional.
        - end_ms: The unix end time in milliseconds to filter orders by (e.g. 1672549200000). Optional."""

        query = {
            "limit": limit,
            "cursor": cursor,
            "market": market,
            "startTime": start_ms,
            "endTime": end_ms,
        }
        return self.bc.get("/v1/fills", params=query)

    def get_fills_by_id(self, *, client_order_id: Optional[str] = None, order_id: Optional[str] = None) -> Res:
        """
        Fills by Order ID
        Exactly one of client_order_id (clientOrderID) or internal order_id (orderID) must be provided.

        `GET /v1/orders/client:{orderID}/fills` if client_order_id
        or
        `GET /v1/orders/{orderID}/fills` if order_id (internal)"""

        if (not any((client_order_id, order_id))) or all((client_order_id, order_id)):
            raise ValueError("Must provide exactly one of client_order_id or order_id")

        path = f"client:{client_order_id}" if client_order_id else order_id

        return self.bc.get(f"/v1/orders/{path}/fills")

    def get_fills_csv(
        self, market: Optional[str] = None, *, start_ms: Optional[int] = None, end_ms: Optional[int] = None
    ) -> Res:
        """
        Export CSV of filled orders that meet the optional parameters.

        `GET /v1/fills/csv`

        Request Query Parameters:
        - market: The market to filter orders by (e.g. AVAX-USDC). Optional.
        - start_ms: The unix start time in milliseconds to filter orders by (e.g. 1684814400000). Optional.
        - end_ms: The unix end time in milliseconds to filter orders by (e.g. 1672549200000). Optional."""

        query = {
            "market": market,
            "startTime": start_ms,
            "endTime": end_ms,
        }
        return self.bc.get("/v1/fills/csv", params=query)

    def cancel_orders(self, market: Optional[str] = None) -> Res:
        """
        Cancel all orders (optionally per market).

        `DELETE /v1/orders`

        Request Query Parameters:
        - market: The market to cancel all orders in (e.g. AVAX-USDC). Optional.
        If no market is provided, all orders for all markets will be cancelled."""

        return self.bc.delete("/v1/orders", params={"market": market})

    def cancel_order(self, *, client_order_id: Optional[str] = None, order_id: Optional[str] = None) -> Res:
        """
        Cancel an order by client order ID or internal order ID. Exactly one of client_order_id or order_id must be provided.

        `DELETE /v1/orders/{orderID}` if order_id (internal).
        or
        `DELETE /v1/orders/client:{clientOrderID}` if client_order_id.


        Request Path Parameters:
        - client_order_id: The client order ID to cancel (e.g. abc123). Optional.
        - order_id: The internal order ID to cancel (e.g. 197ec08e001658690721be129e7fa595). Optional."""

        if (not any((client_order_id, order_id))) or all((client_order_id, order_id)):
            raise ValueError("Must provide exactly one of client_order_id or order_id")

        path = f"client:{client_order_id}" if client_order_id else str(order_id)

        return self.bc.delete(f"/v1/orders/{path}")

    class OrderParams:
        market: str
        side: str
        price: Optional[Decimal] = None
        size: Optional[Decimal] = None
        client_order_id: Optional[str] = None
        quote_size: Optional[Decimal] = None
        order_type: Optional[str] = None
        time_in_force: Optional[str] = None
        post_only: Optional[bool] = None

    def add_order(self, params: OrderParams) -> Res:
        """Creates a spot order.

        Limit or market orders can be created by changing the "type" field.
        For market orders, the quantity specified must always be in terms of the quantity given up,
        so for sells specify a (base) `size`, and for buys specify `quoteSize`

        `POST /v1/orders`

        Request Body Parameters:
        - market: trading market pair (e.g. AVAX-USDC).
        - side: buy or sell (e.g. "buy").

        - price: limit price. Must be aligned with quoteIncrement from /v1/markets (e.g. 1.55). (Not for market orders).
        - size: the amount of base currency to buy or sell.  Must be aligned with baseIncrement from /v1/markets (e.g. 20.30). (Not for market sell)

        - client_order_id: Order id provided by client. Alphanumeric and underscores and dashes. <= 64 characters (e.g. "order123"). Optional.
        - quote_size: Order quantity based in quote currency. Can only be set for market order buys (e.g. 13.0967). Optional.
        - order_type: The order type, "limit" or "market" (e.g. "limit"). Optional, defaults to "limit".
        - time_in_force: "GTC" or "IOC" - Good until canceled / Immediate or cancel. Cannot be set for market orders (e.g. "IOC"). Optional, defaults to "GTC".
        - post_only: Whether an order should be prohibited from filling on placement (e.g. True). Optional, defaults to False.
        """

        body = {
            "market": params.market,
            "price": str(params.price) if params.price else None,
            "side": params.side,
            "size": str(params.size) if params.size else None,
            "clientOrderId": params.client_order_id,
            "quoteSize": str(params.quote_size) if params.quote_size else None,
            "type": params.order_type,
            "timeInForce": params.time_in_force,
            "postOnly": params.post_only,
        }
        body_filtered = {k: v for k, v in body.items() if v is not None}  # filter None

        return self.bc.post("/v1/orders", body=json.dumps(body_filtered))

    def batch_add_order(self, orders: List[OrderParams]) -> Res:
        """Creates multiple spot orders in a single request.

        `POST /v1/orders/batch`

        Request Body Parameters:
        - orders: A list of orders. Field semantics are same as in add_order.
        """

        body: dict = {"orders": []}
        for order in orders:
            order_body = {
                "market": order.market,
                "price": str(order.price) if order.price is not None else None,
                "side": order.side,
                "size": str(order.size) if order.size is not None else None,
                "clientOrderId": order.client_order_id,
                "quoteSize": str(order.quote_size) if order.quote_size is not None else None,
                "type": order.order_type,
                "timeInForce": order.time_in_force,
                "postOnly": order.post_only,
            }
            body["orders"].append({k: v for k, v in order_body.items() if v is not None})  # filter None

        return self.bc.post("/v1/orders/batch", body=json.dumps(body))
