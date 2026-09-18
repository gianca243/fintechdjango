from django.urls import path
from rest_framework.routers import DefaultRouter
from fintech.views.user import UserView


urlpatterns = [
    path("user/", UserView.as_view()),
    path("user/<int:id>/", UserView.as_view())
]