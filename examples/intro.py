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
    custom_id = f"demo{int(time.time())}"
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
    order_status = client.spot.get_order(client_order_id=custom_id).json()
    print(f"{order_status['result']=}")
    filled_size = Decimal(order_status["result"]["filledSize"])
    print(f"{filled_size=}")


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
    enclave_client = Client(API_KEY, API_SECRET, enclave.models.DEV)
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
