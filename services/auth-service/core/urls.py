"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import include, path
from core.metrics import metrics_view

urlpatterns = [
    path("metrics", metrics_view, name="metrics"),
    path("admin/", admin.site.urls),
    path("", include("users.urls")),
]

handler400 = "core.error_handlers.bad_request"
handler403 = "core.error_handlers.permission_denied"
handler404 = "core.error_handlers.page_not_found"
handler500 = "core.error_handlers.server_error"
