# %%
"""Getting started with the Enclave Python Package.
Run from base folder using `python -m examples.intro`"""
import os
import time
from decimal import Decimal

import enclave.models
from enclave.client import Client


def perps(client: Client) -> None:
    """Demonstrate some perps trading functionality."""

    margin_balance = client.perps.get_balance().json()
    print(f"{margin_balance=}")
    available_margin = Decimal(margin_balance["result"]["availableMargin"])
    print(f"{available_margin=}")
    assert available_margin >= Decimal(1)

    # other than margin, leverage etc, perps is the same API as spot
    perps_trading_pairs = client.get_markets().json()["result"]["perps"]["tradingPairs"]
    btcusd_trading_pair = [pairs for pairs in perps_trading_pairs if pairs["market"] == "BTC-USD.P"][0]
    print(f"{btcusd_trading_pair=}")

    # get the min order size for BTC-USD.P
    btcusd_quote_increment = Decimal(btcusd_trading_pair["quoteIncrement"])
    btcusd_base_increment = Decimal(btcusd_trading_pair["baseIncrement"])
    print(f"{btcusd_quote_increment=}, {btcusd_base_increment=}")

    # get the leverage for BTC-USD.P
    btcusd_leverage = Decimal(btcusd_trading_pair["defaultLeverage"])
    print(f"{btcusd_leverage=}")

    # get the top of book for BTC-USD.P
    btcusd_top_of_book = client.perps.get_depth("BTC-USD.P", depth=1).json()["result"]
    print(f"{btcusd_top_of_book=}")
    btcusd_bid_price, btcusd_bid_size = (Decimal(x) for x in btcusd_top_of_book["bids"][0])
    print(f"{btcusd_bid_price=}, {btcusd_bid_size=}")

    # place a buy limit order of the smallest size one tick away from top of book (so we don't get filled)
    # all perps orders are collateralized with USDC at the leverage specified
    buy_price = btcusd_bid_price - btcusd_quote_increment
    buy_size = btcusd_base_increment
    assert available_margin * btcusd_leverage >= buy_price * buy_size

    custom_id = f"demo{int(time.time_ns())}"
    buy_order = client.perps.add_order(
        client.perps.OrderParams(
            market="BTC-USD.P",
            side=enclave.models.BUY,
            price=buy_price,
            size=buy_size,
            order_type=enclave.models.LIMIT,
            client_order_id=custom_id
        )
    ).json()
    print(f"{buy_order=}")

    # cancel all orders in the market
    cancel_res = client.perps.cancel_orders("BTC-USD.P").json()
    print(f"{cancel_res=}")

    # get the order status
    order_status = client.perps.get_order(client_order_id=custom_id).json()["result"]
    print(f"{order_status=}")
    filled_size = Decimal(order_status["filledSize"])
    print(f"{filled_size=}")

    # cause a trade and query fills
    custom_id = f"demo{int(time.time_ns())}"
    buy_order = client.perps.add_order(
        client.perps.OrderParams(
            market="BTC-USD.P",
            side=enclave.models.BUY,
            price=None,
            size=buy_size,
            order_type=enclave.models.MARKET,
            client_order_id=custom_id
        )
    ).json()["result"]
    print(f"{buy_order=}")

    positions = client.perps.get_positions().json()["result"]
    print(f"{positions=}")

    fills_by_custom_id = client.perps.get_fills_by_id(client_order_id=custom_id).json()["result"]
    print(f"found {len(fills_by_custom_id)} fills by custom id")

    fills_by_order_id = client.perps.get_fills_by_id(order_id=buy_order["orderId"]).json()["result"]
    print(f"found {len(fills_by_order_id)} fills by order id")

    all_fills = client.perps.get_fills().json()["result"]
    print(f"found {len(all_fills)} fills for all orders")

    margin_withdraw = client.perps.transfer("USDC", Decimal(-1)).json()
    print(f"{margin_withdraw=}")
    margin_balance = client.perps.get_balance().json()
    print(f"{margin_balance=}")


if __name__ == "__main__":
    # For more auth options, see auth.py

    # load environment variables
    API_KEY = str(os.getenv("enclave_key"))
    API_SECRET = str(os.getenv("enclave_secret"))

    # create a client
    enclave_client = Client(API_KEY, API_SECRET, enclave.models.SANDBOX_PERMISSIONLESS)
    if not enclave_client.wait_until_ready():
        raise RuntimeError("Enclave not connecting.")
    authed_hello = enclave_client.authed_hello().json()
    print(f"{authed_hello=}")

    # run the perps example
    print(f"\nRunning perps example...\n{'*' * 80}")
    perps(enclave_client)

    print("\nHave a nice day! (Thank you!)")

# %%
