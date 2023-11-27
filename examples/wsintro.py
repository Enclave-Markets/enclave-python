# %%
"""Getting started with Enclave WebSockets.
Run from base folder using `python -m examples.wsintro`"""
import asyncio
import logging

import dotenv

from enclave.wsclient import WebSocketClient

if __name__ == "__main__":
    # have a sandbox.env file in the base folder with key and secret like:
    # key=enclaveKeyId_...
    # secret=enclaveApiSecret_...
    envs = dotenv.dotenv_values("sandbox.env")

    logger = logging.getLogger("ws")
    logger.setLevel(logging.DEBUG)

    # define websocket client object
    ws = WebSocketClient(
        envs["key"] or "",
        envs["secret"] or "",
        "wss://api-sandbox.enclave.market/ws",
        log=logger,
    )

    # add callbacks to be subscribed when the ws client connects
    ws.add_pending_subscription("prices", print)
    ws.add_pending_subscription("deposits", print)

    # run the websocket client until it stops
    asyncio.run(ws.run())
