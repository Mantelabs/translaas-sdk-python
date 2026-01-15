# Django Integration

The Translaas SDK provides seamless integration with Django applications, including template tags and helper methods.

## Installation

Install the Django integration along with the SDK:

```bash
pip install translaas[django]
```

Or install Django separately:

```bash
pip install translaas django>=4.0.0
```

## Quick Start

### 1. Configure Settings

Add Translaas configuration to your Django `settings.py`:

```python
# settings.py
TRANSLAAS_API_KEY = "your-api-key"
TRANSLAAS_BASE_URL = "https://api.translaas.com"
TRANSLAAS_DEFAULT_LANGUAGE = "en"
```

### 2. Use in Views

```python
from translaas.extensions.django import t

def index(request):
    # Get translation programmatically
    welcome = t("common", "welcome", request=request)
    greeting = t("messages", "greeting", request=request, parameters={"name": "User"})

    return render(request, "index.html", {"welcome": welcome, "greeting": greeting})
```

### 3. Use Template Tags

Load the template tags in your templates:

```django
{% load translaas_tags %}

<h1>{% translaas "common" "welcome" %}</h1>
<p>{% translaas "messages" "greeting" name="User" %}</p>
```

## Configuration

### Django Settings

Configure Translaas in your Django `settings.py`:

```python
TRANSLAAS_API_KEY = "your-api-key"
TRANSLAAS_BASE_URL = "https://api.translaas.com"
TRANSLAAS_CACHE_MODE = "GROUP"
TRANSLAAS_TIMEOUT = 30.0  # seconds
TRANSLAAS_DEFAULT_LANGUAGE = "en"
```

### Using Configuration Helpers

```python
from django.conf import settings
from translaas.extensions.config import django_config

# Get options from Django settings
options = django_config(settings)
```

## Features

### Automatic Language Resolution

The Django integration automatically detects the user's language from:
- Django's `LANGUAGE_CODE` attribute on the request
- `Accept-Language` header
- `language` cookie
- `lang` query parameter

### Template Tags

Use the `translaas` template tag in Django templates:

```django
{% load translaas_tags %}

<!-- Simple translation -->
{% translaas "common" "welcome" %}

<!-- With parameters -->
{% translaas "messages" "greeting" name="John" %}

<!-- With language -->
{% translaas "common" "welcome" lang="fr" %}

<!-- With plural -->
{% translaas "messages" "item" number=5 %}
```

### Programmatic Usage

Use the `t()` helper function in your views:

```python
from translaas.extensions.django import t

def my_view(request):
    # Automatic language resolution
    welcome = t("common", "welcome", request=request)

    # Explicit language
    welcome_fr = t("common", "welcome", request=request, lang="fr")

    # With parameters
    greeting = t("messages", "greeting", request=request, parameters={"name": "John"})

    # With plural
    items = t("messages", "item", request=request, number=5)

    return render(request, "template.html", {"welcome": welcome})
```

### Getting Service Instance

You can also get a `TranslaasService` instance directly:

```python
from translaas.extensions.django import get_translaas_service

def my_view(request):
    service = get_translaas_service(request)
    # Use service as needed
    # Note: service is async, so you'll need to handle async operations
```

## Template Tags Location

The Django template tags are located in `translaas.extensions.templatetags.translaas_tags`.

Make sure Django can find the template tags by ensuring `translaas` is in your `INSTALLED_APPS` or the template tags directory is accessible.

## API Reference

### t()

Helper function to get translations synchronously.

```python
from translaas.extensions.django import t

translation = t("group", "entry", request=request)
```

### get_translaas_service()

Get a `TranslaasService` instance configured for the current request.

```python
from translaas.extensions.django import get_translaas_service

service = get_translaas_service(request)
```

### DjangoRequestLanguageProvider

Language provider that extracts language from Django request objects.

```python
from translaas.extensions.django import DjangoRequestLanguageProvider

provider = DjangoRequestLanguageProvider(request)
language = await provider.get_language()
```

## Example Application

See `examples/django/` for a complete example application.
