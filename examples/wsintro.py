# %%
"""Getting started with Enclave WebSockets.
Run from base folder using `python -m examples.wsintro`"""
import asyncio
import os

import dotenv

from enclave.wsclient import WebSocketClient


def prices_callback(prices: dict):
    """Demo callback for when the websocket client receives prices.
    Just print the prices of pairs with AVAX as the base."""
    if prices["data"]["pair"]["base"] == "AVAX":
        print(f'Price: {prices["data"]["price"]} for pair: {prices["data"]["pair"]}')


async def subscribe_unsubscribe_prices(ws_client: WebSocketClient):
    """Demonstrate subscribing and unsubscribing to prices."""
    await asyncio.sleep(1)
    # subscribe to prices and print
    await ws_client.subscribe_callback("prices", prices_callback)

    # wait for a few messages to come in before unsubbing
    await asyncio.sleep(0.5)
    # unsubscribe from prices
    await ws_client.unsubscribe_callback("prices")


async def main() -> None:
    # For more auth options, see auth.py

    # load environment variables
    dotenv.load_dotenv("dev.env")

    API_KEY = str(os.getenv("enclave_key"))
    API_SECRET = str(os.getenv("enclave_secret"))

    # define websocket client object
    ws = WebSocketClient(
        API_KEY,
        API_SECRET,
        "wss://api-sandbox.enclave.market/ws",
        on_connect=lambda: print("On Connect"),
        on_auth=lambda: print("On Auth"),
        on_error=lambda x: print(f"On Error: {x}"),
        on_disconnect=lambda: print("On Disconnect"),
        on_exit=lambda: print("On Exit"),
    )

    # add callbacks to be subscribed when the ws client connects
    ws.add_pending_subscription("deposits", print)

    await asyncio.gather(ws.run(), subscribe_unsubscribe_prices(ws))


if __name__ == "__main__":
    # run the websocket client and other coroutines
    asyncio.run(main())
