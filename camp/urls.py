from django.urls import path

from . import views

urlpatterns = [
    path("", views.select_camp, name="select_camp"),
]