import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from textwrap import dedent

from backend.uf_schedule import process_ics_file


def _write_ics(directory: Path, location: str, summary: str = "UF Event") -> Path:
    file_path = directory / "schedule.ics"
    file_path.write_text(
        dedent(
            f"""\
            BEGIN:VCALENDAR
            VERSION:2.0
            PRODID:-//CampusCompass//UnitTest//EN
            BEGIN:VEVENT
            SUMMARY:{summary}
            LOCATION:{location}
            DTSTART:20260305T130000Z
            DTEND:20260305T140000Z
            END:VEVENT
            END:VCALENDAR
            """
        ),
        encoding="utf-8",
    )
    return file_path


class UFScheduleTests(unittest.TestCase):
    def test_process_ics_file_maps_known_building_code(self):
        with TemporaryDirectory() as directory:
            file_path = _write_ics(Path(directory), "CSE 101")
            events = process_ics_file(str(file_path))

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["location_code"], "CSE")
        self.assertIn("campusmap.ufl.edu", events[0]["location_url"])

    def test_process_ics_file_returns_default_for_unknown_code(self):
        with TemporaryDirectory() as directory:
            file_path = _write_ics(Path(directory), "ZZZ 101")
            events = process_ics_file(str(file_path))

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["location_code"], "ZZZ")
        self.assertEqual(events[0]["location_url"], "No URL found for this location code")

    def test_process_ics_file_normalizes_lowercase_location_code(self):
        with TemporaryDirectory() as directory:
            file_path = _write_ics(Path(directory), "cse 201")
            events = process_ics_file(str(file_path))

        self.assertEqual(events[0]["location_code"], "CSE")
        self.assertIn("index/0042", events[0]["location_url"])


if __name__ == "__main__":
    unittest.main()
