"""Append-only CSV storage for experiment attempts."""

import csv
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable


CSV_COLUMNS = (
    "session_id",
    "random_seed",
    "trial_id",
    "participant_id",
    "timestamp_utc",
    "trial_order",
    "is_practice",
    "outcome",
    "task_type",
    "contrast_level",
    "interface_size",
    "brightness",
    "response",
    "response_detail",
    "response_time_seconds",
    "attempt_elapsed_seconds",
    "target_size",
    "target_diameter_pixels",
    "target_distance",
    "target_distance_pixels",
    "target_direction",
    "canvas_width_pixels",
    "canvas_height_pixels",
    "click_time_seconds",
    "incorrect_clicks",
    "ease_rating",
)

VALID_OUTCOMES = {"completed", "timed_out", "aborted"}
VALID_TASKS = {"identification", "target_hitting"}


class DataLogger:
    """Validate and append experiment attempts to the project CSV."""

    def __init__(self, path=None):
        project_dir = Path(__file__).resolve().parent
        self.path = Path(path) if path is not None else (
            project_dir / "data" / "performance_results.csv"
        )
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            with self.path.open("w", newline="", encoding="utf-8-sig") as file:
                csv.writer(file).writerow(CSV_COLUMNS)
        self._validate_header()

    def _validate_header(self):
        try:
            with self.path.open("r", newline="", encoding="utf-8-sig") as file:
                header = next(csv.reader(file), None)
        except OSError as error:
            raise OSError("Unable to read results file: {}".format(error)) from error
        if tuple(header or ()) != CSV_COLUMNS:
            raise ValueError(
                "The results CSV has an unexpected header. Back it up or move it "
                "before starting this version of the application."
            )

    @staticmethod
    def new_id():
        return str(uuid.uuid4())

    @staticmethod
    def timestamp_utc():
        return datetime.now(timezone.utc).isoformat(timespec="milliseconds")

    def _existing_trial_ids(self) -> Iterable[str]:
        with self.path.open("r", newline="", encoding="utf-8-sig") as file:
            for row in csv.DictReader(file):
                yield row.get("trial_id", "")

    def append(self, row: Dict[str, object]):
        missing = set(CSV_COLUMNS) - set(row)
        if missing:
            raise ValueError("CSV row is missing columns: {}".format(
                ", ".join(sorted(missing))
            ))
        if row["outcome"] not in VALID_OUTCOMES:
            raise ValueError("Invalid trial outcome.")
        if row["task_type"] not in VALID_TASKS:
            raise ValueError("Invalid task type.")
        if not str(row["trial_id"]).strip() or not str(row["session_id"]).strip():
            raise ValueError("Session and trial IDs are required.")
        if not str(row["participant_id"]).strip():
            raise ValueError("Participant ID is required.")
        try:
            brightness = int(row["brightness"])
        except (TypeError, ValueError) as error:
            raise ValueError("Brightness must be an integer from 0 to 100.") from error
        if brightness < 0 or brightness > 100:
            raise ValueError("Brightness must be an integer from 0 to 100.")
        if row["outcome"] == "completed":
            if row["ease_rating"] not in (1, 2, 3, 4, 5, "1", "2", "3", "4", "5"):
                raise ValueError("Completed trials require an ease rating from 1 to 5.")
            if row["task_type"] == "identification" and not row["response"]:
                raise ValueError("Completed identification trials require a response.")
            if row["task_type"] == "target_hitting" and not row["click_time_seconds"]:
                raise ValueError("Completed target trials require a successful click time.")
        elif not row["attempt_elapsed_seconds"]:
            raise ValueError("Aborted and timed-out attempts require elapsed time.")

        trial_id = str(row["trial_id"])
        if trial_id in set(self._existing_trial_ids()):
            return False
        try:
            with self.path.open("a", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=CSV_COLUMNS, extrasaction="raise")
                writer.writerow({column: row[column] for column in CSV_COLUMNS})
                file.flush()
                os.fsync(file.fileno())
        except OSError as error:
            raise OSError(
                "Unable to save results. Close the CSV in spreadsheet software "
                "and retry. {}".format(error)
            ) from error
        return True

    def rows_for_session(self, session_id):
        with self.path.open("r", newline="", encoding="utf-8-sig") as file:
            return [
                row for row in csv.DictReader(file)
                if row.get("session_id") == session_id
            ]
