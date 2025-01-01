from django.urls import path

from .views import select_camp, show_parks, show_campsites

urlpatterns = [
    path('select-camp/', select_camp, name='select_camp'),
    path('show-parks/', show_parks, name='show_parks'),
    path('show-campsites/', show_campsites, name='show_campsites'),
]
