from django.db import models


class RecreationArea(models.Model):
    rec_area_id = models.CharField(max_length=100, primary_key=True)
    org_rec_area_id = models.CharField(max_length=100, blank=True, null=True)
    parent_org_id = models.CharField(max_length=100, blank=True, null=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    reservation_url = models.URLField(blank=True, null=True)
    map_url = models.URLField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    enabled = models.BooleanField(default=True)
    last_updated_date = models.DateField()


class Facility(models.Model):
    facility_id = models.CharField(max_length=100, primary_key=True)
    parent_org_id = models.CharField(max_length=100, blank=True, null=True)
    parent_rec_area = models.ForeignKey(
        RecreationArea,
        on_delete=models.SET_NULL,
        null=True,
        related_name="facilities"
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    type_description = models.CharField(max_length=100, blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    reservable = models.BooleanField(default=False)
    enabled = models.BooleanField(default=True)
    last_updated_date = models.DateField()


class RecAreaFacilityLink(models.Model):
    rec_area_id = models.ForeignKey(RecreationArea, on_delete=models.CASCADE)
    facility_id = models.ForeignKey(Facility, on_delete=models.CASCADE)


class Campsite(models.Model):
    campsite_id = models.CharField(max_length=100, primary_key=True)
    facility = models.ForeignKey(
        Facility, on_delete=models.CASCADE, related_name='campsites')
    name = models.CharField(max_length=255)
    campsite_type = models.CharField(max_length=100)
    type_of_use = models.CharField(max_length=100)
    loop = models.CharField(max_length=100, blank=True, null=True)
    accessible = models.BooleanField(default=False)
    longitude = models.FloatField(blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    created_date = models.DateField()
    last_updated_date = models.DateField()
