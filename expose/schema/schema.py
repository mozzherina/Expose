"""This module defines types and constants for requests."""

from typing import Final

# These constants are used to determine which type of abstraction should be applied
PARTHOOD_ABS: Final[str] = "parthood"
HIERARCHY_ABS: Final[str] = "hierarchy"
ASPECTS_ABS: Final[str] = "aspects"
ABSTRACTION_TYPE = (PARTHOOD_ABS, HIERARCHY_ABS, ASPECTS_ABS)
