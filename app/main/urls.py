"""wahltraud URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
import os
from django.conf.urls import url, include
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views.generic.base import RedirectView
from .settings import DEBUG

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^fb/', include('bot.urls')),
    url(r'^tz_detect/', include('tz_detect.urls')),
    url(r'metrics/', include('metrics.urls')),
]

if not DEBUG:
    urlpatterns.append(url(r'^$', RedirectView.as_view(url='https://m.me/sportsfreund.sportschau', permanent=False)))
