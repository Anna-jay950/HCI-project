import csv
import tempfile
import unittest
from pathlib import Path

from data_logger import CSV_COLUMNS, DataLogger
from main import make_target_schedule, shade_color


def valid_identification_row():
    row = {column: "" for column in CSV_COLUMNS}
    row.update({
        "session_id": "session-1",
        "random_seed": 1234,
        "trial_id": "trial-1",
        "participant_id": "P001",
        "timestamp_utc": "2026-01-01T00:00:00+00:00",
        "trial_order": 1,
        "is_practice": "false",
        "outcome": "completed",
        "task_type": "identification",
        "contrast_level": "high",
        "interface_size": "medium",
        "brightness": 100,
        "response": "A vase",
        "response_time_seconds": "1.25",
        "ease_rating": 4,
    })
    return row


class DataLoggerTests(unittest.TestCase):
    def test_creates_header_and_appends_once(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data" / "results.csv"
            logger = DataLogger(path)
            row = valid_identification_row()
            self.assertTrue(logger.append(row))
            self.assertFalse(logger.append(row))
            with path.open(newline="", encoding="utf-8-sig") as file:
                records = list(csv.DictReader(file))
            self.assertEqual(len(records), 1)
            self.assertEqual(tuple(records[0].keys()), CSV_COLUMNS)
            self.assertEqual(records[0]["response"], "A vase")

    def test_rejects_unexpected_existing_header_without_overwriting(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "results.csv"
            path.write_text("old,header\nkeep,this\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                DataLogger(path)
            self.assertEqual(path.read_text(encoding="utf-8"), "old,header\nkeep,this\n")

    def test_validates_completed_trial_rating(self):
        with tempfile.TemporaryDirectory() as directory:
            logger = DataLogger(Path(directory) / "results.csv")
            row = valid_identification_row()
            row["ease_rating"] = ""
            with self.assertRaises(ValueError):
                logger.append(row)

    def test_target_schedule_has_three_repetitions_per_condition(self):
        schedule = make_target_schedule(12345)
        measured = [(size, distance) for size, distance, practice in schedule if not practice]
        self.assertEqual(len(schedule), 28)
        self.assertEqual(sum(1 for _, _, practice in schedule if practice), 1)
        counts = {
            condition: measured.count(condition)
            for condition in set(measured)
        }
        self.assertEqual(len(counts), 9)
        self.assertEqual(set(counts.values()), {3})

    def test_brightness_simulation_endpoints(self):
        self.assertEqual(shade_color("#ffffff", 0), "#595959")
        self.assertEqual(shade_color("#ffffff", 100), "#ffffff")


if __name__ == "__main__":
    unittest.main()
