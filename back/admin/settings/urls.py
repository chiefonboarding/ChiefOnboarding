from django.urls import path

from . import views

app_name = 'settings'
urlpatterns = [
    path('general/', views.OrganizationGeneralUpdateView.as_view(), name="general"),
    path('personal/', views.PersonalLanguageUpdateView.as_view(), name="personal-language"),
    path('welcome_message/<slug:language>/<int:type>/', views.WelcomeMessageUpdateView.as_view(), name="welcome-message"),
    path('administrators/', views.AdministratorListView.as_view(), name="administrators"),
    path('administrators/create/', views.AdministratorCreateView.as_view(), name="administrators-create"),
    path('administrators/delete/<int:pk>/', views.AdministratorDeleteView.as_view(), name="administrators-delete"),
]
