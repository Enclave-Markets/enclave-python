"""Provides constants for types"""

from typing import Final, Set

GET: Final[str] = "GET"
POST: Final[str] = "POST"
DELETE: Final[str] = "DELETE"
PUT: Final[str] = "PUT"
VERBS: Final[Set[str]] = {GET, POST, DELETE, PUT}
