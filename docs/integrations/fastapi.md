# FastAPI Integration

The Translaas SDK provides seamless integration with FastAPI applications, including dependency injection and async support.

## Installation

Install the FastAPI integration along with the SDK:

```bash
pip install translaas[fastapi]
```

Or install FastAPI separately:

```bash
pip install translaas fastapi>=0.100.0
```

## Quick Start

### 1. Initialize the Extension

```python
from fastapi import FastAPI
from translaas import TranslaasOptions
from translaas.extensions.fastapi import FastAPITranslaas

app = FastAPI()

# Configure Translaas
options = TranslaasOptions(
    api_key="your-api-key",
    base_url="https://api.translaas.com",
    default_language="en",
)

# Initialize extension
translaas = FastAPITranslaas()
translaas.init_app(app, options)
```

### 2. Use Dependency Injection

```python
from fastapi import Depends
from translaas.extensions.fastapi import get_translaas_service
from translaas.service import TranslaasService

@app.get("/")
async def index(service: TranslaasService = Depends(get_translaas_service)):
    # Get translation using injected service
    welcome = await service.t("common", "welcome")
    return {"message": welcome}
```

## Configuration

### Application State

You can configure Translaas by setting options in the app state:

```python
from translaas import TranslaasOptions

options = TranslaasOptions(
    api_key="your-api-key",
    base_url="https://api.translaas.com",
    cache_mode=CacheMode.GROUP,
    timeout=timedelta(seconds=30),
    default_language="en",
)

app.state.translaas_options = options
translaas.init_app(app)
```

## Features

### Dependency Injection

FastAPI's dependency injection system automatically provides a `TranslaasService` instance configured for each request:

```python
@app.get("/")
async def index(service: TranslaasService = Depends(get_translaas_service)):
    # Service is automatically configured with language resolution from request
    translation = await service.t("common", "welcome")
    return {"message": translation}
```

### Automatic Language Resolution

The FastAPI integration automatically detects the user's language from:
- `Accept-Language` header
- `language` cookie
- `lang` query parameter

### Async Support

All Translaas operations are async and work seamlessly with FastAPI's async route handlers:

```python
@app.get("/translations/{group}/{entry}")
async def get_translation(
    group: str,
    entry: str,
    lang: str = None,
    service: TranslaasService = Depends(get_translaas_service),
):
    if lang:
        translation = await service.t(group, entry, lang)
    else:
        translation = await service.t(group, entry)

    return {"translation": translation}
```

## API Reference

### FastAPITranslaas

The main extension class for FastAPI integration.

#### Methods

- `init_app(app, options=None)`: Initialize the extension with a FastAPI app

### get_translaas_service

Dependency function that provides a `TranslaasService` instance for each request.

```python
from fastapi import Depends
from translaas.extensions.fastapi import get_translaas_service
from translaas.service import TranslaasService

@app.get("/")
async def index(service: TranslaasService = Depends(get_translaas_service)):
    translation = await service.t("common", "welcome")
    return {"message": translation}
```

### FastAPIRequestLanguageProvider

Language provider that extracts language from FastAPI request objects.

```python
from translaas.extensions.fastapi import FastAPIRequestLanguageProvider

provider = FastAPIRequestLanguageProvider(request)
language = await provider.get_language()
```

## Example Application

See `examples/fastapi/app.py` for a complete example application.
