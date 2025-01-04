# -*- coding: utf-8 -*-
#!/usr/bin/env python3

import json
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from itertools import count, groupby

from dateutil import rrule

from clients.recreation_client import RecreationClient
from enums.date_format import DateFormat
from enums.emoji import Emoji
from utils import formatter

LOG = logging.getLogger(__name__)
log_formatter = logging.Formatter(
    "%(asctime)s - %(process)s - %(levelname)s - %(message)s"
)
sh = logging.StreamHandler()
sh.setFormatter(log_formatter)
LOG.addHandler(sh)


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


def get_park_information(
    park_id, start_date, end_date, campsite_type=None, campsite_ids=(), excluded_site_ids=[]
):
    start_of_month = datetime(start_date.year, start_date.month, 1)
    months = list(
        rrule.rrule(rrule.MONTHLY, dtstart=start_of_month, until=end_date)
    )

    api_data = []
    for month_date in months:
        api_data.append(RecreationClient.get_availability(park_id, month_date))

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
                    and campsite_data["campsite_id"] not in campsite_ids
                ):
                    continue

                available.append(date)
            if available:
                a += available

    return data


def is_weekend(date):
    weekday = date.weekday()
    return weekday == 5 or weekday == 6  # Saturday is 5, Sunday is 6


def get_num_available_sites(
    park_information, start_date, end_date, nights=None, weekends_only=False,
):
    maximum = len(park_information)
    num_available = 0
    num_days = (end_date - start_date).days
    dates = [end_date - timedelta(days=i) for i in range(1, num_days + 1)]

    if weekends_only:
        # Convert the filter object to a list
        dates = list(filter(is_weekend, dates))
    dates = set(
        formatter.format_date(
            i, format_string=DateFormat.ISO_DATE_FORMAT_RESPONSE.value
        )
        for i in dates
    )

    if nights not in range(1, num_days + 1):
        nights = num_days
        # LOG.debug("Setting number of nights to {}.".format(nights))

    available_dates_by_campsite_id = defaultdict(list)
    for site, availabilities in park_information.items():
        desired_available = [
            date for date in availabilities if date in dates
        ]

        if not desired_available:
            continue

        appropriate_consecutive_ranges = consecutive_nights(
            desired_available, nights
        )

        if appropriate_consecutive_ranges:
            num_available += 1
            # LOG.debug("Available site {}: {}".format(num_available, site))

        for r in appropriate_consecutive_ranges:
            start, end = r
            available_dates_by_campsite_id[int(site)].append(
                {"start": start, "end": end}
            )

    return num_available, maximum, available_dates_by_campsite_id


def consecutive_nights(available, nights):
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
    park_id, start_date, end_date, campsite_type, campsite_ids=(), nights=None, weekends_only=False, excluded_site_ids=[],
):
    park_information = get_park_information(
        park_id, start_date, end_date, campsite_type, campsite_ids, excluded_site_ids=excluded_site_ids,
    )
    # LOG.debug(
    #     "Information for park {}: {}".format(
    #         park_id, json.dumps(park_information, indent=2)
    #     )
    # )
    park_name = RecreationClient.get_park_name(park_id)
    current, maximum, availabilities_filtered = get_num_available_sites(
        park_information, start_date, end_date, nights=nights, weekends_only=weekends_only,
    )
    return current, maximum, availabilities_filtered, park_name


def run_campsite_check(
    parks,
    start_date,
    end_date,
    campsite_type=None,
    campsite_ids=(),
    nights=None,
    weekends_only=False,
    show_campsite_info=False,
    excluded_site_ids=[],
    json_output=False,
):
    info_by_park_id = {}
    for park_id in parks:
        info_by_park_id[park_id] = check_park(
            park_id,
            start_date,
            end_date,
            campsite_type,
            campsite_ids,
            nights=nights,
            weekends_only=weekends_only,
            excluded_site_ids=excluded_site_ids,
        )
    if json_output:
        output, has_availabilities = generate_json_output(info_by_park_id)
    else:
        output, has_availabilities = generate_human_output(
            info_by_park_id, start_date, end_date, gen_campsite_info=show_campsite_info
        )

    if show_campsite_info:
        return output, has_availabilities, info_by_park_id

    return output, has_availabilities


def generate_human_output(
    info_by_park_id, start_date, end_date, gen_campsite_info=False
):
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
            0,
            "There are campsites available from {start} to {end} 🟩".format(
                start=start_date.strftime(DateFormat.INPUT_DATE_FORMAT.value),
                end=end_date.strftime(DateFormat.INPUT_DATE_FORMAT.value),
            ),
        )
    else:
        out.insert(0, "There are no campsites available 😢")
    return "\n".join(out), has_availabilities


def generate_json_output(info_by_park_id):
    availabilities_by_park_id = {}
    has_availabilities = False
    for park_id, info in info_by_park_id.items():
        current, _, available_dates_by_site_id, _ = info
        if current:
            has_availabilities = True
            availabilities_by_park_id[park_id] = available_dates_by_site_id

    return json.dumps(availabilities_by_park_id), has_availabilities
