from django.urls import (
    path,
    include,
)
from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedSimpleRouter
from project import views

router = DefaultRouter()
router.register(r'projects', views.ProjectViewSet, basename='project')

projects_router = NestedSimpleRouter(router, r'projects', lookup='project')
projects_router.register(
    r'documents',
    views.DocumentViewSet,
    basename='project-documents'
)

app_name = 'project'

urlpatterns = [
    path('', include(router.urls)),
    path('', include(projects_router.urls))
]