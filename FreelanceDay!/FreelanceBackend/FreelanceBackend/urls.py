"""
URL configuration for FreelanceBackend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from django.urls import path, re_path, include
from newApp import views
import apps


taskpatterns = [
    path('', views.tasks),
    path('task/', views.task),
]

errorpatterns = [
    path("notThis/", views.notThis),
    path("andNotThis/", views.andNotThis),
]

urlpatterns = [
    path('admin/', admin.site.urls),
    path('administration/', include('apps.administration.urls')),
    path('task/', include('apps.task.urls')),
    path('adminPayment/', include('apps.adminPayment.urls')),
]
