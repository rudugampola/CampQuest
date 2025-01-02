import json
from django.core.management.base import BaseCommand
from camp.models import RecreationArea, Facility, RecAreaFacilityLink, Campsite


class Command(BaseCommand):
    help = 'Import JSON files into the database'

    def handle(self, *args, **kwargs):
        try:
            # # Load Recreation Areas
            with open('camp/other/RecAreas_API_v1.json', encoding='utf-8') as file:
                data = json.load(file)
                for item in data['RECDATA']:
                    RecreationArea.objects.create(
                        rec_area_id=item['RecAreaID'],
                        org_rec_area_id=item.get('OrgRecAreaID', ''),
                        parent_org_id=item.get('ParentOrgID', ''),
                        name=item['RecAreaName'],
                        description=item.get('RecAreaDescription', ''),
                        phone=item.get('RecAreaPhone', ''),
                        email=item.get('RecAreaEmail', ''),
                        reservation_url=item.get('RecAreaReservationURL', ''),
                        map_url=item.get('RecAreaMapURL', ''),
                        longitude=item['RecAreaLongitude'],
                        latitude=item['RecAreaLatitude'],
                        enabled=item['Enabled'],
                        last_updated_date=item['LastUpdatedDate']
                    )
                self.stdout.write(self.style.SUCCESS(
                    "Recreation data imported successfully."))

            # Load Facilities and link to Recreation Areas
            with open('camp/other/Facilities_API_v1.json', encoding='utf-8') as file:
                data = json.load(file)
                for item in data['RECDATA']:
                    try:
                        rec_area = RecreationArea.objects.get(
                            rec_area_id=item['ParentRecAreaID'])
                        Facility.objects.create(
                            facility_id=item['FacilityID'],
                            parent_rec_area=rec_area,
                            name=item['FacilityName'],
                            description=item.get('FacilityDescription', ''),
                            type_description=item.get(
                                'FacilityTypeDescription', ''),
                            longitude=item['FacilityLongitude'],
                            latitude=item['FacilityLatitude'],
                            reservable=item['Reservable'],
                            enabled=item['Enabled'],
                            last_updated_date=item['LastUpdatedDate'],
                            parent_org_id=item.get('ParentOrgID', '')
                        )
                    except RecreationArea.DoesNotExist:
                        self.stdout.write(self.style.WARNING(
                            f"RecreationArea with rec_area_id {item['ParentRecAreaID']} does not exist. Skipping facility {item['FacilityID']}."))
                self.stdout.write(self.style.SUCCESS(
                    "Facilities data imported successfully."))

            # Link RecAreas and Facilities
            with open('camp/other/RecAreaFacilities_API_v1.json', encoding='utf-8') as file:
                data = json.load(file)
                for item in data['RECDATA']:
                    rec_area_id_value = item['RecAreaID']
                    facility_id_value = item['FacilityID']
                    try:
                        rec_area = RecreationArea.objects.get(
                            rec_area_id=rec_area_id_value)
                        facility = Facility.objects.get(
                            facility_id=facility_id_value)
                        RecAreaFacilityLink.objects.create(
                            rec_area_id=rec_area, facility_id=facility)
                        self.stdout.write(self.style.SUCCESS(
                            f"Linked RecArea {rec_area_id_value} with Facility {facility_id_value}"))
                    except RecreationArea.DoesNotExist:
                        self.stdout.write(self.style.WARNING(
                            f"RecreationArea with rec_area_id {rec_area_id_value} does not exist. Skipping entry."))
                    except Facility.DoesNotExist:
                        self.stdout.write(self.style.WARNING(
                            f"Facility with facility_id {facility_id_value} does not exist. Skipping entry."))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(
                            f"An error occurred while linking rec_area_id {rec_area_id_value} and facility_id {facility_id_value}: {e}"))

                self.stdout.write(self.style.SUCCESS(
                    "RecAreas and Facilities data imported successfully."))

            # Load Campsites and link to Facilities
            with open('camp/other/Campsites_API_v1.json', encoding='utf-8') as file:
                data = json.load(file)
                for item in data['RECDATA']:
                    try:
                        facility = Facility.objects.get(
                            facility_id=item['FacilityID'])
                        Campsite.objects.create(
                            campsite_id=item['CampsiteID'],
                            facility=facility,
                            name=item['CampsiteName'],
                            campsite_type=item['CampsiteType'],
                            type_of_use=item['TypeOfUse'],
                            loop=item.get('Loop', ''),
                            accessible=item['CampsiteAccessible'],
                            longitude=item['CampsiteLongitude'],
                            latitude=item['CampsiteLatitude'],
                            created_date=item['CreatedDate'],
                            last_updated_date=item['LastUpdatedDate']
                        )
                        self.stdout.write(self.style.SUCCESS(
                            f"Imported Campsite {item['CampsiteID']} linked to Facility {item['FacilityID']}"))
                    except Facility.DoesNotExist:
                        self.stdout.write(self.style.WARNING(
                            f"Facility with facility_id {item['FacilityID']} does not exist. Skipping campsite {item['CampsiteID']}."))
                self.stdout.write(self.style.SUCCESS(
                    "Campsites data imported successfully."))

            self.stdout.write(self.style.SUCCESS(
                "JSON data imported successfully."))
        except UnicodeDecodeError as e:
            self.stdout.write(self.style.ERROR(f"UnicodeDecodeError: {e}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An error occurred: {e}"))
