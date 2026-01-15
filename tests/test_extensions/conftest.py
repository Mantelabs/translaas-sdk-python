"""Pytest configuration for extension tests."""

import os

import django
from django.conf import settings


def pytest_configure():
    """Configure Django settings for tests."""
    if not settings.configured:
        os.environ.setdefault(
            "DJANGO_SETTINGS_MODULE", "tests.test_extensions.django_test_settings"
        )

        # Minimal Django settings for testing
        settings.configure(
            DEBUG=True,
            SECRET_KEY="test-secret-key-for-testing-only",
            INSTALLED_APPS=[
                "django.contrib.contenttypes",
                "django.contrib.auth",
            ],
            DATABASES={
                "default": {
                    "ENGINE": "django.db.backends.sqlite3",
                    "NAME": ":memory:",
                }
            },
            USE_TZ=True,
            # Translaas settings
            TRANSLAAS_API_KEY="test-api-key",
            TRANSLAAS_BASE_URL="https://api.test.com",
            TRANSLAAS_CACHE_MODE=None,
            TRANSLAAS_TIMEOUT=None,
            TRANSLAAS_CACHE_ABSOLUTE_EXPIRATION=None,
            TRANSLAAS_CACHE_SLIDING_EXPIRATION=None,
            TRANSLAAS_DEFAULT_LANGUAGE=None,
        )

        django.setup()
