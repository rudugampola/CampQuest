from django.shortcuts import render
from datetime import datetime
from .camping import run_campsite_check
import json
from django.http import JsonResponse
from django.conf import settings
import os
import ijson

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
    # Define the file path
    file_path = os.path.join(settings.BASE_DIR, 'camp',
                             'other', 'RecAreas_API_v1.json')

    # Get the search query from the request
    search_query = request.GET.get('q', '').lower()

    # Initialize an empty list to hold the filtered parks
    parks = []

    # Read the JSON data from the file using ijson
    try:
        with open(file_path, 'r', encoding='utf-8') as json_file:
            # Use ijson to parse the JSON incrementally
            objects = ijson.items(json_file, 'RECDATA.item')
            for obj in objects:
                if isinstance(obj, dict) and search_query in obj.get('RecAreaName', '').lower():
                    parks.append({
                        'id': obj.get('RecAreaID', 'N/A'),
                        'name': obj.get('RecAreaName', 'N/A'),
                        'latitude': obj.get('RecAreaLatitude', 'N/A'),
                        'longitude': obj.get('RecAreaLongitude', 'N/A')
                    })

        return render(request, 'camp/show_parks.html', {'parks': parks, 'search_query': search_query})
    except FileNotFoundError:
        return JsonResponse({'error': 'RecAreas_API_v1.json file not found'}, status=404)
    except ijson.JSONError:
        return JsonResponse({'error': 'Error decoding JSON data'}, status=500)
    except UnicodeDecodeError as e:
        return JsonResponse({'error': f'Unicode decode error: {str(e)}'}, status=500)
    except Exception as e:
        return JsonResponse({'error': f'Unexpected error: {str(e)}'}, status=500)


def show_campsites(request):
    # Define the file path
    file_path = os.path.join(settings.BASE_DIR, 'camp',
                             'other', 'Campsites_API_v1.json')

    # Get the search query from the request
    search_query = request.GET.get('q', '').lower()

    # Initialize an empty list to hold the filtered campsites
    campsites = []

    # Read the JSON data from the file using ijson
    try:
        with open(file_path, 'r', encoding='utf-8') as json_file:
            # Use ijson to parse the JSON incrementally
            objects = ijson.items(json_file, 'RECDATA.item')
            for obj in objects:
                if isinstance(obj, dict) and search_query in obj.get('FacilityID', '').lower():
                    campsites.append({
                        'id': obj.get('CampsiteID', 'N/A'),
                        'name': obj.get('CampsiteName', 'N/A'),
                        'loop': obj.get('Loop', 'N/A'),
                        'facility_id': obj.get('FacilityID', 'N/A'),
                    })

        return render(request, 'camp/show_campsites.html', {'campsites': campsites, 'search_query': search_query})
    except FileNotFoundError:
        return JsonResponse({'error': 'Campsites_API_v1.json file not found'}, status=404)
    except ijson.JSONError:
        return JsonResponse({'error': 'Error decoding JSON data'}, status=500)
    except UnicodeDecodeError as e:
        return JsonResponse({'error': f'Unicode decode error: {str(e)}'}, status=500)
    except Exception as e:
        return JsonResponse({'error': f'Unexpected error: {str(e)}'}, status=500)
