"""FastAPI example application demonstrating Translaas integration.

This example shows how to use the Translaas SDK with FastAPI, including:
- Extension initialization
- Dependency injection
- Async usage in route handlers
"""

from fastapi import Depends, FastAPI
from fastapi.responses import HTMLResponse

from translaas import TranslaasOptions
from translaas.extensions.fastapi import FastAPITranslaas, get_translaas_service
from translaas.service import TranslaasService

app = FastAPI()

# Configure Translaas
options = TranslaasOptions(
    api_key="your-api-key-here",
    base_url="https://api.translaas.com",
    default_language="en",
)

# Initialize Translaas extension
translaas = FastAPITranslaas()
translaas.init_app(app, options)


@app.get("/", response_class=HTMLResponse)
async def index(service: TranslaasService = Depends(get_translaas_service)):
    """Home page demonstrating dependency injection."""
    # Get translations using injected service
    welcome = await service.t("common", "welcome")
    greeting = await service.t("messages", "greeting", parameters={"name": "FastAPI User"})

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{welcome}</title>
    </head>
    <body>
        <h1>{welcome}</h1>
        <p>{greeting}</p>
        <hr>
        <h2>Dependency Injection Example</h2>
        <p>This page uses FastAPI dependency injection to get TranslaasService.</p>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.get("/about", response_class=HTMLResponse)
async def about(service: TranslaasService = Depends(get_translaas_service)):
    """About page demonstrating automatic language resolution."""
    about_text = await service.t("common", "about")
    description = await service.t("common", "description")

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{about_text}</title>
    </head>
    <body>
        <h1>{about_text}</h1>
        <p>{description}</p>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.get("/api/translations/{group}/{entry}")
async def get_translation(
    group: str,
    entry: str,
    lang: str = None,
    service: TranslaasService = Depends(get_translaas_service),
):
    """API endpoint demonstrating translation retrieval."""
    if lang:
        translation = await service.t(group, entry, lang)
    else:
        translation = await service.t(group, entry)

    return {
        "group": group,
        "entry": entry,
        "language": lang or "auto",
        "translation": translation,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
