"""Flask example application demonstrating Translaas integration.

This example shows how to use the Translaas SDK with Flask, including:
- Extension initialization
- Template filters
- Programmatic usage in views
"""

from flask import Flask, render_template_string

from translaas import TranslaasOptions
from translaas.extensions.flask import FlaskTranslaas

app = Flask(__name__)

# Configure Translaas
app.config["TRANSLAAS_API_KEY"] = "your-api-key-here"
app.config["TRANSLAAS_BASE_URL"] = "https://api.translaas.com"
app.config["TRANSLAAS_DEFAULT_LANGUAGE"] = "en"

# Initialize Translaas extension
translaas = FlaskTranslaas()
options = TranslaasOptions(
    api_key=app.config["TRANSLAAS_API_KEY"],
    base_url=app.config["TRANSLAAS_BASE_URL"],
    default_language=app.config["TRANSLAAS_DEFAULT_LANGUAGE"],
)
translaas.init_app(app, options)


@app.route("/")
def index():
    """Home page demonstrating programmatic usage."""
    # Get translation programmatically
    welcome = translaas.t("common", "welcome")
    greeting = translaas.t("messages", "greeting", parameters={"name": "Flask User"})

    # Render template with translations
    template_str = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>{{ welcome }}</title>
    </head>
    <body>
        <h1>{{ welcome }}</h1>
        <p>{{ greeting }}</p>
        <hr>
        <h2>Template Filter Example:</h2>
        <p>{{ "common" | translaas("welcome") }}</p>
        <p>{{ "messages" | translaas("greeting", name="Template User") }}</p>
    </body>
    </html>
    """
    return render_template_string(template_str, welcome=welcome, greeting=greeting)


@app.route("/about")
def about():
    """About page demonstrating template filter usage."""
    template_str = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>About</title>
    </head>
    <body>
        <h1>{% translaas "common" "about" %}</h1>
        <p>{% translaas "common" "description" %}</p>
    </body>
    </html>
    """
    return render_template_string(template_str)


if __name__ == "__main__":
    app.run(debug=True)
