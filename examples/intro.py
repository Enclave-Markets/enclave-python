# %%
"""Getting started with the Enclave Python Package.
Run from base folder using `python -m examples.intro`"""
import time
from decimal import Decimal

import dotenv

import enclave.models
from enclave.client import Client

if __name__ == "__main__":
    # For more auth options, see auth.py
    envs = dotenv.dotenv_values("dev.env")
    api_key, api_secret = str(envs["key"]), str(envs["secret"])

    # create a client
    client = Client(api_key, api_secret, enclave.models.DEV)
    print(client.authed_hello().text)

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

    # cancel all orders in the market
    cancel_res = client.spot.cancel_orders("AVAX-USDC").json()
    print(f"{cancel_res=}")

    # get the order status
    order_status = client.spot.get_order(client_order_id=custom_id).json()
    print(f"{order_status['result']=}")
    filled_size = Decimal(order_status["result"]["filledSize"])
    print(f"{filled_size=}")


# %%
