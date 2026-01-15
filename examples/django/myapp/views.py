"""Django views demonstrating Translaas integration.

This example shows how to use the Translaas SDK with Django, including:
- Helper functions
- Template tags
- Programmatic usage in views
"""

from django.shortcuts import render

from translaas.extensions.django import t


def index(request):
    """Home page demonstrating programmatic usage."""
    # Get translations programmatically
    welcome = t("common", "welcome", request=request)
    greeting = t("messages", "greeting", request=request, parameters={"name": "Django User"})

    context = {
        "welcome": welcome,
        "greeting": greeting,
    }
    return render(request, "myapp/index.html", context)


def about(request):
    """About page demonstrating template tag usage."""
    # Template will use {% translaas %} tag
    return render(request, "myapp/about.html")
