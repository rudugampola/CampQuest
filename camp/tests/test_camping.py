import unittest
from click.testing import CliRunner
import camp.cli as cli
from camp.enums.date_format import DateFormat
from camp.enums.emoji import Emoji
from camp.cli import TypeConverter


class TestCamping(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()
        self.start_date = ["--start-date", "2022-01-01"]
        self.end_date = ["--end-date", "2022-01-02"]
        self.parks = ["--parks", "111"]
        self.default_args = []
        self.default_args.extend(self.start_date)
        self.default_args.extend(self.end_date)
        self.default_args.extend(self.parks)

    def testCampsiteIdsWithMoreThanOneCampgroundIdThrowsException(self):
        args = ["--campsite-ids", "333", "--parks", "1", "2"]
        args.extend(self.start_date)
        args.extend(self.end_date)
        result = self.runner.invoke(cli.main, args)
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("Error", result.output)

    def testAcceptsMultipleCampsiteIds(self):
        args = ["--campsite-ids", "333", "444"]
        args.extend(self.default_args)
        result = self.runner.invoke(cli.main, args)
        self.assertEqual(result.exit_code, 0)

    def testAcceptsMultipleCampgroundIds(self):
        args = ["--parks", "333", "444"]
        args.extend(self.start_date)
        args.extend(self.end_date)
        result = self.runner.invoke(cli.main, args)
        self.assertEqual(result.exit_code, 0)

    def testGetNumAvailableSites_AggregatesDataForMultipleCampsites(self):
        park_info = {
            "1": [],
            "2": [
                "2022-06-22T00:00:00Z",
                "2022-06-23T00:00:00Z",
                "2022-06-26T00:00:00Z",
            ],
            "3": [
                "2022-06-22T00:00:00Z",
                "2022-06-23T00:00:00Z",
                "2022-06-26T00:00:00Z",
                "2022-06-27T00:00:00Z",
                "2022-06-29T00:00:00Z",
            ],
        }

        _, _, available_dates_by_campsite_id = cli.get_num_available_sites(
            park_info,
            TypeConverter.date("2022-06-22"),
            TypeConverter.date("2022-06-23"),
        )

        self.assertFalse(1 in available_dates_by_campsite_id)
        self.assertTrue(2 in available_dates_by_campsite_id)
        self.assertTrue(3 in available_dates_by_campsite_id)

    def testGenerateOutputToHuman_DefaultOutputWithAvailabilities(self):
        start_date = TypeConverter.date("2022-06-01")
        end_date = TypeConverter.date("2022-07-01")
        park_name = "SOME PARK"
        park_id = 1
        current = 2
        maximum = 3

        expected = "\n".join(
            [
                """There are campsites available from {start} to {end} 😊""",
                """{emoji} {park_name} ({park_id}): {current} site(s) available out of {maximum} site(s)""",
            ]
        ).format(
            start=start_date.strftime(DateFormat.INPUT_DATE_FORMAT.value),
            end=end_date.strftime(DateFormat.INPUT_DATE_FORMAT.value),
            emoji=Emoji.SUCCESS.value,
            park_name=park_name,
            park_id=park_id,
            current=current,
            maximum=maximum,
        )

        info_by_park_id = {
            park_id: (
                current,
                maximum,
                {
                    18621: [{"start": "2022-06-22", "end": "2022-06-23"}],
                    18654: [{"start": "2022-06-22", "end": "2022-06-23"}],
                },
                park_name,
            )
        }
        output, _ = cli.generate_human_output(
            info_by_park_id, start_date, end_date
        )
        self.assertEqual(output, expected)

    def testGenerateOutputToHuman_DefaultOutputWithNoAvailabilities(self):
        start_date = TypeConverter.date("2022-06-01")
        end_date = TypeConverter.date("2022-07-01")
        park_name = "SOME PARK"
        park_id = 1
        current = 0
        maximum = 3

        expected = "\n".join(
            [
                """There are no campsites available 😢""",
                """{emoji} {park_name} ({park_id}): {current} site(s) available out of {maximum} site(s)""",
            ]
        ).format(
            start=start_date.strftime(DateFormat.INPUT_DATE_FORMAT.value),
            end=end_date.strftime(DateFormat.INPUT_DATE_FORMAT.value),
            emoji=Emoji.FAILURE.value,
            park_name=park_name,
            park_id=park_id,
            current=current,
            maximum=maximum,
        )

        info_by_park_id = {park_id: (current, maximum, {}, park_name)}
        output, _ = cli.generate_human_output(
            info_by_park_id, start_date, end_date
        )
        self.assertEqual(output, expected)

    def testGenerateOutputToHuman_SiteOutputWithAvailabilities(self):
        start_date = TypeConverter.date("2022-06-01")
        end_date = TypeConverter.date("2022-07-01")
        park_name = "SOME PARK"
        park_id = 1
        current = 2
        maximum = 3
        site_id1 = 1000
        site_id2 = 1001
        site1_date = {"start": "2022-06-22", "end": "2022-06-23"}
        site2_date = {"start": "2022-06-22", "end": "2022-06-23"}

        expected = "\n".join(
            [
                """There are campsites available from {start} to {end} 😊""",
                """{emoji} {park_name} ({park_id}): {current} site(s) available out of {maximum} site(s)""",
                """  * Site {site_id1} is available on the following dates:""",
                """    * {start1} -> {end1}""",
                """  * Site {site_id2} is available on the following dates:""",
                """    * {start2} -> {end2}""",
            ]
        ).format(
            start=start_date.strftime(DateFormat.INPUT_DATE_FORMAT.value),
            end=end_date.strftime(DateFormat.INPUT_DATE_FORMAT.value),
            emoji=Emoji.SUCCESS.value,
            park_name=park_name,
            park_id=park_id,
            current=current,
            maximum=maximum,
            site_id1=site_id1,
            site_id2=site_id2,
            start1=site1_date["start"],
            start2=site2_date["start"],
            end1=site1_date["end"],
            end2=site2_date["end"],
        )

        info_by_park_id = {
            park_id: (
                current,
                maximum,
                {site_id1: [site1_date], site_id2: [site2_date]},
                park_name,
            )
        }
        output, _ = cli.generate_human_output(
            info_by_park_id, start_date, end_date, True
        )
        self.assertEqual(output, expected)

    def testGenerateOutputToHuman_SiteOutputWithNoAvailabilities(self):
        start_date = TypeConverter.date("2022-06-01")
        end_date = TypeConverter.date("2022-07-01")
        park_name = "SOME PARK"
        park_id = 1
        current = 0
        maximum = 3

        expected = "\n".join(
            [
                """There are no campsites available 😢""",
                """{emoji} {park_name} ({park_id}): {current} site(s) available out of {maximum} site(s)""",
            ]
        ).format(
            start=start_date.strftime(DateFormat.INPUT_DATE_FORMAT.value),
            end=end_date.strftime(DateFormat.INPUT_DATE_FORMAT.value),
            emoji=Emoji.FAILURE.value,
            park_name=park_name,
            park_id=park_id,
            current=current,
            maximum=maximum,
        )

        info_by_park_id = {park_id: (current, maximum, {}, park_name)}
        output, _ = cli.generate_human_output(
            info_by_park_id, start_date, end_date, True
        )
        self.assertEqual(output, expected)


if __name__ == "__main__":
    unittest.main()
