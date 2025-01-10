# -*- coding: utf-8 -*-
#!/usr/bin/env python3

import json
import logging
import sys
import time
import rich_click as click
from collections import defaultdict
from datetime import datetime, timedelta
from itertools import count, groupby

from dateutil import rrule

from camp.clients.recreation_client import RecreationClient
from camp.enums.date_format import DateFormat
from camp.enums.emoji import Emoji
from camp.utils import formatter

from camp.clients.reservecalifornia_client import rc_get_all_available_campsites, rc_get_campground_url

from notifier import send_notification, check_limit

click.rich_click.USE_RICH_MARKUP = True

LOG = logging.getLogger(__name__)
log_formatter = logging.Formatter(
    "%(asctime)s - %(process)s - %(levelname)s - %(message)s"
)

# FileHandler for file output with UTF-8 encoding
fh = logging.FileHandler('campquest.log', encoding='utf-8')
fh.setFormatter(log_formatter)
LOG.addHandler(fh)


class bcolors:
    """ ANSI color codes for terminal output
    """
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def get_park_information(
    park_id, start_date, end_date, campsite_type=None, campsite_ids=(), excluded_site_ids=[]
):
    """ Get park information for a given date range.

    Args:
        park_id: The park ID to get information for.
        start_date: The start date of the date range.
        end_date: The end date of the date range.
        campsite_type: The campsite type, only for recreation.gov. Defaults to None.
        campsite_ids: The campsite IDs to get information for. Defaults to ().
        excluded_site_ids: The campsite IDs to exclude. Defaults to [].

    Returns:
        dict: The park information.
    """
    # Get each first of the month for months in the range we care about.
    start_of_month = datetime(start_date.year, start_date.month, 1)
    months = list(
        rrule.rrule(rrule.MONTHLY, dtstart=start_of_month, until=end_date)
    )

    # Get data for each month.
    api_data = []
    for month_date in months:
        api_data.append(RecreationClient.get_availability(park_id, month_date))

    # Collapse the data into the described output format.
    # Filter by campsite_type if necessary.
    data = {}

    for month_data in api_data:
        for campsite_id, campsite_data in month_data["campsites"].items():
            if campsite_id in excluded_site_ids:
                continue
            available = []
            a = data.setdefault(campsite_id, [])
            for date, availability_value in campsite_data[
                "availabilities"
            ].items():
                if availability_value != "Available":
                    continue

                if (
                    campsite_type
                    and campsite_type != campsite_data["campsite_type"]
                ):
                    continue

                if (
                    len(campsite_ids) > 0
                    and int(campsite_data["campsite_id"]) not in campsite_ids
                ):
                    continue

                available.append(date)
            if available:
                a += available

    return data


def is_weekend(date):
    """ Check if a date is a weekend.

    Args:
        date: The date to check if it is a weekend.

    Returns:
        bool: True if the date is a weekend, False otherwise.
    """
    weekday = date.weekday()
    return weekday == 5 or weekday == 6


def get_num_available_sites(
    park_information, start_date, end_date, nights=None, weekends_only=False,
):
    """ Get the number of available sites for a given date range.

    Args:
        park_information: The park information.
        start_date: The start date of the date range.
        end_date: The end date of the date range.
        nights: The number of nights. Defaults to None.
        weekends_only: Whether to include only weekends. Defaults to False.

    Returns:
        tuple: The number of available sites, the maximum number of sites, and the available dates by campsite ID
    """
    maximum = len(park_information)

    num_available = 0
    num_days = (end_date - start_date).days
    dates = [end_date - timedelta(days=i) for i in range(1, num_days + 1)]
    if weekends_only:
        dates = filter(is_weekend, dates)
    dates = set(
        formatter.format_date(
            i, format_string=DateFormat.ISO_DATE_FORMAT_RESPONSE.value
        )
        for i in dates
    )

    if nights not in range(1, num_days + 1):
        nights = num_days
        LOG.info("Setting number of nights to {}.".format(nights))

    available_dates_by_campsite_id = defaultdict(list)
    for site, availabilities in park_information.items():
        # List of dates that are in the desired range for this site.
        desired_available = []

        for date in availabilities:
            if date not in dates:
                continue
            desired_available.append(date)

        if not desired_available:
            continue

        appropriate_consecutive_ranges = consecutive_nights(
            desired_available, nights
        )

        if appropriate_consecutive_ranges:
            num_available += 1
            LOG.info("Available site {}: {}".format(num_available, site))

        for r in appropriate_consecutive_ranges:
            start, end = r
            available_dates_by_campsite_id[int(site)].append(
                {"start": start, "end": end}
            )

    return num_available, maximum, available_dates_by_campsite_id


def consecutive_nights(available, nights):
    """ Returns a list of dates from which you can start that have
    enough consecutive nights. If there is one or more entries in this list, there is at least one date range for this site that is available.

    Args:
        available: The list of available dates.
        nights: The number of nights to find.

    Returns:
        list: The list of consecutive nights.
    """
    ordinal_dates = [
        datetime.strptime(
            dstr, DateFormat.ISO_DATE_FORMAT_RESPONSE.value
        ).toordinal()
        for dstr in available
    ]
    c = count()

    consecutive_ranges = list(
        list(g) for _, g in groupby(ordinal_dates, lambda x: x - next(c))
    )

    long_enough_consecutive_ranges = []
    for r in consecutive_ranges:
        # Skip ranges that are too short.
        if len(r) < nights:
            continue
        for start_index in range(0, len(r) - nights + 1):
            start_nice = formatter.format_date(
                datetime.fromordinal(r[start_index]),
                format_string=DateFormat.INPUT_DATE_FORMAT.value,
            )
            end_nice = formatter.format_date(
                datetime.fromordinal(r[start_index + nights - 1] + 1),
                format_string=DateFormat.INPUT_DATE_FORMAT.value,
            )
            long_enough_consecutive_ranges.append((start_nice, end_nice))

    return long_enough_consecutive_ranges


def check_park(
    park_id, start_date, end_date, campsite_type, campsite_ids=(), nights=None, weekends_only=False, excluded_site_ids=[], source="recreation",
):
    """ Check a park for availability.

    Args:
        park_id: The park ID to check.
        start_date: The start date.
        end_date: The end date.
        campsite_type: The campsite type. Defaults to None.
        campsite_ids: The campsite IDs. Defaults to ().
        nights: The number of nights. Defaults to None.
        weekends_only: Whether to include only weekends. Defaults to False.
        excluded_site_ids: The campsite IDs to exclude. Defaults to [].
        source: The source of the park information, recreation or reserve_california. Defaults to "recreation".

    Returns:
        tuple: The number of available sites, the maximum number of sites, and the available dates by campsite ID
    """
    if source == "recreation":
        park_information = get_park_information(
            park_id, start_date, end_date, campsite_type, campsite_ids, excluded_site_ids=excluded_site_ids,
        )
        # LOG.info(
        #     "Information for park {}: {}".format(
        #         park_id, json.dumps(park_information, indent=2)
        #     )
        # )
        park_name = RecreationClient.get_park_name(park_id)
        current, maximum, availabilities_filtered = get_num_available_sites(
            park_information, start_date, end_date, nights=nights, weekends_only=weekends_only,
        )
    elif source == "reserve_california":
        park_information = rc_get_all_available_campsites(
            park_id, start_date, (end_date - start_date).days // 30
        )
        # Update with the actual park name if available
        park_name = "ReserveCalifornia Park"
        current = len(park_information)
        maximum = current  # Update with the actual max if available
        availabilities_filtered = {site.campsite.campsite: [
            {"start": site.date, "end": site.date}] for site in park_information}

    return current, maximum, availabilities_filtered, park_name


def generate_human_output(
    info_by_park_id, start_date, end_date, gen_campsite_info=False
):
    """ Generate human readable output. If gen_campsite_info is True, it will also display campsite ID and availability dates.

    Args:
        info_by_park_id: The information by park ID.
        start_date: The start date.
        end_date: The end date.
        gen_campsite_info: Whether to display campsite ID and availability dates. Defaults to False. 

    Returns:
        tuple: The human readable output and whether there are availabilities.
    """
    out = []
    has_availabilities = False
    for park_id, info in info_by_park_id.items():
        current, maximum, available_dates_by_site_id, park_name = info
        if current:
            emoji = Emoji.SUCCESS.value
            has_availabilities = True
        else:
            emoji = Emoji.FAILURE.value

        out.append(
            "{emoji} {park_name} ({park_id}): {current} site(s) available out of {maximum} site(s)".format(
                emoji=emoji,
                park_name=park_name,
                park_id=park_id,
                current=current,
                maximum=maximum,
            )
        )

        # Displays campsite ID and availability dates.
        if gen_campsite_info and available_dates_by_site_id:
            for site_id, dates in available_dates_by_site_id.items():
                out.append(
                    "  * Site {site_id} is available on the following dates:".format(
                        site_id=site_id
                    )
                )
                for date in dates:
                    out.append(
                        "    * {start} -> {end}".format(
                            start=date["start"], end=date["end"]
                        )
                    )

    if has_availabilities:
        out.insert(
            0, "There are campsites available from {start} to {end} 😊".format(
                start=start_date.strftime(DateFormat.INPUT_DATE_FORMAT.value),
                end=end_date.strftime(DateFormat.INPUT_DATE_FORMAT.value),
            ),
        )
    else:
        out.insert(0, "There are no campsites available 😢")
    return "\n".join(out), has_availabilities


def generate_json_output(info_by_park_id):
    """ Generate JSON output.

    Args:
        info_by_park_id: The information by park ID. 

    Returns:
        tuple: The JSON output and whether there are availabilities.
    """
    availabilities_by_park_id = {}
    has_availabilities = False
    for park_id, info in info_by_park_id.items():
        current, _, available_dates_by_site_id, _ = info
        if current:
            has_availabilities = True
            availabilities_by_park_id[park_id] = available_dates_by_site_id

    return json.dumps(availabilities_by_park_id), has_availabilities


def remove_comments(lines: list[str]) -> list[str]:
    """ Remove comments from a list of lines. Comments are lines that start with a '#'.

    Args:
        lines (list[str]): The list of lines to remove comments from.

    Returns:
        list[str]: The list of lines with comments removed.
    """
    new_lines = []
    for line in lines:
        if line.startswith("#"):  # Deal with comment as the first character
            continue

        # line is split into two parts by the comment delimiter " #". The first part is retained
        line = line.split(" #")[0]
        stripped = line.strip()
        if stripped != "":
            new_lines.append(stripped)

    return new_lines


def countdown_timer(seconds):
    """ Countdown timer for a given number of seconds.  

    Args:
        seconds: The number of seconds to countdown.
    """
    for remaining in range(seconds, 0, -1):
        sys.stdout.write("\r")
        sys.stdout.write(bcolors.WARNING +
                         f"No campsites found, checking again in {remaining} seconds..." + bcolors.ENDC)
        sys.stdout.flush()
        time.sleep(1)
    sys.stdout.write("\r")  # Move cursor to the beginning of the line
    sys.stdout.write("\033[K")  # Clear the line from the cursor to the end
    sys.stdout.write("Completed waiting.\n")


@click.command()
@click.option(
    "--start-date",
    required=True,
    help="Start date [YYYY-MM-DD]",
    type=str,
    callback=lambda ctx, param, value: TypeConverter.date(value),
)
@click.option(
    "--end-date",
    required=True,
    help="End date [YYYY-MM-DD]. You expect to leave this day, not stay the night.",
    type=str,
    callback=lambda ctx, param, value: TypeConverter.date(value),
)
@click.option(
    "--nights",
    help="Number of consecutive nights (default is all nights in the given range).",
    type=int,
    callback=lambda ctx, param, value: TypeConverter.positive_int(
        value) if value else value,
)
@click.option(
    "--campsite-ids",
    type=int,
    multiple=True,
    default=(),
    help="Optional, search for availability for a specific campsite ID.",
)
@click.option(
    "--show-campsite-info",
    is_flag=True,
    help="Display campsite ID and availability dates.",
)
@click.option(
    "--campsite-type",
    help=(
        "Optional, can specify type of campsite such as: STANDARD NONELECTRIC"
    ),
)
@click.option(
    "--json-output",
    is_flag=True,
    help=(
        "This make the script output JSON instead of human readable output. Note, this is incompatible with the twitter notifier. This output includes more precise information, such as the exact available dates and which sites are available."
    ),
)
@click.option(
    "--weekends-only",
    is_flag=True,
    help=(
        "Include only weekends (i.e. starting Friday or Saturday)"
    ),
)
@click.option(
    "--exclusion-file",
    is_flag=True,
    help=(
        "Read a list of campsite IDs to exclude from a file. For powershell use: Get-Content parks.txt | python cli.py --exclusion-file"
    ),
)
@click.option(
    "--parks",
    type=int,
    multiple=True,
    help="Park ID(s). Can provide multiple park IDs separated by multuple --parks options.",
)
@click.option(
    "--stdin",
    is_flag=True,
    help="Read a list of park ID(s) from a file. For powershell use: Get-Content parks.txt | python cli.py --stdin",
)
@click.option("--debug", "-d", is_flag=True, help="Enable :point_right: [yellow]debug mode[/] :point_left: log level")
@click.option(
    "--source",
    type=click.Choice(['recreation', 'reserve_california'],
                      case_sensitive=False),
    default='recreation',
    help="Source of park information."
)
@click.option(
    "--notify",
    is_flag=True,
    help="Send a Pushover notification when campsites are available.",
)
def main(debug, start_date, end_date, nights, campsite_ids, show_campsite_info, campsite_type, json_output,
         weekends_only, exclusion_file, parks, stdin, source, notify):
    """ 
        This program is designed to check the availability of campsites in various parks over a specified date range. It uses a rich set of options to customize the search criteria and output format.
    """

    if debug:
        LOG.setLevel(logging.DEBUG)
        LOG.debug("Debug mode enabled.")
    else:
        LOG.setLevel(logging.INFO)

    LOG.info("Received inputs: start_date=%s, end_date=%s, nights=%s, campsite_ids=%s, show_campsite_info=%s, campsite_type=%s, json_output=%s, weekends_only=%s, exclusion_file=%s, parks=%s, stdin=%s, source=%s, notify=%s",
             start_date, end_date, nights, campsite_ids, show_campsite_info, campsite_type, json_output, weekends_only, exclusion_file, parks, stdin, source, notify)

    if stdin:
        input_lines = sys.stdin.read().strip().split('\n')
        filtered_lines = remove_comments(input_lines)
        parks = tuple(map(int, ' '.join(filtered_lines).split()))
        # parks = tuple(map(int, sys.stdin.read().strip().split()))
    elif not parks:
        raise click.UsageError(
            "You must provide at least one park ID using --parks or --stdin.")

    excluded_site_ids = []
    if exclusion_file:
        with open(exclusion_file, "r") as f:
            excluded_site_ids = f.readlines()
            excluded_site_ids = [l.strip() for l in excluded_site_ids]
            excluded_site_ids = remove_comments(excluded_site_ids)

    remaining_parks = set(parks)  # Track parks without availability

    while remaining_parks:
        parks_to_check = list(remaining_parks)  # Copy the remaining parks list

        for park_id in parks_to_check:
            info_by_park_id = {}
            info_by_park_id[park_id] = check_park(
                park_id,
                start_date,
                end_date,
                campsite_type,
                campsite_ids,
                nights=nights,
                weekends_only=weekends_only,
                excluded_site_ids=excluded_site_ids,
                source=source
            )

            if json_output:
                output, has_availabilities = generate_json_output(
                    info_by_park_id)
            else:
                output, has_availabilities = generate_human_output(
                    info_by_park_id,
                    start_date,
                    end_date,
                    show_campsite_info,
                )

            #  Setup so it runs in a loop if notify is selected until a site is found
            if has_availabilities:
                print(output)
                LOG.info("Output: %s", output)
                LOG.info("Success! Output generated - No Notification Sent!")
                remaining_parks.remove(park_id)  # Remove park from the loop
                # return has_availabilities
                if notify:
                    print(output)
                    send_notification(output, "CampQuest")
                    limit_data = check_limit()
                    LOG.info("Message limit: %s, Remaining: %s",
                             limit_data.get("limit"), limit_data.get("remaining"))
                    LOG.info("Success! Output generated - Notification Sent!")
                    return has_availabilities
            else:
                LOG.info(f"No availability for park ID {park_id}.")

        if remaining_parks:
            LOG.info(
                "No availability found for some parks, checking again in 60 seconds...")
            countdown_timer(60)  # Wait 60 seconds before re-checking
        else:
            LOG.info("All parks checked. Exiting loop.")


class TypeConverter:
    @classmethod
    def date(cls, date_str):
        try:
            return datetime.strptime(
                date_str, DateFormat.INPUT_DATE_FORMAT.value
            )
        except ValueError as e:
            msg = "Not a valid date: '{0}'.".format(date_str)
            logging.critical(e)
            raise click.BadParameter(msg)

    @classmethod
    def positive_int(cls, i):
        i = int(i)
        if i <= 0:
            msg = "Not a valid number of nights: {0}".format(i)
            raise click.BadParameter(msg)
        return i


if __name__ == "__main__":
    main()
