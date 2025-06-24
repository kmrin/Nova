from django.urls import path, include

urlpatterns = [
    path("ui/", include("apps.web.urls")),
    path("api/v1/", include("apps.bot.urls")),
]