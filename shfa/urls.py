"""SHFA URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
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
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls.static import static
from django.conf import settings
from rest_framework import routers

admin.site.index_title = _('admin.site.index_title')
admin.site.site_header = _('admin.site.site_header')
admin.site.site_title = _('admin.site.site_title')

router = routers.DefaultRouter()

urlpatterns = [
    path("i18n/", include("django.conf.urls.i18n")),
]

apps = [path('', include(f"apps.{app['name']}.urls")) for app in settings.APPS_LOCAL]

urlpatterns += i18n_patterns(
    path('admin/', admin.site.urls), 
    path('api/', include("apps.shfa.urls")),
    path('api/geography', include("apps.geography.urls")),
    *apps,
    prefix_default_language=False
)
urlpatterns += staticfiles_urlpatterns()
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)