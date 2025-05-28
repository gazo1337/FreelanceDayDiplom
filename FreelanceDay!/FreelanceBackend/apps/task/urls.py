from django.urls import path, re_path, include
from apps.task import views
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="Task API",
        default_version='v1',
        description="API подсистемы \"Система задач\" сервиса FreelanceDay!",
    ),
    patterns=[
        path('task/', include('apps.task.urls')),
    ],
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('createTask/', views.create_task),
    path('pushTask/', views.push_task),
    path('getTasks/', views.get_tasks),
    path('task/', views.task),
    path('vote/', views.vote),
    path('ifVote/', views.ifVote),
    path('getExTask/', views.get_ex_tasks),
    path('getEmpTask/', views.get_emp_tasks),
    path('getVotes/', views.getVotes),
    path('setExecutor/', views.setExecutor),
]