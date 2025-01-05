# reservecalifornia_client.py

import dataclasses
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List

import requests
from dateutil.relativedelta import relativedelta


LOG = logging.getLogger(__name__)
log_formatter = logging.Formatter(
    "%(asctime)s - %(process)s - %(levelname)s - %(message)s"
)

# FileHandler for file output
fh = logging.FileHandler('campquest.log')  # specify your log file name
fh.setFormatter(log_formatter)
LOG.addHandler(fh)

LOG.setLevel(logging.INFO)

BASE_URL = "https://calirdr.usedirect.com"
SEARCH_ENDPOINT = "/rdr/rdr/fd/citypark/namecontains/"
PLACE_ENDPOINT = "/rdr/rdr/search/place"
AVAILABILITY_ENDPOINT = "/rdr/rdr/search/grid"
DATE_FORMAT = "%m-%d-%Y"
CAMPGROUND_URL = "https://www.reservecalifornia.com/"


@dataclass
class Campsite:
    campground: str
    campsite: str


@dataclass
class AvailableCampsite:
    date: datetime
    campsite: Campsite

    def __lt__(self, other: 'AvailableCampsite') -> bool:
        return self.date < other.date

    def __hash__(self) -> int:
        return hash((self.date, self.campsite.campsite))


@dataclass
class ReserveCaliforniaCampsite:
    Campground: str
    UnitId: int
    Name: str
    ShortName: str
    RecentPopups: int
    IsAda: bool
    AllowWebBooking: bool
    MapInfo: Dict[str, Any]
    IsWebViewable: bool
    IsFiltered: bool
    UnitCategoryId: int
    SleepingUnitIds: List[int]
    UnitTypeGroupId: int
    UnitTypeId: int
    VehicleLength: int
    OrderBy: int
    OrderByRaw: int
    SliceCount: int
    AvailableCount: int
    Slices: Dict[str, Any]

    def get_availabilities(self) -> List[datetime]:
        availabilities: List[datetime] = []
        for campsite in self.Slices.values():
            if campsite["IsFree"]:
                date_string = campsite["Date"]
                date = datetime.strptime(date_string, "%Y-%m-%d")
                availabilities.append(date)
        return availabilities

    def to_campsite(self) -> Campsite:
        return Campsite(campground=self.Campground, campsite=self.Name)


def make_get_request(url: str) -> Dict[str, Any]:
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


def make_post_request(url: str, data: Dict[str, Any]) -> Dict[str, Any]:
    response = requests.post(url, json=data)
    response.raise_for_status()
    return response.json()


def get_campground_id(query: str, url: str = f"{BASE_URL}{SEARCH_ENDPOINT}") -> str:
    url_with_query = f"{url}{requests.utils.quote(query)}"  # type: ignore
    response = make_get_request(url_with_query)
    if not response:
        LOG.error(f"Could not find campground: {query}")
        raise ValueError(
            f"Campground: {query} not found. Try being more specific.")
    top_hit = response[0]
    campground_name = top_hit["Name"]
    campground_id = top_hit["PlaceId"]
    LOG.info(
        f"Found campground: {campground_name} (campground id: {campground_id})")
    return campground_id


def get_facility_ids(
    campground: str, url: str = f"{BASE_URL}{PLACE_ENDPOINT}"
) -> List[Dict[str, str]]:
    campground_id = get_campground_id(campground)
    data = {
        "PlaceId": campground_id,
        "StartDate": datetime.today().strftime("%m-%d-%Y"),
    }
    response = make_post_request(url, data)
    if "SelectedPlace" not in response or response["SelectedPlace"] is None:
        LOG.error(f"Could not find facilities in {campground}")
        raise ValueError(
            f"Could not find facilities in {campground} - try being more specific."
        )
    facilities = response["SelectedPlace"]["Facilities"]
    facility_ids: List[Dict[str, str]] = []
    for facility in facilities.values():
        data = {
            "campground": facility["Name"],
            "facility_id": str(facility["FacilityId"]),
        }
        facility_ids.append(data)
    return sorted(facility_ids, key=lambda x: x.get("campground", ""))


def get_all_campsites(
    campground_id: str, start_date: datetime, months: int
) -> List[ReserveCaliforniaCampsite]:
    data = {
        "FacilityId": campground_id,
        "StartDate": start_date.strftime(DATE_FORMAT),
        "EndDate": (start_date + relativedelta(months=months)).strftime(DATE_FORMAT),
    }
    url = f"{BASE_URL}{AVAILABILITY_ENDPOINT}"
    response = make_post_request(url, data)
    campground = response["Facility"]["Name"]
    if not campground:
        LOG.error(f"Could not find campground with ID: {campground_id}")
        raise ValueError(f"Could not find campground with ID: {campground_id}")
    LOG.info(
        f"Found campground: {campground} (campground id: {campground_id})")
    campsites = response["Facility"]["Units"].values()
    results: List[ReserveCaliforniaCampsite] = []
    field_names = [x.name for x in dataclasses.fields(
        ReserveCaliforniaCampsite)]
    for site in campsites:
        site["Campground"] = campground
        site_data = {field: site[field] for field in field_names}
        results.append(ReserveCaliforniaCampsite(**site_data))
    return results


def rc_get_all_available_campsites(
    campground_id: str, start_date: datetime, months: int
) -> List[AvailableCampsite]:
    results: List[AvailableCampsite] = []
    campsites = get_all_campsites(
        campground_id=campground_id, start_date=start_date, months=months
    )
    for campsite in campsites:
        availabilities = campsite.get_availabilities()
        if availabilities:
            for date in availabilities:
                results.append(AvailableCampsite(date, campsite.to_campsite()))
    return results


def rc_get_campground_url(campground_id: str) -> str:
    return CAMPGROUND_URL
