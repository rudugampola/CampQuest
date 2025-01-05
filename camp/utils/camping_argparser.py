import logging
import sys
from datetime import datetime

import rich_click as click
from camp.enums.date_format import DateFormat


@click.command()
@click.option("--debug", "-d", is_flag=True, help="Debug log level")
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
        "Optional, can specify type of campsite such as:"
        '"STANDARD NONELECTRIC" or TODO'
    ),
)
@click.option(
    "--json-output",
    is_flag=True,
    help=(
        "This make the script output JSON instead of human readable "
        "output. Note, this is incompatible with the twitter notifier. "
        "This output includes more precise information, such as the exact "
        "available dates and which sites are available."
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
    help=(
        "File with site IDs to exclude"
    ),
)
@click.option(
    "--parks",
    type=int,
    multiple=True,
    help="Park ID(s)",
)
@click.option(
    "--stdin",
    "-",
    is_flag=True,
    help="Read list of park ID(s) from stdin instead",
)
def main(debug, start_date, end_date, nights, campsite_ids, show_campsite_info, campsite_type, json_output,
         weekends_only, exclusion_file, parks, stdin):
    if debug:
        logging.basicConfig(level=logging.DEBUG)

    if stdin:
        parks = tuple(map(int, sys.stdin.read().strip().split()))

    # Validate mutually exclusive options
    if parks and stdin:
        raise click.UsageError(
            "Illegal usage: --parks is mutually exclusive with --stdin.")

    _validate_args(parks, campsite_ids)


def _validate_args(parks, campsite_ids):
    if len(parks) > 1 and len(campsite_ids) > 0:
        raise click.BadParameter(
            "--campsite-ids can only be used with a single park ID."
        )


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


if __name__ == '__main__':
    main()
