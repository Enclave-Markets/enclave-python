# %%
"""Websocket Client for Enclave Market"""
import asyncio
import functools
import hashlib
import hmac
import json
import logging
import time
from collections import defaultdict
from typing import Any, Callable, Dict, Final, Optional

import dotenv
import websockets

LOGIN_STR: Final[str] = "enclave_ws_login"

SUBSCRIBE: Final[str] = '{{"op":"subscribe", "channel":"{channel}"}}'
PING: Final[str] = '{"op":"ping"}'


def noop(*_: Any, **__: Any) -> None:
    """No operation."""
    return None


class WebSocketClient:
    def __init__(self, api_key: str, api_secret: str, base_url: str):
        self._base_url = base_url
        self._key = api_key
        self.__secret = api_secret
        self._client: Optional[websockets.WebSocketClientProtocol] = None
        self._pending_subscriptions: Dict[str, Callable] = {}
        self._callbacks: Dict[str, Callable] = defaultdict(lambda: noop)
        self._lock = asyncio.Lock()  # only use from coroutines

    @property
    def ws(self) -> websockets.WebSocketClientProtocol:
        if not self._client:
            raise ValueError("Client not connected")
        return self._client

    def _auth_message(self) -> str:
        timestamp = str(int(time.time() * 1_000))
        message: str = f"{timestamp}{LOGIN_STR}"
        auth = hmac.new(self.__secret.encode(), message.encode(), hashlib.sha256).hexdigest()

        return json.dumps({"op": "login", "args": {"key": self._key, "time": timestamp, "sign": auth}})

    async def run(self) -> None:
        logger = logging.getLogger("ws")
        logger.setLevel(logging.DEBUG)
        async for ws in websockets.connect(self._base_url, ping_interval=15, logger=logger):
            async with self._lock:  # lock on reconnect
                setattr(ws, "ping", functools.partial(ws.ping, data=PING))  # not strictly necessary
                await ws.send(self._auth_message())
                msg = await ws.recv()
                print(msg)
                if json.loads(msg) != {"type": "loggedIn"}:
                    raise ValueError("Login failed")
                self._client = ws
            for channel, callback in self._pending_subscriptions.items():
                await self.subscribe_callback(channel, callback)
            while True:
                msg = await ws.recv()
                msg_json: Dict[str, str] = json.loads(msg)
                if msg_json["type"] == "update":
                    channel = msg_json["channel"]
                    self._callbacks[channel](msg_json)  # TODO: or msg_json["data"]?
                # print(msg)
                await asyncio.sleep(0)  # yield

    def add_subscription(self, channel: str, callback: Callable) -> None:
        self._pending_subscriptions[channel] = callback

    async def subscribe_callback(self, channel: str, callback: Callable) -> None:
        """Subscribe a callback function to a channel.
        Also adds the subscription to the pending subscriptions so that it will be resubscribed on reconnect.

        The callback function should take a single argument, the message from the channel, (including the type and channel).

        This function holds the lock."""
        self.add_subscription(channel, callback)  # add for reconnect

        self._callbacks[channel] = callback
        async with self._lock:
            try:
                ws = self.ws
            except ValueError:
                return
            await ws.send(SUBSCRIBE.format(channel=channel))
        await asyncio.sleep(0)  # yield to other tasks


if __name__ == "__main__":
    envs = dotenv.dotenv_values("sandbox.env")
    c = WebSocketClient(
        envs["key"] or "",
        envs["secret"] or "",
        "wss://api-sandbox.enclave.market/ws",
    )

    async def sleep_run(a: Callable) -> None:
        await asyncio.sleep(3)
        await a()

    # await asyncio.gather(c.run(), sleep_run(functools.partial(c.subscribe_callback, channel="prices", callback=print)))
    # await c.run()

# %%
