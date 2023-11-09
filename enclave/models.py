"""Provides constants for types"""

from typing import Final, Set

import requests

GET: Final[str] = "GET"
POST: Final[str] = "POST"
DELETE: Final[str] = "DELETE"
PUT: Final[str] = "PUT"
VERBS: Final[Set[str]] = {GET, POST, DELETE, PUT}

DEV: Final[str] = "https://api-dev.enclavemarket.dev"
PROD: Final[str] = "https://api.enclave.market"

BUY: Final[str] = "buy"
SELL: Final[str] = "sell"
SIDES: Final[Set[str]] = {BUY, SELL}

GTC: Final[str] = "GTC"
IOC: Final[str] = "IOC"
TIME_IN_FORCE: Final[Set[str]] = {GTC, IOC}

LIMIT: Final[str] = "limit"
MARKET: Final[str] = "market"
ORDER_TYPES: Final[Set[str]] = {LIMIT, MARKET}


Res = requests.Response
