"""Enumeration types for the Translaas SDK."""

from enum import Enum


class CacheMode(Enum):
    """Cache mode enumeration for translation caching strategies.

    Defines how translations should be cached:
    - NONE: No caching
    - ENTRY: Cache individual translation entries
    - GROUP: Cache entire translation groups
    - PROJECT: Cache entire translation projects
    """

    NONE = 0
    ENTRY = 1
    GROUP = 2
    PROJECT = 3


class OfflineFallbackMode(Enum):
    """Offline fallback mode enumeration for cache behavior.

    Defines how the SDK should behave when offline or when cache is unavailable:
    - CACHE_FIRST: Try cache first, fallback to API if cache miss
    - API_FIRST: Try API first, fallback to cache if API fails
    - CACHE_ONLY: Only use cache, never call API
    - API_ONLY_WITH_BACKUP: Use API only, but backup responses to cache
    """

    CACHE_FIRST = 0
    API_FIRST = 1
    CACHE_ONLY = 2
    API_ONLY_WITH_BACKUP = 3


class PluralCategory(Enum):
    """Plural category enumeration for plural form handling.

    Represents the different plural categories used in translation systems:
    - ZERO: Zero quantity
    - ONE: Singular form
    - TWO: Dual form
    - FEW: Few items
    - MANY: Many items
    - OTHER: Default/other form
    """

    ZERO = "zero"
    ONE = "one"
    TWO = "two"
    FEW = "few"
    MANY = "many"
    OTHER = "other"
