# Finding Campsite IDs

## Recreation.gov
For the recreation API, the campsite ID is required to search for availability. The campsite ID is unique to each campsite and is used to identify the campsite in the API. The campsite ID can be found by inspecting the URL for a specific park. The campsite ID is usually a numerical value that corresponds to a specific campsite within the park.

For example, the URL for a Upper Pines Campground looks like this:

```plaintext 
https://www.recreation.gov/camping/campgrounds/232447
```

In this case, the campsite ID is `232447`. This ID can be used to search for availability for this specific campsite with the `--parks` command. 

## ReserveCalifornia
For the ReserveCalifornia API, the campsite ID is required to search for availability. The campsite ID is unique to each campsite and is used to identify the campsite in the API.

For example, the URL for North Beach Campground at the Pismo SB looks like this:

```plaintext
https://www.reservecalifornia.com/Web/Default.aspx#!park/691/615
```

In this case, the campsite ID is `615`. This ID can be used to search for availability for this specific campsite with the `--parks` command. 