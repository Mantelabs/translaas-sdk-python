"""Tests for exception classes."""

from unittest.mock import Mock

import httpx

from translaas.exceptions import (
    TranslaasApiException,
    TranslaasConfigurationException,
    TranslaasException,
    TranslaasLanguageResolutionException,
    TranslaasOfflineCacheException,
    TranslaasOfflineCacheMissException,
    create_api_exception_from_httpx_error,
)


class TestTranslaasException:
    """Tests for TranslaasException base class."""

    def test_create_with_message_only(self) -> None:
        """Test creating exception with message only."""
        exc = TranslaasException("Test error message")
        assert str(exc) == "Test error message"
        assert exc.message == "Test error message"
        assert exc.inner_error is None

    def test_create_with_inner_error(self) -> None:
        """Test creating exception with inner error."""
        inner = ValueError("Inner error")
        exc = TranslaasException("Test error message", inner_error=inner)
        assert exc.message == "Test error message"
        assert exc.inner_error == inner
        assert "caused by: ValueError" in str(exc)
        assert "Inner error" in str(exc)

    def test_str_without_inner_error(self) -> None:
        """Test __str__ method without inner error."""
        exc = TranslaasException("Simple error")
        assert str(exc) == "Simple error"

    def test_str_with_inner_error(self) -> None:
        """Test __str__ method with inner error."""
        inner = RuntimeError("Something went wrong")
        exc = TranslaasException("Wrapper error", inner_error=inner)
        result = str(exc)
        assert "Wrapper error" in result
        assert "RuntimeError" in result
        assert "Something went wrong" in result


class TestTranslaasApiException:
    """Tests for TranslaasApiException."""

    def test_create_with_message_only(self) -> None:
        """Test creating API exception with message only."""
        exc = TranslaasApiException("API error")
        assert str(exc) == "API error"
        assert exc.message == "API error"
        assert exc.status_code is None
        assert exc.inner_error is None

    def test_create_with_status_code(self) -> None:
        """Test creating API exception with status code."""
        exc = TranslaasApiException("API error", status_code=404)
        assert exc.status_code == 404
        assert "status: 404" in str(exc)

    def test_create_with_inner_error(self) -> None:
        """Test creating API exception with inner error."""
        inner = ValueError("Inner error")
        exc = TranslaasApiException("API error", inner_error=inner)
        assert exc.inner_error == inner
        assert "caused by: ValueError" in str(exc)

    def test_create_with_status_code_and_inner_error(self) -> None:
        """Test creating API exception with both status code and inner error."""
        inner = httpx.HTTPStatusError("Not Found", request=Mock(), response=Mock())
        exc = TranslaasApiException(
            "API request failed",
            status_code=404,
            inner_error=inner,
        )
        assert exc.status_code == 404
        assert exc.inner_error == inner
        result = str(exc)
        assert "status: 404" in result
        assert "HTTPStatusError" in result

    def test_str_without_status_code(self) -> None:
        """Test __str__ method without status code."""
        exc = TranslaasApiException("Simple API error")
        assert str(exc) == "Simple API error"

    def test_str_with_status_code(self) -> None:
        """Test __str__ method with status code."""
        exc = TranslaasApiException("API error", status_code=500)
        assert str(exc) == "API error (status: 500)"

    def test_str_with_status_code_and_inner_error(self) -> None:
        """Test __str__ method with status code and inner error."""
        inner = RuntimeError("Network issue")
        exc = TranslaasApiException(
            "API error",
            status_code=503,
            inner_error=inner,
        )
        result = str(exc)
        assert "status: 503" in result
        assert "RuntimeError" in result
        assert "Network issue" in result


class TestTranslaasConfigurationException:
    """Tests for TranslaasConfigurationException."""

    def test_create_with_message_only(self) -> None:
        """Test creating configuration exception with message only."""
        exc = TranslaasConfigurationException("Configuration error")
        assert str(exc) == "Configuration error"
        assert exc.message == "Configuration error"
        assert exc.inner_error is None

    def test_create_with_inner_error(self) -> None:
        """Test creating configuration exception with inner error."""
        inner = ValueError("Invalid value")
        exc = TranslaasConfigurationException(
            "Configuration error",
            inner_error=inner,
        )
        assert exc.inner_error == inner
        assert "caused by: ValueError" in str(exc)

    def test_inheritance(self) -> None:
        """Test that TranslaasConfigurationException inherits from TranslaasException."""
        exc = TranslaasConfigurationException("Test")
        assert isinstance(exc, TranslaasException)


class TestTranslaasOfflineCacheException:
    """Tests for TranslaasOfflineCacheException."""

    def test_create_with_message_only(self) -> None:
        """Test creating cache exception with message only."""
        exc = TranslaasOfflineCacheException("Cache error")
        assert str(exc) == "Cache error"
        assert exc.message == "Cache error"
        assert exc.inner_error is None

    def test_create_with_inner_error(self) -> None:
        """Test creating cache exception with inner error."""
        inner = OSError("File not found")
        exc = TranslaasOfflineCacheException("Cache error", inner_error=inner)
        assert exc.inner_error == inner
        assert "caused by: OSError" in str(exc)

    def test_inheritance(self) -> None:
        """Test that TranslaasOfflineCacheException inherits from TranslaasException."""
        exc = TranslaasOfflineCacheException("Test")
        assert isinstance(exc, TranslaasException)


class TestTranslaasOfflineCacheMissException:
    """Tests for TranslaasOfflineCacheMissException."""

    def test_create_with_message_only(self) -> None:
        """Test creating cache miss exception with message only."""
        exc = TranslaasOfflineCacheMissException("Cache miss")
        assert str(exc) == "Cache miss"
        assert exc.message == "Cache miss"
        assert exc.cache_key is None
        assert exc.inner_error is None

    def test_create_with_cache_key(self) -> None:
        """Test creating cache miss exception with cache key."""
        exc = TranslaasOfflineCacheMissException(
            "Cache miss",
            cache_key="project:group:entry:lang",
        )
        assert exc.cache_key == "project:group:entry:lang"
        assert "key: project:group:entry:lang" in str(exc)

    def test_create_with_inner_error(self) -> None:
        """Test creating cache miss exception with inner error."""
        inner = KeyError("key")
        exc = TranslaasOfflineCacheMissException(
            "Cache miss",
            inner_error=inner,
        )
        assert exc.inner_error == inner
        assert "caused by: KeyError" in str(exc)

    def test_create_with_cache_key_and_inner_error(self) -> None:
        """Test creating cache miss exception with both cache key and inner error."""
        inner = OSError("File not found")
        exc = TranslaasOfflineCacheMissException(
            "Cache miss",
            cache_key="test-key",
            inner_error=inner,
        )
        assert exc.cache_key == "test-key"
        assert exc.inner_error == inner
        result = str(exc)
        assert "key: test-key" in result
        assert "OSError" in result

    def test_str_with_cache_key(self) -> None:
        """Test __str__ method with cache key."""
        exc = TranslaasOfflineCacheMissException(
            "Translation not found",
            cache_key="my-key",
        )
        assert str(exc) == "Translation not found (key: my-key)"

    def test_inheritance(self) -> None:
        """Test that TranslaasOfflineCacheMissException inherits from TranslaasOfflineCacheException."""
        exc = TranslaasOfflineCacheMissException("Test")
        assert isinstance(exc, TranslaasOfflineCacheException)
        assert isinstance(exc, TranslaasException)


class TestTranslaasLanguageResolutionException:
    """Tests for TranslaasLanguageResolutionException."""

    def test_create_with_message_only(self) -> None:
        """Test creating language resolution exception with message only."""
        exc = TranslaasLanguageResolutionException("Language resolution error")
        assert str(exc) == "Language resolution error"
        assert exc.message == "Language resolution error"
        assert exc.language_code is None
        assert exc.inner_error is None

    def test_create_with_language_code(self) -> None:
        """Test creating language resolution exception with language code."""
        exc = TranslaasLanguageResolutionException(
            "Invalid language code",
            language_code="xyz",
        )
        assert exc.language_code == "xyz"
        assert "language: xyz" in str(exc)

    def test_create_with_inner_error(self) -> None:
        """Test creating language resolution exception with inner error."""
        inner = ValueError("Invalid format")
        exc = TranslaasLanguageResolutionException(
            "Language resolution error",
            inner_error=inner,
        )
        assert exc.inner_error == inner
        assert "caused by: ValueError" in str(exc)

    def test_create_with_language_code_and_inner_error(self) -> None:
        """Test creating language resolution exception with both language code and inner error."""
        inner = KeyError("not found")
        exc = TranslaasLanguageResolutionException(
            "Language resolution error",
            language_code="invalid",
            inner_error=inner,
        )
        assert exc.language_code == "invalid"
        assert exc.inner_error == inner
        result = str(exc)
        assert "language: invalid" in result
        assert "KeyError" in result

    def test_str_with_language_code(self) -> None:
        """Test __str__ method with language code."""
        exc = TranslaasLanguageResolutionException(
            "Invalid language",
            language_code="xx",
        )
        assert str(exc) == "Invalid language (language: xx)"

    def test_inheritance(self) -> None:
        """Test that TranslaasLanguageResolutionException inherits from TranslaasException."""
        exc = TranslaasLanguageResolutionException("Test")
        assert isinstance(exc, TranslaasException)


class TestCreateApiExceptionFromHttpxError:
    """Tests for create_api_exception_from_httpx_error factory function."""

    def test_create_from_http_status_error(self) -> None:
        """Test creating exception from HTTPStatusError."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.status_text = "Not Found"
        error = httpx.HTTPStatusError(
            "Not Found",
            request=Mock(),
            response=mock_response,
        )

        exc = create_api_exception_from_httpx_error(error)
        assert isinstance(exc, TranslaasApiException)
        assert exc.status_code == 404
        assert exc.inner_error == error
        assert "Not Found" in str(exc)

    def test_create_from_http_status_error_without_status_text(self) -> None:
        """Test creating exception from HTTPStatusError without status_text."""
        mock_response = Mock()
        mock_response.status_code = 500
        del mock_response.status_text  # Remove status_text attribute
        error = httpx.HTTPStatusError(
            "Internal Server Error",
            request=Mock(),
            response=mock_response,
        )

        exc = create_api_exception_from_httpx_error(error)
        assert isinstance(exc, TranslaasApiException)
        assert exc.status_code == 500
        assert "status 500" in str(exc)

    def test_create_from_timeout_exception(self) -> None:
        """Test creating exception from TimeoutException."""
        error = httpx.TimeoutException("Request timed out", request=Mock())

        exc = create_api_exception_from_httpx_error(error)
        assert isinstance(exc, TranslaasApiException)
        assert exc.status_code is None
        assert exc.inner_error == error
        assert "timed out" in str(exc)

    def test_create_from_connect_error(self) -> None:
        """Test creating exception from ConnectError."""
        error = httpx.ConnectError("Connection failed", request=Mock())

        exc = create_api_exception_from_httpx_error(error)
        assert isinstance(exc, TranslaasApiException)
        assert exc.status_code is None
        assert exc.inner_error == error
        assert "Failed to connect" in str(exc)

    def test_create_from_network_error(self) -> None:
        """Test creating exception from NetworkError."""
        error = httpx.NetworkError("Network issue", request=Mock())

        exc = create_api_exception_from_httpx_error(error)
        assert isinstance(exc, TranslaasApiException)
        assert exc.status_code is None
        assert exc.inner_error == error
        assert "Network error" in str(exc)

    def test_create_from_request_error_with_default_message(self) -> None:
        """Test creating exception from RequestError with default message."""
        error = httpx.RequestError("Request failed", request=Mock())

        exc = create_api_exception_from_httpx_error(
            error,
            default_message="Custom error message",
        )
        assert isinstance(exc, TranslaasApiException)
        assert exc.inner_error == error
        assert "Custom error message" in str(exc)

    def test_create_from_generic_exception(self) -> None:
        """Test creating exception from generic Exception."""
        error = ValueError("Some error")

        exc = create_api_exception_from_httpx_error(error)
        assert isinstance(exc, TranslaasApiException)
        assert exc.status_code is None
        assert exc.inner_error == error
        assert "Some error" in str(exc)

    def test_create_with_default_message(self) -> None:
        """Test creating exception with default message."""
        error = Exception("Generic error")

        exc = create_api_exception_from_httpx_error(
            error,
            default_message="API request failed",
        )
        assert isinstance(exc, TranslaasApiException)
        assert "API request failed" in str(exc)
