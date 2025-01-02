from django.urls import path

from .views import select_camp, show_parks, show_campsites, show_facilities, show_campsites

urlpatterns = [
    path('camp/', select_camp, name='select_camp'),
    path('parks/', show_parks, name='show_parks'),
    path('parks/<str:recarea_id>/facilities/',
         show_facilities, name='show_facilities'),
    path('campsites/<str:facility_id>/', show_campsites, name='show_campsites'),

]
