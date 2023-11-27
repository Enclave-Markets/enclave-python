# %%
"""Websocket Client for Enclave Markets."""
import asyncio
import decimal
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
UNSUBSCRIBE: Final[str] = '{{"op":"unsubscribe", "channel":"{channel}"}}'
PING: Final[str] = '{"op":"ping"}'


def noop(*_: Any, **__: Any) -> None:
    """No operation. Accepts any arguments and does nothing."""
    return None


Callback = Callable[[dict], None]  # type alias: callback is a function that takes in the message dict.


class WebSocketClient:
    """Websocket Client for Enclave Markets WebSocket API.
    Handles authentication, subscriptions, and callbacks.

    See Enclave WebSocket Docs:
    https://enclave-markets.notion.site/Common-WebSocket-API-c30db312d36b4bd3a4c77c569db25c4e
    """

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        base_url: str,
        log: Optional[logging.Logger] = None,
    ):
        self._base_url = base_url
        self._key = api_key
        self.__secret = api_secret
        self._client: Optional[websockets.WebSocketClientProtocol] = None
        self._pending_subscriptions: Dict[str, Callback] = {}
        self._callbacks: Dict[str, Callback] = defaultdict(lambda: noop)
        self._lock = asyncio.Lock()  # only use from coroutines
        self.log = log
        self._stop = False

    @property
    def ws(self) -> websockets.WebSocketClientProtocol:
        """Get the websocket client. Raises RuntimeError if client not set.

        Used instead of `self._client` directly to go from returning type
        `WebSocketClientProtocol | None` to `WebSocketClientProtocol` instead."""
        if not self._client:
            raise RuntimeError("Client not set.")
        return self._client

    def _auth_message(self) -> str:
        """Create the authentication message for the websocket as defined in Enclave docs

        https://enclave-markets.notion.site/Common-WebSocket-API-c30db312d36b4bd3a4c77c569db25c4e#9dc9468b99c54c76b92ad191b4ac3d21.
        """
        timestamp = str(int(time.time() * 1_000))
        message: str = f"{timestamp}{LOGIN_STR}"
        auth = hmac.new(self.__secret.encode(), message.encode(), hashlib.sha256).hexdigest()

        return json.dumps({"op": "login", "args": {"key": self._key, "time": timestamp, "sign": auth}})

    async def run(self, ping_interval: float = 15) -> bool:
        """Run the websocket client (forever) async.
        Should be run in an existing event loop or with `asyncio.run()` or `asyncio.gather()`.

        This function will connect to the websocket and authenticate (while holding the lock).
        Then it subscribes to all pending subscriptions and waits for messages.
        When a message is received, it will call the callback function for that channel if that hook is set.

        This function runs forever until
        the websocket connection is closed by setting `self.close()`
        or a fatal error.

        Returns True if the connection was closed by the client, False if it was closed by the server."""

        async for ws in websockets.connect(self._base_url, ping_interval=ping_interval, logger=self.log):
            if self._stop:
                await ws.close()
                return True

            async with self._lock:  # lock on reconnect
                # Sets the data for the automatic ping (not strictly necessary).
                # Uses setattr so mypy doesn't complain we're setting a method of an object.
                setattr(ws, "ping", functools.partial(ws.ping, data=PING))
                await ws.send(self._auth_message())
                msg = await asyncio.wait_for(ws.recv(), timeout=20)
                if json.loads(msg) != {"type": "loggedIn"}:
                    raise RuntimeError("Login failed")
                self._client = ws

            for channel, callback in self._pending_subscriptions.items():
                await self.subscribe_callback(channel, callback)  # (re)subscribe all pending subscriptions

            while ws.open:
                if self._stop:
                    await ws.close()
                    return True

                try:
                    msg = await ws.recv()
                except websockets.ConnectionClosed:
                    break  # break `while`` to reconnect

                try:
                    msg_json: Dict[str, str] = json.loads(msg, parse_float=decimal.Decimal, parse_int=decimal.Decimal)
                except json.JSONDecodeError:
                    continue

                if msg_json["type"] == "update":
                    channel = msg_json["channel"]
                    self._callbacks[channel](msg_json)  # TODO: or pass msg_json["data"]?

                await asyncio.sleep(0)  # yield

        return self._stop

    def close(self) -> None:
        """Signal the Client to close the websocket connection."""
        self._stop = True

    def add_pending_subscription(self, channel: str, callback: Callable) -> None:
        """Add a subscription to the pending subscriptions to be subscribed on (re)connect."""
        self._pending_subscriptions[channel] = callback

    async def subscribe_callback(self, channel: str, callback: Callback) -> bool:
        """Subscribe a callback function to a channel.
        Also adds the subscription to the pending subscriptions so that it will be resubscribed on reconnect.

        This is meant to be called async after `run()` while the Client is connected.

        The callback function should take a single argument
        which is the message from the channel, (including the type and channel).

        This function holds the lock."""
        self.add_pending_subscription(channel, callback)  # add for reconnect

        self._callbacks[channel] = callback
        async with self._lock:
            try:
                ws = self.ws
                await ws.send(SUBSCRIBE.format(channel=channel))
            except (RuntimeError, websockets.ConnectionClosed, TypeError):
                return False
        await asyncio.sleep(0)  # yield
        return True

    async def unsubscribe_callback(self, channel: str) -> bool:
        """Unsubscribe the callback function from the channel.
        Also removes the subscription from the pending subscriptions.

        Returns True if the unsubscribe was successful or wasn't subscribed, False otherwise.

        Holds the lock."""
        if channel not in self._callbacks:
            return True
        async with self._lock:
            del self._callbacks[channel]
            try:
                ws = self.ws
                await ws.send(UNSUBSCRIBE.format(channel=channel))
            except (RuntimeError, websockets.ConnectionClosed, TypeError):
                return False
        await asyncio.sleep(0)  # yield
        return True


# %%
