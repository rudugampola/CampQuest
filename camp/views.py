from django.shortcuts import render
from datetime import datetime
from .camping import run_campsite_check
import json
from django.http import JsonResponse
from django.conf import settings
import os

# TODO: Add a rating for the campsite


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

# Utility to load JSON data from a file


def load_json(file_name):
    file_path = os.path.join(settings.BASE_DIR, 'camp', 'other', file_name)
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)


# Load JSON data once
recareas_data = load_json('RecAreas_API_v1.json')["RECDATA"]
recareas_facilities_data = load_json(
    'RecAreaFacilities_API_v1.json')["RECDATA"]
facilities_data = load_json('Facilities_API_v1.json')["RECDATA"]
campsite_data = load_json('Campsites_API_v1.json')["RECDATA"]


def select_camp(request):
    if request.method == "POST":
        # Process the form data
        start_date_str = request.POST.get("start_date")
        end_date_str = request.POST.get("end_date")

        # The parks has comma-separated values, so we need to split them into a list of strings
        parks = request.POST.get("parks").strip().split(',')

        # nights = request.POST.get("nights")

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
                # nights=int(nights),
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
                # nights=int(nights),
                show_campsite_info=show_campsite_info,
                weekends_only=weekends_only
            )
            campsite_info = None

        # Create a context dictionary with the form data and the results
        context = {
            'start_date': start_date_str,
            'end_date': end_date_str,
            'parks': parks,
            # 'nights': nights,
            'output': output,
            'has_availabilities': has_availabilities,
            'show_campsite_info': show_campsite_info,
            'campsite_info': campsite_info,  # Include detailed campsite info
            'weekends_only': weekends_only,
            'title': 'Camp Reservation Result'
        }

        # Print the output
        print(bcolors.OKGREEN + "Output: " + output + bcolors.ENDC)
        # Print the campsite_info
        # print(campsite_info)

        # Return the rendered template with the context data
        return render(request, 'camp/camp_result.html', context)

    # Render the select_camp.html template
    return render(request, 'camp/select_camp.html', {'title': 'Select Camp'})


def show_parks(request):
    search_query = request.GET.get('q', '').lower()
    parks = [
        {
            'id': park.get('RecAreaID', 'N/A'),
            'name': park.get('RecAreaName', 'N/A'),
            'latitude': park.get('RecAreaLatitude', 'N/A'),
            'longitude': park.get('RecAreaLongitude', 'N/A')
        }
        for park in recareas_data
        if search_query in park.get('RecAreaName', '').lower()
    ]

    # Sort parks by name
    parks = sorted(parks, key=lambda x: x['name'].lower())

    return render(request, 'camp/show_parks.html', {'parks': parks, 'search_query': search_query, 'title': 'Parks'})


def show_facilities(request, recarea_id):
    # Find all facilities linked to the given RecAreaID
    linked_facilities = [
        entry["FacilityID"] for entry in recareas_facilities_data if entry["RecAreaID"] == recarea_id
    ]

    # Retrieve FacilityNames for the found FacilityIDs
    facility_details = [
        {
            'id': facility["FacilityID"],
            'name': facility.get("FacilityName", "N/A"),
            'type': facility.get("FacilityTypeDescription", "N/A"),
            'latitude': facility.get("FacilityLatitude", "N/A"),
            'longitude': facility.get("FacilityLongitude", "N/A")
        }
        for facility in facilities_data if facility["FacilityID"] in linked_facilities
    ]

    # Sort facilities to show "Campground" type first
    facility_details = sorted(facility_details, key=lambda x: (
        x['type'] != "Campground", x['name']))

    return render(request, 'camp/show_facilities.html', {'facilities': facility_details, 'recarea_id': recarea_id, 'title': 'Facilities'})


def show_campsites(request):
    # Get the search query from the request
    search_query = request.GET.get('q', '').lower()

    # Filter the preloaded campsite_data based on the search query
    filtered_campsites = [
        {
            'id': campsite.get('CampsiteID', 'N/A'),
            'name': campsite.get('CampsiteName', 'N/A'),
            'loop': campsite.get('Loop', 'N/A'),
            'facility_id': campsite.get('FacilityID', 'N/A'),
        }
        for campsite in campsite_data
        if search_query in campsite.get('FacilityID', '').lower()
    ]

    return render(request, 'camp/show_campsites.html', {'campsites': filtered_campsites, 'search_query': search_query, 'title': 'Campsites'})
