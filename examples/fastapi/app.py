"""FastAPI example application demonstrating Translaas integration.

This example shows how to use the Translaas SDK with FastAPI, including:
- Extension initialization
- Dependency injection
- Async usage in route handlers
"""

import os

from dotenv import load_dotenv
from fastapi import Depends, FastAPI
from fastapi.responses import HTMLResponse

from translaas import TranslaasOptions
from translaas.extensions.fastapi import FastAPITranslaas, get_translaas_service
from translaas.service import TranslaasService

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

# Configure Translaas from environment variables
options = TranslaasOptions(
    api_key=os.getenv("TRANSLAAS_API_KEY", "your-api-key-here"),
    base_url=os.getenv("TRANSLAAS_BASE_URL", "https://api.translaas.com"),
    default_language=os.getenv("TRANSLAAS_DEFAULT_LANGUAGE", "en"),
    verify=os.getenv("TRANSLAAS_VERIFY", "true").lower() == "true",
)

# Initialize Translaas extension
translaas = FastAPITranslaas()
translaas.init_app(app, options)


@app.get("/", response_class=HTMLResponse)
async def index(service: TranslaasService = Depends(get_translaas_service)):
    """Home page demonstrating server-side translation fetching."""
    # Example 1: App Name (nested entry key)
    app_name = await service.t("common", "app.name", "en")

    # Example 2: Welcome Message (basic translation with explicit language)
    welcome = await service.t("common", "welcome", "en")

    # Example 3: Greeting with Parameters
    greeting = await service.t(
        "messages", "greeting", "en", {"userName": "FastAPI User", "itemCount": "1"}
    )

    # Example 4: Pluralization
    items = await service.t("messages", "item", "en", 5.0)

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>🌐 Translaas FastAPI Example</title>
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }}
            .example {{ background: #f5f5f5; padding: 15px; margin: 20px 0; border-radius: 5px; }}
            .example h2 {{ margin-top: 0; }}
            code {{ background: #e9ecef; padding: 2px 6px; border-radius: 3px; }}
        </style>
    </head>
    <body>
        <h1>🌐 Translaas FastAPI Example</h1>
        <p>This page is server-side rendered with translations.</p>

        <div class="example">
            <h2>App Name</h2>
            <p><strong>Translation:</strong> {app_name}</p>
            <code>await service.t("common", "app.name", "en")</code>
        </div>

        <div class="example">
            <h2>Welcome Message</h2>
            <p><strong>Translation:</strong> {welcome}</p>
            <code>await service.t("common", "welcome", "en")</code>
        </div>

        <div class="example">
            <h2>Greeting with Parameters</h2>
            <p><strong>Translation:</strong> {greeting}</p>
            <code>await service.t("messages", "greeting", "en", undefined, {{"{{"}} userName: "FastAPI User", itemCount: "1" {{"}}"}})</code>
        </div>

        <div class="example">
            <h2>Pluralization</h2>
            <p><strong>Translation:</strong> {items}</p>
            <code>await service.t("messages", "item", "en", 5)</code>
        </div>

    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.get("/api/translations/{group}/{entry}")
async def get_translation(
    group: str,
    entry: str,
    lang: str = None,
    number: float = None,
    service: TranslaasService = Depends(get_translaas_service),
):
    """API endpoint demonstrating translation retrieval."""
    from fastapi import Query
    from typing import Dict

    # Get parameters from query string
    parameters: Dict[str, str] = {}
    # Note: FastAPI doesn't easily support arbitrary query params, so we'd need to use request.query_params
    # For simplicity, this example focuses on lang and number

    try:
        if number is not None:
            if lang:
                translation = await service.t(group, entry, lang, number)
            else:
                translation = await service.t(group, entry, number)
        elif lang:
            translation = await service.t(group, entry, lang)
        else:
            translation = await service.t(group, entry)

        return {
            "group": group,
            "entry": entry,
            "language": lang or "auto",
            "translation": translation,
            "number": number,
        }
    except Exception as e:
        from fastapi import HTTPException

        raise HTTPException(status_code=500, detail=str(e)) from e


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
