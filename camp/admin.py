from django.contrib import admin
from camp.models import RecreationArea, Facility, RecAreaFacilityLink, Campsite

admin.site.register(RecreationArea)
admin.site.register(Facility)
admin.site.register(RecAreaFacilityLink)
admin.site.register(Campsite)
