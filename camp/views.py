from django.shortcuts import render
from django.http import HttpResponse
from datetime import datetime
from collections import defaultdict
from .camping import run_campsite_check

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

        # The campsite_id has comma-separated values, so we need to split them into a list of integers
        campsite_id = int(request.POST.get("campsite_id"))

        nights = request.POST.get("nights")

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
                [campsite_id],
                start_date,
                end_date,
                nights=int(nights),
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
                [campsite_id],
                start_date,
                end_date,
                nights=int(nights),
                show_campsite_info=show_campsite_info,
                weekends_only=weekends_only
            )
            campsite_info = None

        # Create a context dictionary with the form data and the results
        context = {
            'start_date': start_date_str,
            'end_date': end_date_str,
            'campsite_id': campsite_id,
            'nights': nights,
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
