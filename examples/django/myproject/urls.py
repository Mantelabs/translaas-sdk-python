"""URL configuration for myproject."""

from django.urls import include, path

urlpatterns = [
    path("", include("myapp.urls")),
]
