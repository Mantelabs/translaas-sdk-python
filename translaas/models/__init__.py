"""Data transfer objects and models for the Translaas SDK."""

# Enums
from translaas.models.enums import CacheMode, OfflineFallbackMode, PluralCategory

# Language codes
from translaas.models.language_codes import LanguageCodes

# Configuration models
from translaas.models.options import (
    HybridCacheOptions,
    OfflineCacheOptions,
    TranslaasOptions,
)

# Protocols
from translaas.models.protocols import (
    ILanguageProvider,
    ITranslaasCacheProvider,
    ITranslaasClient,
    ITranslaasService,
)

# Response models
from translaas.models.responses import (
    ProjectLocales,
    TranslationGroup,
    TranslationProject,
)

# Type aliases
from translaas.models.types import CacheKey, LanguageCode, TranslationValue

__all__ = [
    # Enums
    "CacheMode",
    "OfflineFallbackMode",
    "PluralCategory",
    # Language codes
    "LanguageCodes",
    # Type aliases
    "LanguageCode",
    "CacheKey",
    "TranslationValue",
    # Configuration models
    "TranslaasOptions",
    "OfflineCacheOptions",
    "HybridCacheOptions",
    # Response models
    "TranslationGroup",
    "TranslationProject",
    "ProjectLocales",
    # Protocols
    "ITranslaasClient",
    "ITranslaasService",
    "ITranslaasCacheProvider",
    "ILanguageProvider",
]
