# Flask Integration

The Translaas SDK provides seamless integration with Flask applications, including initialization, template filters, and helper methods.

## Installation

Install the Flask integration along with the SDK:

```bash
pip install translaas[flask]
```

Or install Flask separately:

```bash
pip install translaas flask>=2.0.0
```

## Quick Start

### 1. Initialize the Extension

```python
from flask import Flask
from translaas import TranslaasOptions
from translaas.extensions.flask import FlaskTranslaas

app = Flask(__name__)

# Configure Translaas
app.config["TRANSLAAS_API_KEY"] = "your-api-key"
app.config["TRANSLAAS_BASE_URL"] = "https://api.translaas.com"
app.config["TRANSLAAS_DEFAULT_LANGUAGE"] = "en"

# Initialize extension
translaas = FlaskTranslaas()
options = TranslaasOptions(
    api_key=app.config["TRANSLAAS_API_KEY"],
    base_url=app.config["TRANSLAAS_BASE_URL"],
    default_language=app.config["TRANSLAAS_DEFAULT_LANGUAGE"],
)
translaas.init_app(app, options)
```

### 2. Use in Views

```python
@app.route("/")
def index():
    # Get translation programmatically
    welcome = translaas.t("common", "welcome")
    greeting = translaas.t("messages", "greeting", parameters={"name": "User"})

    return render_template("index.html", welcome=welcome, greeting=greeting)
```

### 3. Use in Templates

```jinja2
{% filter translaas("common", "welcome") %}{% endfilter %}

<!-- Or with parameters -->
{{ "messages" | translaas("greeting", name="User") }}
```

## Configuration

### Flask Configuration

You can configure Translaas using Flask's `app.config`:

```python
app.config["TRANSLAAS_API_KEY"] = "your-api-key"
app.config["TRANSLAAS_BASE_URL"] = "https://api.translaas.com"
app.config["TRANSLAAS_CACHE_MODE"] = "GROUP"
app.config["TRANSLAAS_TIMEOUT"] = 30.0  # seconds
app.config["TRANSLAAS_DEFAULT_LANGUAGE"] = "en"
```

### Using Configuration Helpers

```python
from translaas.extensions.config import flask_config

# Initialize with Flask config
options = flask_config(app.config)
translaas.init_app(app, options)
```

## Features

### Automatic Language Resolution

The Flask integration automatically detects the user's language from:
- `Accept-Language` header
- `language` cookie
- `lang` query parameter

### Template Filters

Use the `translaas` template filter in Jinja2 templates:

```jinja2
<!-- Simple translation -->
{{ "common" | translaas("welcome") }}

<!-- With parameters -->
{{ "messages" | translaas("greeting", name="John") }}

<!-- With language -->
{{ "common" | translaas("welcome", lang="fr") }}

<!-- With plural -->
{{ "messages" | translaas("item", number=5) }}
```

### Programmatic Usage

Use the `translaas` extension object in your views:

```python
@app.route("/")
def index():
    # Automatic language resolution
    welcome = translaas.t("common", "welcome")

    # Explicit language
    welcome_fr = translaas.t("common", "welcome", lang="fr")

    # With parameters
    greeting = translaas.t("messages", "greeting", parameters={"name": "John"})

    # With plural
    items = translaas.t("messages", "item", number=5)

    return render_template("index.html", welcome=welcome)
```

## API Reference

### FlaskTranslaas

The main extension class for Flask integration.

#### Methods

- `init_app(app, options=None)`: Initialize the extension with a Flask app
- `t(group, entry, lang=None, number=None, parameters=None)`: Get a translation synchronously

### FlaskRequestLanguageProvider

Language provider that extracts language from Flask request objects.

```python
from translaas.extensions.flask import FlaskRequestLanguageProvider

provider = FlaskRequestLanguageProvider(request)
language = await provider.get_language()
```

## Example Application

See `examples/flask/app.py` for a complete example application.
