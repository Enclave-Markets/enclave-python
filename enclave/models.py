"""Provides constants for types"""

from typing import Final, Set

GET: Final[str] = "GET"
POST: Final[str] = "POST"
DELETE: Final[str] = "DELETE"
PUT: Final[str] = "PUT"
VERBS: Final[Set[str]] = {GET, POST, DELETE, PUT}

DEV: Final[str] = "https://api-dev.enclavemarket.dev"
PROD: Final[str] = "https://api.enclave.market"
