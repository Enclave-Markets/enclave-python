"""Provides constants for types"""

from typing import Final, Set

import requests

GET: Final[str] = "GET"
POST: Final[str] = "POST"
DELETE: Final[str] = "DELETE"
PUT: Final[str] = "PUT"
VERBS: Final[Set[str]] = {GET, POST, DELETE, PUT}

DEV: Final[str] = "https://api-dev.enclavemarket.dev"
DEV_PERMISSIONLESS: Final[str] = "https://api-dev-permissionless.enclavemarket.dev"
STAGING: Final[str] = "https://api-staging.enclavemarket.dev"
SANDBOX: Final[str] = "https://api-sandbox.enclave.market"
SANDBOX_PERMISSIONLESS: Final[str] = "https://api-sandbox.enclave.trade"
PROD: Final[str] = "https://api.enclave.market"
PROD_PERMISSIONLESS: Final[str] = "https://api.enclave.trade"

BUY: Final[str] = "buy"
SELL: Final[str] = "sell"
SIDES: Final[Set[str]] = {BUY, SELL}

GTC: Final[str] = "GTC"
IOC: Final[str] = "IOC"
TIME_IN_FORCE: Final[Set[str]] = {GTC, IOC}

LIMIT: Final[str] = "limit"
MARKET: Final[str] = "market"
ORDER_TYPES: Final[Set[str]] = {LIMIT, MARKET}

LONG: Final[str] = "long"
SHORT: Final[str] = "short"
DIRECTIONS: Final[Set[str]] = {LONG, SHORT}

STOP_LOSS: Final[str] = "stopLoss"
TAKE_PROFIT: Final[str] = "takeProfit"
STOP_TYPES: Final[Set[str]] = {STOP_LOSS, TAKE_PROFIT}


Res = requests.Response
