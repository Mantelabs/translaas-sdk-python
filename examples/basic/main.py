"""Basic Python example demonstrating Translaas SDK usage.

This example shows how to use the Translaas SDK in a vanilla Python application,
including translation lookups, caching, error handling, and async/await usage.
"""

import asyncio
import os
from datetime import timedelta

from dotenv import load_dotenv

from translaas import CacheMode, TranslaasOptions, TranslaasService
from translaas.caching.memory import MemoryCacheProvider
from translaas.exceptions import TranslaasApiException

# Load environment variables from .env file
load_dotenv()


async def main() -> None:
    """Main function demonstrating Translaas SDK usage."""
    print("=" * 60)
    print("Translaas SDK - Basic Python Example")
    print("=" * 60)
    print()

    # Configure Translaas from environment variables
    options = TranslaasOptions(
        api_key=os.getenv("TRANSLAAS_API_KEY", "your-api-key-here"),
        base_url=os.getenv("TRANSLAAS_BASE_URL", "https://api.translaas.com"),
        default_language=os.getenv("TRANSLAAS_DEFAULT_LANGUAGE", "en"),
        cache_mode=CacheMode[os.getenv("TRANSLAAS_CACHE_MODE", "ENTRY")],
        cache_absolute_expiration=timedelta(
            seconds=int(os.getenv("TRANSLAAS_CACHE_ABSOLUTE_EXPIRATION", "3600"))
        ),
        verify=os.getenv("TRANSLAAS_VERIFY", "true").lower() == "true",
    )

    # Create a memory cache provider with statistics enabled
    cache_provider = MemoryCacheProvider(
        max_size=1000,  # Maximum 1000 entries
        enable_statistics=True,  # Track cache hits/misses
    )

    # Create TranslaasService with caching enabled
    service = TranslaasService(options, cache_provider=cache_provider)

    # Use async context manager for proper resource cleanup
    async with service:
        # Example 1: Basic translation lookup
        print("Example 1: Basic Translation Lookup")
        print("-" * 60)
        try:
            translation = await service.t("common", "welcome", "en")
            print(f"Translation: {translation}")
        except TranslaasApiException as e:
            print(f"Error: {e.message} (Status: {e.status_code})")
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
        print()

        # Example 2: Translation with parameters
        print("Example 2: Translation with Parameters")
        print("-" * 60)
        try:
            greeting = await service.t(
                "messages",
                "greeting",
                "en",
                parameters={"name": "Python User"},
            )
            print(f"Greeting: {greeting}")
        except TranslaasApiException as e:
            print(f"Error: {e.message} (Status: {e.status_code})")
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
        print()

        # Example 3: Translation with pluralization
        print("Example 3: Translation with Pluralization")
        print("-" * 60)
        try:
            # Try with different numbers to demonstrate pluralization
            for count in [0, 1, 5]:
                message = await service.t("messages", "item.count", "en", number=count)
                print(f"Items ({count}): {message}")
        except TranslaasApiException as e:
            print(f"Error: {e.message} (Status: {e.status_code})")
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
        print()

        # Example 4: Caching demonstration
        print("Example 4: Caching Demonstration")
        print("-" * 60)
        try:
            # First call - will hit the API
            print("First call (API):")
            translation1 = await service.t("common", "welcome", "en")
            print(f"  Translation: {translation1}")
            print(f"  Cache hits: {cache_provider.hits}, misses: {cache_provider.misses}")

            # Second call - should hit the cache
            print("\nSecond call (Cache):")
            translation2 = await service.t("common", "welcome", "en")
            print(f"  Translation: {translation2}")
            print(f"  Cache hits: {cache_provider.hits}, misses: {cache_provider.misses}")
            print(f"  Cache working: {translation1 == translation2}")
        except TranslaasApiException as e:
            print(f"Error: {e.message} (Status: {e.status_code})")
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
        print()

        # Example 5: Error handling
        print("Example 5: Error Handling")
        print("-" * 60)
        try:
            # Try to get a non-existent translation
            translation = await service.t("nonexistent", "missing", "en")
            print(f"Translation: {translation}")
        except TranslaasApiException as e:
            print(f"Caught TranslaasApiException:")
            print(f"  Message: {e.message}")
            print(f"  Status Code: {e.status_code}")
            if e.inner_error:
                print(f"  Inner Error: {type(e.inner_error).__name__}")
        except Exception as e:
            print(f"Unexpected error: {type(e).__name__}: {str(e)}")
        print()

        # Example 6: Multiple translations
        print("Example 6: Multiple Translations")
        print("-" * 60)
        try:
            translations = await asyncio.gather(
                service.t("common", "welcome", "en"),
                service.t("common", "about", "en"),
                service.t("messages", "greeting", "en", parameters={"name": "User"}),
                return_exceptions=True,
            )

            for i, result in enumerate(translations):
                if isinstance(result, Exception):
                    print(f"  Translation {i + 1}: Error - {str(result)}")
                else:
                    print(f"  Translation {i + 1}: {result}")
        except Exception as e:
            print(f"Error: {str(e)}")
        print()

        # Print cache statistics
        print("Cache Statistics")
        print("-" * 60)
        print(f"Total hits: {cache_provider.hits}")
        print(f"Total misses: {cache_provider.misses}")
        if cache_provider.hits + cache_provider.misses > 0:
            hit_rate = (cache_provider.hits / (cache_provider.hits + cache_provider.misses)) * 100
            print(f"Hit rate: {hit_rate:.1f}%")
        print()

    print("=" * 60)
    print("Example completed!")
    print("=" * 60)


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
