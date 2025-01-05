import unittest
from click.testing import CliRunner
from camp.cli import main  # Import the main function from your camping.py script


class TestCampingArgParser(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()
        self.start_date = ["--start-date", "2025-01-30"]
        self.end_date = ["--end-date", "2025-01-31"]
        self.parks = ["--parks", "111"]
        self.default_args = []
        self.default_args.extend(self.start_date)
        self.default_args.extend(self.end_date)
        self.default_args.extend(self.parks)

    def testCampsiteIdsWithMoreThanOneCampgroundIdThrowsException(self):
        args = ["--campsite-ids", "333", "--parks", "1", "2"]
        args.extend(self.start_date)
        args.extend(self.end_date)
        result = self.runner.invoke(main, args)
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("Error", result.output)

    def testAcceptsMultipleCampsiteIds(self):
        args = ["--campsite-ids", "333", "444"]
        args.extend(self.default_args)
        result = self.runner.invoke(main, args)
        self.assertEqual(result.exit_code, 0)

    def testAcceptsMultipleCampgroundIds(self):
        args = ["--parks", "333", "444"]
        args.extend(self.start_date)
        args.extend(self.end_date)
        result = self.runner.invoke(main, args)
        self.assertEqual(result.exit_code, 0)


if __name__ == "__main__":
    unittest.main()
