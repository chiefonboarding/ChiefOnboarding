from django.urls import path, include
from rest_framework import routers
from users import views

router = routers.DefaultRouter(trailing_slash=False)
router.register('new_hire', views.NewHireViewSet, 'new_hire')
router.register('admin', views.AdminViewSet, 'admin')
router.register('employee', views.EmployeeViewSet, 'employee')

urlpatterns = [
    path('to_do/<int:id>', views.ToDoUserView.as_view()),
    path('resource/<int:id>', views.ResourceUserView.as_view()),
    path('', include(router.urls)),
]