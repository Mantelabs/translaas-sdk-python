"""Exception classes for the Translaas Python SDK.

This module provides comprehensive exception handling for the Translaas SDK,
including base exceptions, API exceptions, configuration exceptions, cache
exceptions, and language resolution exceptions.
"""

from typing import Optional


class TranslaasException(Exception):
    """Base exception class for all Translaas SDK exceptions.

    This exception serves as the base class for all exceptions raised by the
    Translaas SDK. It provides error context preservation through the
    `inner_error` attribute.

    Attributes:
        message: The error message describing what went wrong.
        inner_error: Optional inner exception that caused this exception.

    Example:
        ```python
        try:
            # Some operation
            pass
        except ValueError as e:
            raise TranslaasException("Operation failed", inner_error=e) from e
        ```
    """

    def __init__(
        self,
        message: str,
        *,
        inner_error: Optional[Exception] = None,
    ) -> None:
        """Initialize a TranslaasException.

        Args:
            message: The error message describing what went wrong.
            inner_error: Optional inner exception that caused this exception.
        """
        super().__init__(message)
        self.message = message
        self.inner_error = inner_error

    def __str__(self) -> str:
        """Return a string representation of the exception.

        Returns:
            The error message, optionally including inner error information.
        """
        if self.inner_error:
            return (
                f"{self.message} (caused by: {type(self.inner_error).__name__}: {self.inner_error})"
            )
        return self.message


class TranslaasApiException(TranslaasException):
    """Exception raised when an API request fails.

    This exception is raised when an HTTP request to the Translaas API fails
    or returns an error status code. It includes the HTTP status code and
    response details.

    Attributes:
        message: The error message describing what went wrong.
        status_code: The HTTP status code returned by the API.
        inner_error: Optional inner exception that caused this exception.

    Example:
        ```python
        try:
            response = await client.get(url)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise TranslaasApiException(
                f"API request failed: {e.response.status_text}",
                status_code=e.response.status_code,
                inner_error=e
            ) from e
        ```
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: Optional[int] = None,
        inner_error: Optional[Exception] = None,
    ) -> None:
        """Initialize a TranslaasApiException.

        Args:
            message: The error message describing what went wrong.
            status_code: Optional HTTP status code returned by the API.
            inner_error: Optional inner exception that caused this exception.
        """
        super().__init__(message, inner_error=inner_error)
        self.status_code = status_code

    def __str__(self) -> str:
        """Return a string representation of the exception.

        Returns:
            The error message, optionally including status code and inner error.
        """
        base_message = self.message
        if self.status_code is not None:
            base_message = f"{base_message} (status: {self.status_code})"
        if self.inner_error:
            return (
                f"{base_message} (caused by: {type(self.inner_error).__name__}: {self.inner_error})"
            )
        return base_message


class TranslaasConfigurationException(TranslaasException):
    """Exception raised when SDK configuration is invalid.

    This exception is raised when the SDK configuration is invalid or missing
    required parameters.

    Attributes:
        message: The error message describing the configuration issue.
        inner_error: Optional inner exception that caused this exception.

    Example:
        ```python
        if not api_key:
            raise TranslaasConfigurationException(
                "api_key is required and cannot be empty"
            )
        ```
    """

    def __init__(
        self,
        message: str,
        *,
        inner_error: Optional[Exception] = None,
    ) -> None:
        """Initialize a TranslaasConfigurationException.

        Args:
            message: The error message describing the configuration issue.
            inner_error: Optional inner exception that caused this exception.
        """
        super().__init__(message, inner_error=inner_error)


class TranslaasOfflineCacheException(TranslaasException):
    """Base exception for offline cache-related errors.

    This exception serves as the base class for all offline cache exceptions.
    It is raised when there is a general error with the offline cache system.

    Attributes:
        message: The error message describing what went wrong.
        inner_error: Optional inner exception that caused this exception.

    Example:
        ```python
        try:
            # Cache operation
            pass
        except IOError as e:
            raise TranslaasOfflineCacheException(
                "Failed to access cache directory",
                inner_error=e
            ) from e
        ```
    """

    def __init__(
        self,
        message: str,
        *,
        inner_error: Optional[Exception] = None,
    ) -> None:
        """Initialize a TranslaasOfflineCacheException.

        Args:
            message: The error message describing what went wrong.
            inner_error: Optional inner exception that caused this exception.
        """
        super().__init__(message, inner_error=inner_error)


class TranslaasOfflineCacheMissException(TranslaasOfflineCacheException):
    """Exception raised when a cache lookup fails (cache miss).

    This exception is raised when a requested translation is not found in
    the offline cache and cannot be retrieved from the API (e.g., when offline).

    Attributes:
        message: The error message describing the cache miss.
        cache_key: Optional cache key that was not found.
        inner_error: Optional inner exception that caused this exception.

    Example:
        ```python
        if not cache.get(cache_key):
            raise TranslaasOfflineCacheMissException(
                f"Translation not found in cache: {cache_key}",
                cache_key=cache_key
            )
        ```
    """

    def __init__(
        self,
        message: str,
        *,
        cache_key: Optional[str] = None,
        inner_error: Optional[Exception] = None,
    ) -> None:
        """Initialize a TranslaasOfflineCacheMissException.

        Args:
            message: The error message describing the cache miss.
            cache_key: Optional cache key that was not found.
            inner_error: Optional inner exception that caused this exception.
        """
        super().__init__(message, inner_error=inner_error)
        self.cache_key = cache_key

    def __str__(self) -> str:
        """Return a string representation of the exception.

        Returns:
            The error message, optionally including cache key and inner error.
        """
        base_message = self.message
        if self.cache_key:
            base_message = f"{base_message} (key: {self.cache_key})"
        if self.inner_error:
            return (
                f"{base_message} (caused by: {type(self.inner_error).__name__}: {self.inner_error})"
            )
        return base_message


class TranslaasLanguageResolutionException(TranslaasException):
    """Exception raised when language resolution fails.

    This exception is raised when the SDK cannot resolve a language code
    or determine the appropriate language to use.

    Attributes:
        message: The error message describing the language resolution failure.
        language_code: Optional language code that could not be resolved.
        inner_error: Optional inner exception that caused this exception.

    Example:
        ```python
        if not is_valid_language_code(lang):
            raise TranslaasLanguageResolutionException(
                f"Invalid language code: {lang}",
                language_code=lang
            )
        ```
    """

    def __init__(
        self,
        message: str,
        *,
        language_code: Optional[str] = None,
        inner_error: Optional[Exception] = None,
    ) -> None:
        """Initialize a TranslaasLanguageResolutionException.

        Args:
            message: The error message describing the language resolution failure.
            language_code: Optional language code that could not be resolved.
            inner_error: Optional inner exception that caused this exception.
        """
        super().__init__(message, inner_error=inner_error)
        self.language_code = language_code

    def __str__(self) -> str:
        """Return a string representation of the exception.

        Returns:
            The error message, optionally including language code and inner error.
        """
        base_message = self.message
        if self.language_code:
            base_message = f"{base_message} (language: {self.language_code})"
        if self.inner_error:
            return (
                f"{base_message} (caused by: {type(self.inner_error).__name__}: {self.inner_error})"
            )
        return base_message


def create_api_exception_from_httpx_error(
    error: Exception,
    *,
    default_message: Optional[str] = None,
) -> TranslaasApiException:
    """Create a TranslaasApiException from an httpx error.

    This factory function converts httpx exceptions into TranslaasApiException
    instances, preserving error context and extracting HTTP status codes when
    available.

    Args:
        error: The httpx exception to convert.
        default_message: Optional default message if one cannot be extracted
            from the error.

    Returns:
        A TranslaasApiException instance with appropriate error details.

    Example:
        ```python
        try:
            response = await client.get(url)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise create_api_exception_from_httpx_error(e)
        except httpx.RequestError as e:
            raise create_api_exception_from_httpx_error(
                e,
                default_message="Failed to connect to API"
            )
        ```
    """
    import httpx

    message = default_message or str(error)

    # Extract status code from HTTPStatusError
    status_code: Optional[int] = None
    if isinstance(error, httpx.HTTPStatusError):
        status_code = error.response.status_code
        if hasattr(error.response, "status_text"):
            message = f"API request failed: {error.response.status_text}"
        else:
            message = f"API request failed with status {status_code}"

    # Provide more specific messages for common error types
    if isinstance(error, httpx.TimeoutException):
        message = "API request timed out"
    elif isinstance(error, httpx.ConnectError):
        message = "Failed to connect to API"
    elif isinstance(error, httpx.NetworkError):
        message = "Network error occurred while connecting to API"

    return TranslaasApiException(
        message,
        status_code=status_code,
        inner_error=error,
    )
