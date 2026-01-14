"""Framework integrations and extensions for the Translaas SDK."""

from translaas.extensions.django import DjangoRequestLanguageProvider
from translaas.extensions.fastapi import FastAPIRequestLanguageProvider
from translaas.extensions.flask import FlaskRequestLanguageProvider

__all__ = [
    "FlaskRequestLanguageProvider",
    "FastAPIRequestLanguageProvider",
    "DjangoRequestLanguageProvider",
]
