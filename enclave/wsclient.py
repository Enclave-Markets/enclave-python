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
from typing import Any, Callable, Dict, Final, Optional, TypeVar

import websockets
import websockets.legacy.client

LOGIN_STR: Final[str] = "enclave_ws_login"

SUBSCRIBE: Final[str] = '{{"op":"subscribe", "channel":"{channel}"}}'
UNSUBSCRIBE: Final[str] = '{{"op":"unsubscribe", "channel":"{channel}"}}'
PING: Final[str] = '{"op":"ping"}'


def noop(*_: Any, **__: Any) -> None:
    """No operation. Accepts any arguments and does nothing."""
    return None


Callback = Callable[[dict], None]  # type alias: callback is a function that takes in the message dict.

E = TypeVar("E", bound=BaseException)


def wrap_error(err: E, msg: str) -> E:
    """Add a message to an error.

    Modifies the error with the message prepended to the error message,
    and also returns the error."""
    err.args = (msg, *err.args)
    return err


class WebSocketClient:
    """Websocket Client for Enclave Markets WebSocket API.
    Handles authentication, subscriptions, and callbacks.

    See Enclave WebSocket Docs:
    https://enclave-markets.notion.site/Common-WebSocket-API-c30db312d36b4bd3a4c77c569db25c4e

    There are two methods to subscribe and hook callback functions to the channel:
    1. Create a client and call `add_pending_subscription` for each subscription before calling `run()`.
    2. Create a client and call `subscribe_callback` asynchronously after calling `run()`.

    Only one callback function can be subscribed to a channel at a time.
    The newest callback function will replace the existing one.

    In addition to the subscription callbacks, there are also hooks for:
    - `on_connect`: called when the websocket connects.
    - `on_auth`: called when the websocket authenticates.
    - `on_disconnect`: called when the websocket disconnects.
    - `on_exit`: called when the Enclave WebSocketClient exits (after disconnect).
    - `on_error`: called when an error occurs

    Pass a logger set to DEBUG to log all websocket traffic (including pings).

    """

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        base_url: str,
        *,
        log: Optional[logging.Logger] = None,
        on_connect: Callable[[], None] = noop,
        on_auth: Callable[[], None] = noop,
        on_error: Callable[[Exception], None] = noop,
        on_disconnect: Callable[[], None] = noop,
        on_exit: Callable[[], None] = noop,
    ):
        self._base_url = base_url
        self._key, self.__secret = api_key, api_secret
        self._client: Optional[websockets.WebSocketClientProtocol] = None
        self._pending_subscriptions: Dict[str, Callback] = {}
        self._callbacks: Dict[str, Callback] = defaultdict(lambda: noop)
        self._stop = False

        # only use the lock from coroutines (not thread safe)
        # the lock ensures coroutines don't have stale references to the client if the `run()` loop reconnects
        self._lock = asyncio.Lock()

        self.log = log if log else logging.getLogger("enclave.websockets")

        self.on_connect, self.on_auth = on_connect, on_auth
        self.on_disconnect, self.on_exit = on_disconnect, on_exit
        self.on_error = on_error

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
        unix_ms = str(int(time.time() * 1_000))
        message: str = f"{unix_ms}{LOGIN_STR}"
        auth = hmac.new(self.__secret.encode(), message.encode(), hashlib.sha256).hexdigest()

        return json.dumps({"op": "login", "args": {"key": self._key, "time": unix_ms, "sign": auth}})

    async def _auth(self, ws: websockets.WebSocketClientProtocol) -> None:
        try:
            await ws.send(self._auth_message())
            msg = await ws.recv()
            if json.loads(msg) != {"type": "loggedIn"}:
                raise RuntimeError("Not logged in.")
            self._client = ws
        except websockets.ConnectionClosed as e:
            raise e
        except Exception as e:  # pylint: disable=W0703
            self.log.error(wrap_error(e, "Authentication failed"))
            self.on_error(e)
            raise e

    async def run(self, ping_secs: float = 15) -> bool:
        """Run the websocket client (forever) async.
        Should be run in an existing event loop or with `asyncio.run()` or `asyncio.gather()`.

        This function will connect to the websocket and authenticate (while holding the lock).
        Then it subscribes to all pending subscriptions and waits for messages.
        When a message is received, it will call the callback function for that channel if that hook is set.

        This function runs forever until
        the websocket connection is closed by setting `self.close()`
        or a fatal error.
        """

        async for ws in websockets.connect(self._base_url, ping_interval=ping_secs, logger=self.log):
            try:
                async with self._lock:  # lock on reconnect
                    # Sets the data for the automatic ping (not strictly necessary).
                    # Uses setattr so mypy doesn't complain we're setting a method of an object.
                    setattr(ws, "ping", functools.partial(ws.ping, data=PING))
                    self.on_connect()
                    await asyncio.wait_for(self._auth(ws), timeout=20)
                    self.on_auth()

                for channel, callback in self._pending_subscriptions.items():
                    await self.subscribe_callback(channel, callback)  # (re)subscribe all pending subscriptions

                await self._handle_messages_forever(ws)

            except websockets.ConnectionClosed:
                if self._stop:
                    self.on_disconnect()
                    break  # break the `async for` loop
            except Exception as e:  # pylint: disable=W0703
                self.log.error(wrap_error(e, "Error uncaught in websocket"))
                self.on_error(e)
                pass  # continue the `async for` loop and reconnect

            self.on_disconnect()

        self.on_exit()
        return self._stop

    async def _handle_messages_forever(self, ws: websockets.WebSocketClientProtocol) -> None:
        """Handle messages forever. Used in `run()`."""
        while not self._stop:
            try:
                msg = await ws.recv()
            except websockets.ConnectionClosed as e:
                raise e
            try:
                msg_json: Dict[str, str] = json.loads(msg, parse_float=decimal.Decimal, parse_int=decimal.Decimal)

                if msg_json["type"] == "update":
                    channel = msg_json["channel"]
                    self._callbacks[channel](msg_json)  # TODO: or pass msg_json["data"]?

                await asyncio.sleep(0)  # yield

            except (json.JSONDecodeError, Exception) as e:  # pylint: disable=W0703
                self.log.error(wrap_error(e, f"Error handling message, Data: {msg!r}"))
                self.on_error(e)
                continue

    async def close(self) -> None:
        """Signal the Client to close the websocket connection."""
        async with self._lock:
            self._stop = True
            await self.ws.close()

    def add_pending_subscription(self, channel: str, callback: Callable) -> None:
        """Add a subscription to the pending subscriptions to be subscribed on (re)connect.

        This is intended to be called after making a client but before calling run."""
        self._pending_subscriptions[channel] = callback

    async def subscribe_callback(self, channel: str, callback: Callback) -> bool:
        """Subscribe a callback function to a channel.
        Also adds the subscription to the pending subscriptions so that it will be resubscribed on reconnect.

        If there is already a callback subscribed to the channel, it will be replaced.

        This is meant to be called async after `run()` while the Client is connected.

        The callback function should take a single argument
        which is the message from the channel, (including the type and channel).

        This function holds the lock."""
        self.add_pending_subscription(channel, callback)  # add for reconnect

        self._callbacks[channel] = callback
        async with self._lock:
            try:
                await self.ws.send(SUBSCRIBE.format(channel=channel))
            except websockets.ConnectionClosed as e:
                raise e
            except Exception as e:  # pylint: disable=W0703
                self.log.error(wrap_error(e, f"Subscribe failed for channel {channel}"))
                self.on_error(e)
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
                await self.ws.send(UNSUBSCRIBE.format(channel=channel))
            except websockets.ConnectionClosed as e:
                raise e
            except Exception as e:  # pylint: disable=W0703
                self.log.error(wrap_error(e, f"Unsubscribe failed for channel {channel}"))
                self.on_error(e)
                return False
        await asyncio.sleep(0)  # yield
        return True
