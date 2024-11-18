# %%
"""Getting started with the Enclave Python Package.
Run from base folder using `python -m examples.intro`"""
import os
import time
from decimal import Decimal

import enclave.models
from enclave.client import Client


def spot(client: Client) -> None:
    """Demonstrate some spot trading functionality."""

    # get the balance of AVAX
    balance = Decimal(client.get_balance("AVAX").json()["result"]["freeBalance"])
    print(f"Free AVAX balance: {balance=}")

    # get the AVAX-USDC trading pair to find the min order sizes
    spot_trading_pairs = client.get_markets().json()["result"]["spot"]["tradingPairs"]
    avax_trading_pair = [pairs for pairs in spot_trading_pairs if pairs["market"] == "AVAX-USDC"][0]
    print(f"{avax_trading_pair=}")
    avax_base_min, avax_quote_min = Decimal(avax_trading_pair["baseIncrement"]), Decimal(
        avax_trading_pair["quoteIncrement"]
    )
    print(f"{avax_base_min=} {avax_quote_min=}")

    # get top of book for avax usdc
    avax_top_of_book = client.spot.get_depth("AVAX-USDC", depth=1).json()["result"]
    print(f"{avax_top_of_book=}")
    avax_ask_price, avax_ask_size = (Decimal(x) for x in avax_top_of_book["asks"][0])
    print(f"{avax_ask_price=}, {avax_ask_size=}")

    # place a sell limit order of the smallest size one tick above the top of book (so we don't get filled)
    assert balance >= avax_base_min
    custom_id = f"demo{int(time.time_ns())}"
    sell_order = client.spot.add_order(
        "AVAX-USDC",
        enclave.models.SELL,
        avax_ask_price + avax_quote_min,
        avax_base_min,
        order_type=enclave.models.LIMIT,
        client_order_id=custom_id,
    ).json()["result"]
    print(f"{sell_order=}")

    # cancel all orders in the market
    cancel_res = client.spot.cancel_orders("AVAX-USDC").json()
    print(f"{cancel_res=}")

    # get the order status
    order_status = client.spot.get_order(client_order_id=custom_id).json()["result"]
    print(f"{order_status=}")
    filled_size = Decimal(order_status["filledSize"])
    print(f"{filled_size=}")

    # cause a trade and query fills
    custom_id = f"demo{int(time.time_ns())}"
    sell_order = client.spot.add_order(
        "AVAX-USDC",
        enclave.models.SELL,
        None,
        avax_base_min,
        order_type=enclave.models.MARKET,
        client_order_id=custom_id,
    ).json()["result"]

    print(f"{sell_order=}")
    
    fills_by_custom_id = client.spot.get_fills_by_id(client_order_id=custom_id).json()["result"]
    print(f"found {len(fills_by_custom_id)} fills by custom id")

    fills_by_order_id = client.spot.get_fills_by_id(order_id=sell_order["orderId"]).json()["result"]
    print(f"found {len(fills_by_order_id)} fills by order id")

    all_fills = client.spot.get_fills().json()["result"]
    print(f"found {len(all_fills)} fills for all orders")


def perps(client: Client) -> None:
    """Demonstrate some perps trading functionality."""

    # get USDC balance
    usdc_balance = Decimal(client.get_balance("USDC").json()["result"]["freeBalance"])
    print(f"Free USDC balance: {usdc_balance=}")

    # transfer USDC from the main account to perps
    assert usdc_balance >= Decimal(1)
    margin_deposit = client.perps.transfer("USDC", Decimal(1)).json()
    print(f"{margin_deposit=}")
    margin_balance = client.perps.get_balance().json()
    print(f"{margin_balance=}")
    available_margin = Decimal(margin_balance["result"]["availableMargin"])
    print(f"{available_margin=}")

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
        "BTC-USD.P",
        enclave.models.BUY,
        buy_price,
        buy_size,
        order_type=enclave.models.LIMIT,
        client_order_id=custom_id,
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
        "BTC-USD.P",
        enclave.models.BUY,
        None,
        buy_size,
        order_type=enclave.models.MARKET,
        client_order_id=custom_id,
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


def cross(client: Client) -> None:
    """Demonstrate some cross trading functionality."""

    # get the balance of AVAX
    balance = Decimal(client.get_balance("USDC").json()["result"]["freeBalance"])
    print(f"Free USDC balance: {balance=}")

    # get the AVAX-USDC trading pair to find the min order sizes for cross
    cross_configs = client.get_markets().json()["result"]["tokenConfig"]
    usdc_trading_pair = [token for token in cross_configs if token["id"] == "USDC"][0]
    print(f"{usdc_trading_pair=}")
    # doing a buy order so we need the sizes for the quote currency, USDC
    min_usdc, max_usdc = Decimal(usdc_trading_pair["minOrderSize"]), Decimal(usdc_trading_pair["maxOrderSize"])
    print(f"{min_usdc=} {max_usdc=}")

    # get the oracle price for AVAX-USDC
    avax_usdc_price = Decimal(client.cross.get_price("AVAX-USDC").json()["result"]["price"])
    print(f"{avax_usdc_price=}")

    # buy AVAX for USDC at no more than the current price + $1
    assert min_usdc <= balance <= max_usdc
    custom_id = f"demo{int(time.time_ns())}"
    buy_order = client.cross.add_order(
        "AVAX-USDC",
        enclave.models.BUY,
        min_usdc,
        cancel_above=avax_usdc_price + Decimal(1),
        customer_order_id=custom_id,
    ).json()
    print(f"{buy_order=}")

    # cancel order
    cancel_res = client.cross.cancel_order(customer_order_id=custom_id).json()
    print(f"{cancel_res=}")

    # get the order details
    order_status = client.cross.get_order(customer_order_id=custom_id).json()["result"]
    print(f"{order_status=}")
    print(f"amount filled: {order_status['filledSize']=}, status: {order_status['status']=}")

    fills_by_custom_id = client.cross.get_fills_by_id(customer_order_id=custom_id).json()["result"]
    print(f"found {len(fills_by_custom_id)} fills by custom id")

    fills_by_order_id = client.cross.get_fills_by_id(internal_order_id=buy_order["result"]["internalOrderId"]).json()["result"]
    print(f"found {len(fills_by_order_id)} fills by order id")

    all_fills = client.cross.get_fills().json()["result"]
    print(f"found {len(all_fills)} fills for all orders")


if __name__ == "__main__":
    # For more auth options, see auth.py

    # load environment variables
    API_KEY = str(os.getenv("enclave_key"))
    API_SECRET = str(os.getenv("enclave_secret"))

    # create a client
    enclave_client = Client(API_KEY, API_SECRET, enclave.models.SANDBOX)
    if not enclave_client.wait_until_ready():
        raise RuntimeError("Enclave not connecting.")
    authed_hello = enclave_client.authed_hello().json()
    print(f"{authed_hello=}")

    # run the spot example
    print(f"\nRunning spot example...\n{'*' * 80}")
    spot(enclave_client)

    # run the perps example
    print(f"\nRunning perps example...\n{'*' * 80}")
    perps(enclave_client)

    # run the cross example
    print(f"\nRunning cross example...\n{'*' * 80}")
    cross(enclave_client)

    print("\nHave a nice day! (Thank you!)")

# %%
