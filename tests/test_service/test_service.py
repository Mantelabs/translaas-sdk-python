"""Unit tests for TranslaasService."""

from unittest.mock import AsyncMock, patch

import pytest

# Import shared fixtures from conftest
from tests.conftest import MockCacheProvider  # noqa: F401
from translaas.exceptions import (
    TranslaasConfigurationException,
    TranslaasLanguageResolutionException,
)
from translaas.language.providers import DefaultLanguageProvider
from translaas.language.resolver import LanguageResolver
from translaas.models.options import TranslaasOptions
from translaas.models.request_context import TranslaasRequestContext
from translaas.models.responses import ProjectLocales, TranslationGroup, TranslationProject
from translaas.models.sdk_payloads import ReportMissingKeyItem, ValidateApiKeyResult
from translaas.service import TranslaasService


@pytest.fixture
def language_resolver() -> LanguageResolver:
    """Create language resolver with default provider."""
    return LanguageResolver([DefaultLanguageProvider("en")])


@pytest.fixture
async def service(
    options: TranslaasOptions,
    cache_provider: MockCacheProvider,
    language_resolver: LanguageResolver,
) -> TranslaasService:
    """Create and return a TranslaasService instance."""
    service_instance = TranslaasService(
        options, cache_provider=cache_provider, language_resolver=language_resolver
    )
    async with service_instance:
        yield service_instance


class TestTranslaasServiceInitialization:
    """Tests for TranslaasService initialization."""

    def test_init_with_valid_options(self, options: TranslaasOptions) -> None:
        """Test initialization with valid options."""
        service = TranslaasService(options)
        assert service.options == options
        assert service.cache_provider is None
        assert service.language_resolver is None

    def test_init_with_cache_provider(
        self, options: TranslaasOptions, cache_provider: MockCacheProvider
    ) -> None:
        """Test initialization with cache provider."""
        service = TranslaasService(options, cache_provider=cache_provider)
        assert service.cache_provider == cache_provider

    def test_init_with_language_resolver(
        self, options: TranslaasOptions, language_resolver: LanguageResolver
    ) -> None:
        """Test initialization with language resolver."""
        service = TranslaasService(options, language_resolver=language_resolver)
        assert service.language_resolver == language_resolver


class TestTranslaasServiceContextManager:
    """Tests for TranslaasService context manager support."""

    @pytest.mark.asyncio
    async def test_context_manager_initializes_client(self, options: TranslaasOptions) -> None:
        """Test that context manager initializes the client."""
        async with TranslaasService(options) as service:
            assert service._client is not None
            assert service._client.options == options

    @pytest.mark.asyncio
    async def test_context_manager_cleans_up_client(self, options: TranslaasOptions) -> None:
        """Test that context manager cleans up the client."""
        async with TranslaasService(options) as service:
            client = service._client
            assert client is not None

        # After exiting context, client should be None
        assert service._client is None


class TestTranslaasServiceLanguageResolution:
    """Tests for language resolution in TranslaasService."""

    @pytest.mark.asyncio
    async def test_resolve_language_with_explicit_lang(self, service: TranslaasService) -> None:
        """Test language resolution with explicit language."""
        lang = await service._resolve_language("fr")
        assert lang == "fr"

    @pytest.mark.asyncio
    async def test_resolve_language_with_resolver(
        self, options: TranslaasOptions, language_resolver: LanguageResolver
    ) -> None:
        """Test language resolution with language resolver."""
        service = TranslaasService(options, language_resolver=language_resolver)
        async with service:
            lang = await service._resolve_language(None)
            assert lang == "en"

    @pytest.mark.asyncio
    async def test_resolve_language_with_default_language(self, options: TranslaasOptions) -> None:
        """Test language resolution with default language from options."""
        options.default_language = "es"
        service = TranslaasService(options)
        async with service:
            lang = await service._resolve_language(None)
            assert lang == "es"

    @pytest.mark.asyncio
    async def test_resolve_language_fails_when_no_resolver_or_default(
        self, options: TranslaasOptions
    ) -> None:
        """Test that language resolution fails when no resolver or default."""
        service = TranslaasService(options)
        async with service:
            with pytest.raises(TranslaasLanguageResolutionException):
                await service._resolve_language(None)


class TestTranslaasServiceParameterReplacement:
    """Tests for parameter replacement in TranslaasService."""

    def test_replace_parameters_single_brace(self, service: TranslaasService) -> None:
        """Test parameter replacement with {key} format."""
        text = "Hello {name}, welcome to {app}!"
        parameters = {"name": "John", "app": "Translaas"}
        result = service._replace_parameters(text, parameters)
        assert result == "Hello John, welcome to Translaas!"

    def test_replace_parameters_double_brace(self, service: TranslaasService) -> None:
        """Test parameter replacement with {{key}} format."""
        text = "Hello {{name}}, welcome to {{app}}!"
        parameters = {"name": "John", "app": "Translaas"}
        result = service._replace_parameters(text, parameters)
        assert result == "Hello John, welcome to Translaas!"

    def test_replace_parameters_mixed_formats(self, service: TranslaasService) -> None:
        """Test parameter replacement with mixed formats."""
        text = "Hello {name}, welcome to {{app}}!"
        parameters = {"name": "John", "app": "Translaas"}
        result = service._replace_parameters(text, parameters)
        assert result == "Hello John, welcome to Translaas!"

    def test_replace_parameters_no_parameters(self, service: TranslaasService) -> None:
        """Test parameter replacement with no parameters."""
        text = "Hello {name}!"
        result = service._replace_parameters(text, None)
        assert result == text

    def test_replace_parameters_empty_dict(self, service: TranslaasService) -> None:
        """Test parameter replacement with empty parameters dict."""
        text = "Hello {name}!"
        result = service._replace_parameters(text, {})
        assert result == text

    def test_replace_parameters_special_characters(self, service: TranslaasService) -> None:
        """Test parameter replacement with special characters."""
        text = "Hello {name}!"
        parameters = {"name": "John & Jane"}
        result = service._replace_parameters(text, parameters)
        assert result == "Hello John & Jane!"

    def test_replace_parameters_regex_special_chars(self, service: TranslaasService) -> None:
        """Test parameter replacement with regex special characters in keys."""
        text = "Hello {name}!"
        parameters = {"name": "John"}
        result = service._replace_parameters(text, parameters)
        assert result == "Hello John!"


class TestTranslaasServiceTMethod:
    """Tests for TranslaasService.t() method."""

    @pytest.mark.asyncio
    async def test_t_with_explicit_language(self, service: TranslaasService) -> None:
        """Test t() method with explicit language."""
        with patch.object(service._client, "get_entry", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = "Hello World"
            result = await service.t("group", "entry", "fr")
            assert result == "Hello World"
            mock_get.assert_called_once_with(
                group="group",
                entry="entry",
                lang="fr",
                number=None,
                parameters=None,
                project=None,
                request_context=None,
            )

    @pytest.mark.asyncio
    async def test_t_with_automatic_language_resolution(self, service: TranslaasService) -> None:
        """Test t() method with automatic language resolution."""
        with patch.object(service._client, "get_entry", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = "Hello World"
            result = await service.t("group", "entry")
            assert result == "Hello World"
            mock_get.assert_called_once_with(
                group="group",
                entry="entry",
                lang="en",
                number=None,
                parameters=None,
                project=None,
                request_context=None,
            )

    @pytest.mark.asyncio
    async def test_t_with_number(self, service: TranslaasService) -> None:
        """Test t() method with number for pluralization."""
        with patch.object(service._client, "get_entry", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = "5 items"
            result = await service.t("group", "entry", 5.0)
            assert result == "5 items"
            mock_get.assert_called_once_with(
                group="group",
                entry="entry",
                lang="en",
                number=5.0,
                parameters=None,
                project=None,
                request_context=None,
            )

    @pytest.mark.asyncio
    async def test_t_with_lang_and_number(self, service: TranslaasService) -> None:
        """Test t() method with language and number."""
        with patch.object(service._client, "get_entry", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = "5 items"
            result = await service.t("group", "entry", "fr", 5.0)
            assert result == "5 items"
            mock_get.assert_called_once_with(
                group="group",
                entry="entry",
                lang="fr",
                number=5.0,
                parameters=None,
                project=None,
                request_context=None,
            )

    @pytest.mark.asyncio
    async def test_t_with_parameters(self, service: TranslaasService) -> None:
        """Test t() method with parameters."""
        with patch.object(service._client, "get_entry", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = "Hello {name}!"
            result = await service.t("group", "entry", {"name": "John"})
            assert result == "Hello John!"
            mock_get.assert_called_once_with(
                group="group",
                entry="entry",
                lang="en",
                number=None,
                parameters=None,
                project=None,
                request_context=None,
            )

    @pytest.mark.asyncio
    async def test_t_with_lang_and_parameters(self, service: TranslaasService) -> None:
        """Test t() method with language and parameters."""
        with patch.object(service._client, "get_entry", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = "Hello {name}!"
            result = await service.t("group", "entry", "fr", {"name": "John"})
            assert result == "Hello John!"
            mock_get.assert_called_once_with(
                group="group",
                entry="entry",
                lang="fr",
                number=None,
                parameters=None,
                project=None,
                request_context=None,
            )

    @pytest.mark.asyncio
    async def test_t_fails_without_client(self, options: TranslaasOptions) -> None:
        """Test that t() fails when client is not initialized."""
        service = TranslaasService(options)
        with pytest.raises(TranslaasConfigurationException):
            await service.t("group", "entry", "en")

    @pytest.mark.asyncio
    async def test_t_fails_when_language_cannot_be_resolved(
        self, options: TranslaasOptions
    ) -> None:
        """Test that t() fails when language cannot be resolved."""
        service = TranslaasService(options)
        async with service:
            with pytest.raises(TranslaasLanguageResolutionException):
                await service.t("group", "entry")


class TestTranslaasServiceConvenienceMethods:
    """Tests for TranslaasService convenience methods."""

    @pytest.mark.asyncio
    async def test_get_entry(self, service: TranslaasService) -> None:
        """Test get_entry convenience method."""
        with patch.object(service._client, "get_entry", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = "Hello {name}!"
            result = await service.get_entry("group", "entry", "en", parameters={"name": "John"})
            assert result == "Hello John!"
            mock_get.assert_called_once_with(
                group="group",
                entry="entry",
                lang="en",
                number=None,
                parameters=None,
                project=None,
                request_context=None,
            )

    @pytest.mark.asyncio
    async def test_get_group(self, service: TranslaasService) -> None:
        """Test get_group convenience method."""
        group_data = TranslationGroup(entries={"test": "value"})
        with patch.object(service._client, "get_group", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = group_data
            result = await service.get_group("project", "group", "en")
            assert result == group_data
            mock_get.assert_called_once_with(
                project="project",
                group="group",
                lang="en",
                format=None,
                include_context=None,
                request_context=TranslaasRequestContext(project="project"),
            )

    @pytest.mark.asyncio
    async def test_get_project(self, service: TranslaasService) -> None:
        """Test get_project convenience method."""
        project_data = TranslationProject(groups={"test": {}})
        with patch.object(service._client, "get_project", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = project_data
            result = await service.get_project("project", "en")
            assert result == project_data
            mock_get.assert_called_once_with(
                project="project",
                lang="en",
                format=None,
                include_context=None,
                request_context=TranslaasRequestContext(project="project"),
            )

    @pytest.mark.asyncio
    async def test_get_project_locales(self, service: TranslaasService) -> None:
        """Test get_project_locales convenience method."""
        locales_data = ProjectLocales(locales=["en", "fr"])
        with patch.object(
            service._client, "get_project_locales", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = locales_data
            result = await service.get_project_locales("project")
            assert result == locales_data
            mock_get.assert_called_once_with(
                project="project",
                request_context=TranslaasRequestContext(project="project"),
            )


class TestTranslaasServiceSdkDelegates:
    """``TranslaasService`` passthroughs for validate / report / offline and query kwargs."""

    @pytest.mark.asyncio
    async def test_get_group_forwards_include_channel_version(
        self, service: TranslaasService
    ) -> None:
        grp = TranslationGroup(entries={"a": "b"})
        with patch.object(service._client, "get_group", new_callable=AsyncMock) as mock_gg:
            mock_gg.return_value = grp
            out = await service.get_group(
                "p",
                "g",
                "en",
                format="flat-json",
                include_context=True,
                channel="c",
                snapshot_version="9",
            )
        assert out == grp
        mock_gg.assert_called_once_with(
            project="p",
            group="g",
            lang="en",
            format="flat-json",
            include_context=True,
            request_context=TranslaasRequestContext(
                channel="c",
                version="9",
                project="p",
                include_context=True,
            ),
        )

    @pytest.mark.asyncio
    async def test_validate_api_key_delegates(self, service: TranslaasService) -> None:
        val = ValidateApiKeyResult(
            is_valid=True,
            tenant_id="t",
            project_id="p",
            project_ids=("p",),
            default_project_id="p",
            integration_name="i",
            authenticated_at="2020-01-01T00:00:00Z",
        )
        with patch.object(service._client, "validate_api_key", new_callable=AsyncMock) as m:
            m.return_value = val
            r = await service.validate_api_key()
        assert r == val
        m.assert_called_once_with()

    @pytest.mark.asyncio
    async def test_report_missing_keys_delegates(self, service: TranslaasService) -> None:
        keys = [ReportMissingKeyItem("g", "e", "en")]
        with patch.object(service._client, "report_missing_keys", new_callable=AsyncMock) as m:
            m.return_value = None
            await service.report_missing_keys(keys)
        m.assert_called_once_with(keys)

    @pytest.mark.asyncio
    async def test_get_offline_cache_delegates(self, service: TranslaasService) -> None:
        with patch.object(service._client, "get_offline_cache", new_callable=AsyncMock) as m:
            m.return_value = b"z"
            data = await service.get_offline_cache(
                "proj", include_context=False, channel="ch", snapshot_version="1"
            )
        assert data == b"z"
        m.assert_called_once_with(
            "proj",
            include_context=False,
            channel="ch",
            snapshot_version="1",
            request_context=TranslaasRequestContext(
                channel="ch",
                version="1",
                project="proj",
                include_context=False,
            ),
        )
