"""Django template tags for Translaas translations.

This module provides template tags for using Translaas translations in Django templates.

Example:
    ```django
    {% load translaas_tags %}

    <h1>{% translaas "common" "welcome" %}</h1>
    <p>{% translaas "messages" "greeting" name="John" %}</p>
    ```
"""

from django import template

from translaas.extensions.django import t

register = template.Library()


@register.simple_tag(takes_context=True)  # type: ignore[misc]
def translaas(
    context: dict,
    group: str,
    entry: str,
    lang: str = None,
    number: float = None,
    **kwargs: str,
) -> str:
    """Template tag for Translaas translations.

    This tag retrieves a translation from Translaas and can be used in Django templates.

    Args:
        context: The template context (automatically provided by Django).
        group: The translation group name.
        entry: The translation entry key.
        lang: Optional explicit language code.
        number: Optional number for plural form selection.
        **kwargs: Optional parameters for string interpolation.

    Returns:
        The translated string.

    Example:
        ```django
        {% load translaas_tags %}

        <!-- Simple translation -->
        <h1>{% translaas "common" "welcome" %}</h1>

        <!-- With language -->
        <h1>{% translaas "common" "welcome" lang="fr" %}</h1>

        <!-- With parameters -->
        <p>{% translaas "messages" "greeting" name="John" %}</p>

        <!-- With plural -->
        <p>{% translaas "messages" "item" number=5 %}</p>
        ```
    """
    # Get request from context if available
    request = context.get("request") if context else None

    parameters = kwargs if kwargs else None

    return t(group, entry, request=request, lang=lang, number=number, parameters=parameters)
