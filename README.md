# Translaas SDK

![Tests](https://github.com/acuencadev/translaas-sdk-python/workflows/CI/badge.svg)

A strongly-typed, performant, and modular Python SDK for consuming the **Translaas Translation Delivery API**. This SDK provides a clean, easy-to-use way to retrieve translations in your Python applications.

## Features

- ✅ **Strongly-typed API** - Full type hints support with IDE autocomplete and type safety
- ✅ **Convenience API** - Simple `t()` method for quick translation lookups via `TranslaasService`
- ✅ **Automatic Language Resolution** - Optional language parameter with configurable providers (HTTP request, default)
- ✅ **Framework Integrations** - Flask, FastAPI, Django, and other framework integrations
- ✅ **Flexible Caching** - Built-in memory caching with configurable cache modes
- ✅ **Offline Caching** - File-based caching for offline mode with automatic sync
- ✅ **Hybrid Caching** - Two-level caching (memory L1 + file L2) for optimal performance
- ✅ **Multi-Environment Support** - Works in Python 3.8+, CPython, PyPy, and modern Python runtimes
- ✅ **Retry & Resilience** - Configurable retry policies and timeouts
- ✅ **Modular Design** - Use only what you need with separate Python packages
- ✅ **Async/Await** - Fully asynchronous API for optimal performance
- ✅ **Type Hints** - Native Python type hints with full IDE support

## Installation

### pip

```bash
pip install translaas
```

### pip with virtual environment (Recommended)

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install translaas
```

### Individual Packages

If you prefer to use individual packages:

- `translaas-models` - Data transfer objects and types
- `translaas-client` - Core HTTP client
- `translaas-caching` - In-memory caching layer
- `translaas-caching-file` - File-based offline caching with hybrid caching support
- `translaas-extensions` - Framework integrations (Flask, FastAPI, Django, etc.)
- `translaas` - Main package (includes all) - **Recommended**

## Quick Start

### 1. Install Package

```bash
pip install translaas
```

### 2. Create Client

**Option A: Using TranslaasService (Recommended for simple lookups)**

```python
from translaas import TranslaasService, TranslaasOptions, CacheMode, LanguageCodes

options = TranslaasOptions(
    api_key='your-api-key-here',
    base_url='https://api.translaas.com',  # or your custom base URL
    cache_mode=CacheMode.GROUP,  # Optional: configure caching
)

translaas = TranslaasService(options)

# Use the convenient t() method
# lang parameter is optional when language providers are configured
welcome = await translaas.t('common', 'welcome', LanguageCodes.ENGLISH)

# Automatic language resolution (requires providers configured)
welcome_auto = await translaas.t('common', 'welcome')  # lang omitted

# With pluralization
items = await translaas.t('messages', 'item', LanguageCodes.ENGLISH, 5)
```

**Option B: Using TranslaasClient (Full API access)**

```python
from translaas import TranslaasClient, TranslaasOptions

options = TranslaasOptions(
    api_key='your-api-key-here',
    base_url='https://api.translaas.com',
)

client = TranslaasClient(options)

# Get a single translation entry
translation = await client.get_entry('common', 'welcome', 'en')
```

## Configuration

### Basic Configuration

```python
from translaas import TranslaasService, TranslaasOptions, LanguageCodes

options = TranslaasOptions(
    # Required: API key and base URL
    api_key='your-api-key',
    base_url='https://api.translaas.com',
)

translaas = TranslaasService(options)
```

### Advanced Configuration

```python
from translaas import TranslaasService, TranslaasOptions, CacheMode, LanguageCodes

options = TranslaasOptions(
    # Required: API key and base URL
    api_key='your-api-key',
    base_url='https://api.translaas.com',

    # Optional: Default language fallback
    default_language=LanguageCodes.ENGLISH,

    # Optional: Caching configuration
    cache_mode=CacheMode.GROUP,
    cache_absolute_expiration=3600.0,  # 1 hour in seconds
    cache_sliding_expiration=900.0,  # 15 minutes in seconds

    # Optional: HTTP Client timeout
    timeout=30.0,  # 30 seconds
)

translaas = TranslaasService(options)
```

**Configuration Options:**

| Option                      | Required        | Description                                                                                |
| --------------------------- | --------------- | ------------------------------------------------------------------------------------------ |
| `api_key`                   | ✅ **Required** | Your Translaas API key                                                                     |
| `base_url`                  | ✅ **Required** | Base URL for the Translaas API (do NOT include `/api`)                                     |
| `default_language`           | ⚪ Optional     | Default language code fallback (e.g., `LanguageCodes.ENGLISH`)                             |
| `cache_mode`                | ⚪ Optional     | Caching mode (`CacheMode.NONE`, `CacheMode.ENTRY`, `CacheMode.GROUP`, `CacheMode.PROJECT`) |
| `cache_absolute_expiration` | ⚪ Optional     | Absolute cache expiration time (seconds)                                                    |
| `cache_sliding_expiration`  | ⚪ Optional     | Sliding cache expiration time (seconds)                                                    |
| `timeout`                   | ⚪ Optional     | HTTP client timeout (seconds)                                                             |

### Configuration from Environment Variables

```bash
# .env file
TRANSLAAS_API_KEY=your-api-key
TRANSLAAS_BASE_URL=https://api.translaas.com
TRANSLAAS_CACHE_MODE=GROUP
TRANSLAAS_DEFAULT_LANGUAGE=en
```

```python
import os
from translaas import TranslaasService, TranslaasOptions, CacheMode

options = TranslaasOptions(
    api_key=os.getenv('TRANSLAAS_API_KEY'),
    base_url=os.getenv('TRANSLAAS_BASE_URL', 'https://api.translaas.com'),
    cache_mode=CacheMode[os.getenv('TRANSLAAS_CACHE_MODE', 'NONE')],
    default_language=os.getenv('TRANSLAAS_DEFAULT_LANGUAGE'),
)

translaas = TranslaasService(options)
```

**Note:** `api_key` should be stored in environment variables or secure configuration, not in source code.

## Usage Examples

### Get Single Translation Entry

**Using TranslaasService (Convenience API):**

```python
from translaas import LanguageCodes

# Basic usage with explicit language
translation = await translaas.t('ui', 'button.save', LanguageCodes.ENGLISH)

# Automatic language resolution (requires providers configured)
translation = await translaas.t('ui', 'button.save')  # lang omitted

# With pluralization
message = await translaas.t('messages', 'item.count', LanguageCodes.ENGLISH, 5)
```

**Using TranslaasClient (Full API):**

```python
from translaas import LanguageCodes

# Basic usage
translation = await client.get_entry('ui', 'button.save', LanguageCodes.ENGLISH)

# With pluralization
message = await client.get_entry(
    'messages',
    'item.count',
    LanguageCodes.ENGLISH,
    5  # Used for pluralization rules
)
```

## Environment Compatibility

The SDK supports multiple Python environments:

| Environment | Compatible With                |
| ---------- | ------------------------------ |
| CPython    | Python 3.8+                   |
| PyPy       | PyPy 3.8+                      |
| AsyncIO    | Full async/await support       |

The SDK uses `httpx` for async HTTP requests and `requests` for synchronous requests.

## Error Handling

```python
from translaas import TranslaasApiException, LanguageCodes

try:
    translation = await client.get_entry('group', 'entry', LanguageCodes.ENGLISH)
except TranslaasApiException as e:
    # Handle Translaas-specific errors
    print(f"Error: {e.message}")
    print(f"Status Code: {e.status_code}")
except Exception as e:
    # Handle other errors
    print(f"Error: {str(e)}")
```

## Development

### Building from Source

```bash
git clone https://github.com/acuencadev/translaas-sdk-python.git
cd translaas-sdk-python
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[dev]"
python -m build
```

### Running Tests

```bash
pytest
```

### Running Tests with Coverage

```bash
pytest --cov=translaas --cov-report=html
```

## API Endpoints

The SDK communicates with the following Translaas API endpoints:

| Endpoint                    | Method | Purpose                             |
| --------------------------- | ------ | ----------------------------------- |
| `/api/translations/text`    | GET    | Get single translation entry        |
| `/api/translations/group`   | GET    | Get all translations for a group    |
| `/api/translations/project` | GET    | Get all translations for a project  |
| `/api/translations/locales` | GET    | Get available locales for a project |

**Note:** All endpoints use GET requests with query parameters.

## Authentication

The SDK uses API key authentication via the `X-Api-Key` header. Provide your API key during client creation:

```python
options = TranslaasOptions(
    api_key='your-api-key-here',
    base_url='https://api.translaas.com',
)
```

## Examples

We provide example applications demonstrating how to use the Translaas SDK in different environments:

### Basic Python Example

Basic Python application showing translation lookups, caching, and error handling.

```bash
cd examples/basic
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

[View Basic Python Example →](examples/basic/)

### Flask Example

Flask server with middleware integration and automatic language resolution from HTTP requests.

```bash
cd examples/flask
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

[View Flask Example →](examples/flask/)

### FastAPI Example

FastAPI application with async support, dependency injection, and automatic language resolution.

```bash
cd examples/fastapi
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

[View FastAPI Example →](examples/fastapi/)

### Django Example

Django application with middleware integration, template tags, and automatic language resolution.

```bash
cd examples/django
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py runserver
```

[View Django Example →](examples/django/)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Copyright (c) 2025 Translaas SDK Contributors

## Support

- **Documentation**: [Link to full documentation]
- **Issues**: [https://github.com/acuencadev/translaas-sdk-python/issues]
- **API Reference**: [Swagger/API Docs URL]

## Contributing

We welcome contributions to the Translaas SDK! Please read our [Contributing Guidelines](CONTRIBUTING.md) for details on:

- How to get started
- Development guidelines and code style
- Pull request process
- Commit message conventions
- Reporting issues

For more information, see [CONTRIBUTING.md](CONTRIBUTING.md).

---

**Made with ❤️ for the Python community**
