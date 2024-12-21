from django.shortcuts import render
from django.http import HttpResponse
from datetime import datetime
from .camping import run_campsite_check


def select_camp(request):
    if request.method == "POST":
        # Process the form data
        start_date_str = request.POST.get("start_date")
        end_date_str = request.POST.get("end_date")

        # The campsite_id has comma separated values, so we need to split them into a list of integers
        campsite_id = int(request.POST.get("campsite_id"))

        nights = request.POST.get("nights")

        # The dates are in the format "YYYY-MM-DD", so we can parse them into datetime objects
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d")

        # Render the camp_result.html template with the results
        output, has_availabilities = run_campsite_check(
            [campsite_id], start_date, end_date, nights=int(nights)
        )

        # Create a context dictionary with the form data and the results
        context = {
            'start_date': start_date_str,
            'end_date': end_date_str,
            'campsite_id': campsite_id,
            'nights': nights,
            'output': output,
            'has_availabilities': has_availabilities,
            'title': 'Camp Reservation Result'
        }

        # Print the context to the console for debugging
        print(context)

        # Return the rendered template with the context data
        return render(request, 'camp/camp_result.html', context)

    # Render the select_camp.html template
    return render(request, 'camp/select_camp.html', {'title': 'Select Camp'})
