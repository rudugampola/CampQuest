# Command Line Usage

The CampQuest application has a command line interface (CLI) that can be used to interact with the application. The CLI tool can be used to search for campsites by specifying start and end dates and with other optional parameters. 


`python cli.py --help` will display the help message and list all the available options.

```bash
Usage: cli.py [OPTIONS]

This program is designed to check the availability of campsites in various parks over a specified date range. It uses a rich set of options to customize the
search criteria and output format.

─ Options 

*  --start-date              TEXT                             Start date [YYYY-MM-DD] [required]
*  --end-date                TEXT                             End date [YYYY-MM-DD]. You expect to leave this day, not stay the night. [required]
   --nights                  INTEGER                          Number of consecutive nights (default is all nights in the given range).
   --campsite-ids            INTEGER                          Optional, search for availability for a specific campsite ID.
   --show-campsite-info                                       Display campsite ID and availability dates.
   --campsite-type           TEXT                             Optional, can specify type of campsite such as:"STANDARD NONELECTRIC" or TODO
   --json-output                                              This make the script output JSON instead of human readable output. Note, this is incompatible
                                                              with the twitter notifier. This output includes more precise information, such as the exact
                                                              available dates and which sites are available.
   --weekends-only                                            Include only weekends (i.e. starting Friday or Saturday)
   --exclusion-file                                           Read a list of campsite IDs to exclude from a file. For powershell use: Get-Content parks.txt |
                                                              python cli.py --exclusion-file
   --parks                   INTEGER                          Park ID(s). Can provide multiple park IDs separated by multiple --parks options.
   --stdin                                                    Read a list of park ID(s) from a file. For powershell use: Get-Content parks.txt | python
                                                              cli.py --stdin
   --debug               -d                                   Enable debug mode log level
   --source                  [recreation|reserve_california]  Source of park information.
   --notify                                                   Send a Pushover notification when campsites are available.
   --help                                                     Show this message and exit.

```

## Examples

### Search for campsites in all parks for a specific date range

```bash
python cli.py --start-date 2021-07-01 --end-date 2021-07-05 --parks 272299
```

### Search for campsites in all parks for a specific date range and show campsite info.

```bash
python cli.py --start-date 2021-07-01 --end-date 2021-07-05 --parks 272299 --show-campsite-info --notify
```

```--notify``` will send a pushover notification if campsites are available. If no sites are available, the search will be repeated every 1 minute until an unavailable site becomes available.
