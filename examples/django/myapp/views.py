"""Django views demonstrating Translaas integration.

This example shows how to use the Translaas SDK with Django, including:
- Helper functions
- Template tags
- Programmatic usage in views
"""

from django.http import JsonResponse
from django.shortcuts import render

from translaas.extensions.django import t


def index(request):
    """Home page demonstrating server-side translation fetching."""
    # Example 1: App Name (nested entry key)
    app_name = t("common", "app.name", request=request, lang="en")

    # Example 2: Welcome Message (basic translation with explicit language)
    welcome = t("common", "welcome", request=request, lang="en")

    # Example 3: Greeting with Parameters
    greeting = t(
        "messages",
        "greeting",
        request=request,
        lang="en",
        parameters={"userName": "Django User", "itemCount": "1"},
    )

    # Example 4: Pluralization
    items = t("messages", "item", request=request, lang="en", number=5.0)

    context = {
        "app_name": app_name,
        "welcome": welcome,
        "greeting": greeting,
        "items": items,
    }
    return render(request, "myapp/index.html", context)


def api_translation(request, group: str, entry: str):
    """API endpoint demonstrating translation retrieval."""
    lang = request.GET.get("lang")
    number_str = request.GET.get("number")
    number = float(number_str) if number_str else None

    # Get parameters from query string
    parameters = {}
    for key, value in request.GET.items():
        if key not in ["lang", "number"]:
            parameters[key] = value

    try:
        if number is not None:
            if lang:
                translation = t(group, entry, request=request, lang=lang, number=number)
            else:
                translation = t(group, entry, request=request, number=number)
        elif parameters:
            if lang:
                translation = t(group, entry, request=request, lang=lang, parameters=parameters)
            else:
                translation = t(group, entry, request=request, parameters=parameters)
        elif lang:
            translation = t(group, entry, request=request, lang=lang)
        else:
            translation = t(group, entry, request=request)

        return JsonResponse(
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
        return JsonResponse({"error": str(e)}, status=500)
