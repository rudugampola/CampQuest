from django.core.management.base import BaseCommand
from camp.models import RecreationArea, Facility, RecAreaFacilityLink


class Command(BaseCommand):
    help = 'Clear all imported records from the database'

    def handle(self, *args, **kwargs):
        try:
            # Delete all records
            RecreationArea.objects.all().delete()
            Facility.objects.all().delete()
            RecAreaFacilityLink.objects.all().delete()

            self.stdout.write(self.style.SUCCESS(
                "All imported records have been cleared."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An error occurred: {e}"))
