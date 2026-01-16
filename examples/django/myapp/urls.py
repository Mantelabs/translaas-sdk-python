"""URL configuration for myapp."""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path(
        "api/translations/<str:group>/<str:entry>/", views.api_translation, name="api_translation"
    ),
]
