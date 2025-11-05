"""
URL configuration for fleet_management project.

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
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from inventory.error_handlers import (
    custom_400_handler,
    custom_403_handler,
    custom_404_handler,
    custom_500_handler
)

urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('', include('inventory.urls')),
]

# Serve static files in development (media files are now served securely through views)
if settings.DEBUG:
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    urlpatterns += staticfiles_urlpatterns()
    # Also serve from STATICFILES_DIRS for development
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0] if settings.STATICFILES_DIRS else settings.STATIC_ROOT)

# Custom error handlers
handler400 = custom_400_handler
handler403 = custom_403_handler
handler404 = custom_404_handler
handler500 = custom_500_handler
