"""apps/companies/urls.py"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CompanyViewSet, BranchViewSet, DepartmentViewSet, JobGradeViewSet

router = DefaultRouter()
router.register(r'branches', BranchViewSet, basename='branches')
router.register(r'departments', DepartmentViewSet, basename='departments')
router.register(r'job-grades', JobGradeViewSet, basename='job-grades')
router.register(r'', CompanyViewSet, basename='companies')

urlpatterns = [path('', include(router.urls))]
