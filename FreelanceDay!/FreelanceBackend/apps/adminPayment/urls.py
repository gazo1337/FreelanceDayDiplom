from django.urls import path, re_path, include
from apps.adminPayment import views
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

schema_view = get_schema_view(
    openapi.Info(
        title="Administration Payment API",
        default_version='v1',
        description="API подсистемы \"Администрация платежей\" сервиса FreelanceDay!",
    ),
     patterns=[
        path('adminPayment/', include('apps.adminPayment.urls')),
    ],
    public=True,
    permission_classes=(permissions.AllowAny,),
)


urlpatterns = [
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('createCard/', views.create_card),
    path('getBalance/', views.getBalance),
    path('payment/toEmployer/', views.toEmloyer),
    path('payment/toTask/', views.toTask),
    path('payment/toExecutor/', views.toExecutor),
    path('payment/fromExecutor/', views.fromExecutor),
    path('payment/getOperations/', views.getOperations),
]