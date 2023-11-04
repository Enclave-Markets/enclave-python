"""Provides constants for types"""

from typing import Final, Set

GET: Final[str] = "GET"
POST: Final[str] = "POST"
DELETE: Final[str] = "DELETE"
VERBS: Final[Set[str]] = {GET, POST, DELETE}
