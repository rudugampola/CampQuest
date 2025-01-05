from django.shortcuts import render
from datetime import datetime
from camp.camping import run_campsite_check
from django.http import JsonResponse
from camp.models import RecreationArea, Facility, RecAreaFacilityLink, Campsite

# Utility to convert model instances to dictionaries for easier use in templates


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def recarea_to_dict(recarea):
    return {
        'id': recarea.rec_area_id,
        'name': recarea.name,
        'latitude': recarea.latitude,
        'longitude': recarea.longitude
    }


def facility_to_dict(facility):
    return {
        'id': facility.facility_id,
        'name': facility.name,
        'type': facility.type_description,
        'latitude': facility.latitude,
        'longitude': facility.longitude
    }


def select_camp(request):
    if request.method == "POST":
        # Process the form data
        start_date_str = request.POST.get("start_date")
        end_date_str = request.POST.get("end_date")

        # The parks has comma-separated values, so we need to split them into a list of strings
        parks = request.POST.get("parks").strip().split(',')

        # The dates are in the format "YYYY-MM-DD", so we can parse them into datetime objects
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d")

        # Get the Show Campsite Info checkbox value
        show_campsite_info = request.POST.get("show_campsite_info") == "true"

        # Get the Weekends Only checkbox value
        weekends_only = request.POST.get("weekends_only") == "true"

        # Pass the 'show_campsite_info' value as "true" if checked
        if show_campsite_info:
            output, has_availabilities, raw_campsite_info = run_campsite_check(
                parks,
                start_date,
                end_date,
                show_campsite_info=show_campsite_info,
                weekends_only=weekends_only
            )

            # Convert raw_campsite_info to a list of dictionaries for easier iteration in the template
            campsite_info = []
            for park_id, park_info in raw_campsite_info.items():
                park_data = {
                    'park_id': park_id,
                    'available_sites': park_info[0],
                    'total_sites': park_info[1],
                    'sites': [],
                    'park_name': park_info[3]
                }
                for site_id, dates in park_info[2].items():
                    site_data = {
                        'site_id': site_id,
                        'dates': dates
                    }
                    park_data['sites'].append(site_data)
                campsite_info.append(park_data)
        else:
            output, has_availabilities = run_campsite_check(
                parks,
                start_date,
                end_date,
                show_campsite_info=show_campsite_info,
                weekends_only=weekends_only
            )
            campsite_info = None

        # Create a context dictionary with the form data and the results
        context = {
            'start_date': start_date_str,
            'end_date': end_date_str,
            'parks': parks,
            'output': output,
            'has_availabilities': has_availabilities,
            'show_campsite_info': show_campsite_info,
            'campsite_info': campsite_info,  # Include detailed campsite info
            'weekends_only': weekends_only,
            'title': 'Camp Reservation Result'
        }

        # Print the output
        print(bcolors.OKGREEN + "Output: " + output + bcolors.ENDC)

        # Return the rendered template with the context data
        return render(request, 'camp/camp_result.html', context)

    # Render the select_camp.html template
    return render(request, 'camp/select_camp.html', {'title': 'Select Camp'})


def show_parks(request):
    search_query = request.GET.get('q', '').lower()
    recareas = RecreationArea.objects.filter(name__icontains=search_query)

    parks = [recarea_to_dict(recarea) for recarea in recareas]

    # Sort parks by name
    parks = sorted(parks, key=lambda x: x['name'].lower())

    return render(request, 'camp/show_parks.html', {'parks': parks, 'search_query': search_query, 'title': 'Parks'})


def show_facilities(request, recarea_id):
    try:
        recarea = RecreationArea.objects.get(pk=recarea_id)
        facilities = recarea.facilities.all()

        facility_details = [facility_to_dict(
            facility) for facility in facilities]

        # Sort facilities to show "Campground" type first
        facility_details = sorted(facility_details, key=lambda x: (
            x['type'] != "Campground", x['name']))

        return render(request, 'camp/show_facilities.html', {'facilities': facility_details, 'recarea_id': recarea_id, 'title': 'Facilities'})
    except RecreationArea.DoesNotExist:
        return JsonResponse({'error': 'RecreationArea not found'}, status=404)


def show_campsites(request, facility_id):
    try:
        # Fetch the facility object using the facility_id
        facility = Facility.objects.get(facility_id=facility_id)

        # Filter campsites that belong to the specified facility
        campsites = Campsite.objects.filter(facility=facility)

        # Convert campsite objects to dictionaries for easier iteration in the template
        campsite_details = [
            {
                'id': campsite.campsite_id,
                'name': campsite.name,
                'loop': campsite.loop,
                'facility_id': campsite.facility.facility_id,
                'type_of_use': campsite.type_of_use,
                'accessible': campsite.accessible,
                'longitude': campsite.longitude,
                'latitude': campsite.latitude
            }
            for campsite in campsites
        ]

        return render(request, 'camp/show_campsites.html', {'campsites': campsite_details, 'title': 'Campsites'})

    except Facility.DoesNotExist:
        return JsonResponse({'error': 'Facility not found'}, status=404)
    except Campsite.DoesNotExist:
        return JsonResponse({'error': 'Campsite not found'}, status=404)
