"""Flask example application demonstrating Translaas integration.

This example shows how to use the Translaas SDK with Flask, including:
- Extension initialization
- Template filters
- Programmatic usage in views
"""

import os

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template_string, request

from translaas import TranslaasOptions
from translaas.extensions.flask import FlaskTranslaas

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Configure Translaas from environment variables
app.config["TRANSLAAS_API_KEY"] = os.getenv("TRANSLAAS_API_KEY", "your-api-key-here")
app.config["TRANSLAAS_BASE_URL"] = os.getenv("TRANSLAAS_BASE_URL", "https://api.translaas.com")
app.config["TRANSLAAS_DEFAULT_LANGUAGE"] = os.getenv("TRANSLAAS_DEFAULT_LANGUAGE", "en")

# Initialize Translaas extension
translaas = FlaskTranslaas()
options = TranslaasOptions(
    api_key=app.config["TRANSLAAS_API_KEY"],
    base_url=app.config["TRANSLAAS_BASE_URL"],
    default_language=app.config["TRANSLAAS_DEFAULT_LANGUAGE"],
    verify=os.getenv("TRANSLAAS_VERIFY", "true").lower() == "true",
)
translaas.init_app(app, options)


@app.route("/")
def index():
    """Home page demonstrating various translation examples."""
    # Example 1: App Name (nested entry key)
    app_name = translaas.t("common", "app.name", lang="en")

    # Example 2: Welcome Message (basic translation with explicit language)
    welcome = translaas.t("common", "welcome", lang="en")

    # Example 3: Greeting with Parameters
    greeting = translaas.t(
        "messages", "greeting", lang="en", parameters={"userName": "Flask User", "itemCount": "1"}
    )

    # Example 4: Pluralization
    items = translaas.t("messages", "item", lang="en", number=5.0)

    template_str = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>🌐 Translaas Flask Example</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
            .example { background: #f5f5f5; padding: 15px; margin: 20px 0; border-radius: 5px; }
            .example h2 { margin-top: 0; }
            code { background: #e9ecef; padding: 2px 6px; border-radius: 3px; }
        </style>
    </head>
    <body>
        <h1>🌐 Translaas Flask Example</h1>
        <p>This page demonstrates server-side translation fetching.</p>

        <div class="example">
            <h2>App Name</h2>
            <p><strong>Translation:</strong> {{ app_name }}</p>
            <code>translaas.t("common", "app.name", lang="en")</code>
        </div>

        <div class="example">
            <h2>Welcome Message</h2>
            <p><strong>Translation:</strong> {{ welcome }}</p>
            <code>translaas.t("common", "welcome", lang="en")</code>
        </div>

        <div class="example">
            <h2>Greeting with Parameters</h2>
            <p><strong>Translation:</strong> {{ greeting }}</p>
            <code>translaas.t("messages", "greeting", lang="en", parameters={"userName": "Flask User", "itemCount": "1"})</code>
        </div>

        <div class="example">
            <h2>Pluralization</h2>
            <p><strong>Translation:</strong> {{ items }}</p>
            <code>translaas.t("messages", "item", lang="en", number=5)</code>
        </div>

    </body>
    </html>
    """
    return render_template_string(
        template_str,
        app_name=app_name,
        welcome=welcome,
        greeting=greeting,
        items=items,
    )


@app.route("/api/translations/<group>/<entry>")
def api_translation(group: str, entry: str):
    """API endpoint demonstrating translation retrieval."""

    lang = request.args.get("lang")
    number_str = request.args.get("number")
    number = float(number_str) if number_str else None

    # Get parameters from query string
    parameters = {}
    for key, value in request.args.items():
        if key not in ["lang", "number"]:
            parameters[key] = value

    try:
        if number is not None:
            if lang:
                translation = translaas.t(group, entry, lang=lang, number=number)
            else:
                translation = translaas.t(group, entry, number=number)
        elif parameters:
            if lang:
                translation = translaas.t(group, entry, lang=lang, parameters=parameters)
            else:
                translation = translaas.t(group, entry, parameters=parameters)
        elif lang:
            translation = translaas.t(group, entry, lang=lang)
        else:
            translation = translaas.t(group, entry)

        return jsonify(
            {
                "group": group,
                "entry": entry,
                "language": lang or "auto",
                "translation": translation,
                "number": number,
                "parameters": parameters if parameters else None,
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
