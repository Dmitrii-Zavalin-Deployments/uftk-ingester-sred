import csv
from datetime import datetime
from pathlib import Path
from PIL import Image
import pytest

import universal_field_toolkit_ingester_sred as ingester


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def create_dummy_image(path: Path, size=(10, 10), color=(100, 150, 200)):
    img = Image.new("RGB", size, color)
    img.save(path)


# ---------------------------------------------------------
# load_image
# ---------------------------------------------------------

def test_load_image_reads_image(tmp_path):
    img_path = tmp_path / "test.jpg"
    create_dummy_image(img_path)
    img = ingester.load_image(str(img_path))
    assert isinstance(img, Image.Image)
    assert img.size == (10, 10)


# ---------------------------------------------------------
# extract_exif
# ---------------------------------------------------------

def test_extract_exif_no_exif():
    class DummyImage:
        def _getexif(self):
            return None

    img = DummyImage()
    exif = ingester.extract_exif(img)
    assert exif == {}


def test_extract_exif_with_data():
    class DummyImage:
        def _getexif(self):
            return {0x010F: "CameraBrand", 9999: "CustomValue"}

    img = DummyImage()
    exif = ingester.extract_exif(img)
    assert exif["Make"] == "CameraBrand"
    assert exif[9999] == "CustomValue"


# ---------------------------------------------------------
# normalize_metadata
# ---------------------------------------------------------

def test_normalize_metadata_returns_placeholders():
    meta = ingester.normalize_metadata({"anything": "value"})
    assert meta["timestamp"] == "..."
    assert meta["date"] == "..."
    assert meta["time_of_day"] == "..."
    assert meta["gps"] == "..."


# ---------------------------------------------------------
# generate_observation_id
# ---------------------------------------------------------

def test_generate_observation_id(monkeypatch):
    class DummyDateTime:
        @classmethod
        def now(cls):
            return datetime(2024, 1, 2, 3, 4, 5)

    monkeypatch.setattr(ingester, "datetime", DummyDateTime)
    obs_id = ingester.generate_observation_id()
    assert obs_id == "OBS-20240102-001"


# ---------------------------------------------------------
# manual_entry_prompt
# ---------------------------------------------------------

def test_manual_entry_prompt_structure():
    data = ingester.manual_entry_prompt()
    assert data["timestamp"] == "..."
    assert data["date"] == "..."
    assert data["time_of_day"] == "..."
    assert data["gps"] == "..."
    assert data["notes"] == ""
    assert data["human_influence_score"] == 0
    assert data["human_influence_note"] == ""


# ---------------------------------------------------------
# create_csv_row
# ---------------------------------------------------------

def test_create_csv_row_full_metadata():
    obs_id = "OBS-TEST"
    metadata = {
        "timestamp": "t",
        "date": "d",
        "time_of_day": "night",
        "gps": "coords",
        "notes": "note",
        "human_influence_score": 5,
        "human_influence_note": "footprints",
    }
    row = ingester.create_csv_row(obs_id, metadata, "photo_ingested.jpg", "photo")

    assert row["Observation_ID"] == obs_id
    assert row["Photo_Filename"] == "photo_ingested.jpg"
    assert row["Observation_Type"] == "photo"
    assert row["Timestamp"] == "t"
    assert row["Date"] == "d"
    assert row["Time_Of_Day"] == "night"
    assert row["GPS"] == "coords"
    assert row["Notes"] == "note"
    assert row["Human_Influence_Score"] == 5
    assert row["Human_Influence_Note"] == "footprints"


def test_create_csv_row_missing_optional_fields():
    obs_id = "OBS-TEST"
    metadata = {
        "timestamp": "t",
        "date": "d",
        "time_of_day": "day",
        "gps": "coords",
    }
    row = ingester.create_csv_row(obs_id, metadata, "file.jpg", "photo")

    assert row["Human_Influence_Score"] == 0
    assert row["Human_Influence_Note"] == ""
    assert row["Notes"] == ""


# ---------------------------------------------------------
# append_to_csv
# ---------------------------------------------------------

def test_append_to_csv_creates_file_with_header(tmp_path, monkeypatch):
    csv_path = tmp_path / "field_data.csv"
    monkeypatch.setattr(ingester, "FIELD_DATA_CSV", str(csv_path))

    row = {
        "Observation_ID": "OBS-1",
        "Photo_Filename": "a.jpg",
        "Observation_Type": "photo",
        "Timestamp": "t",
        "Date": "d",
        "Time_Of_Day": "morning",
        "GPS": "g",
        "Human_Influence_Score": 1,
        "Human_Influence_Note": "note",
        "Notes": "n",
    }

    ingester.append_to_csv(row)

    assert csv_path.is_file()
    with csv_path.open() as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 1
    assert rows[0]["Observation_ID"] == "OBS-1"


def test_append_to_csv_appends_rows(tmp_path, monkeypatch):
    csv_path = tmp_path / "field_data.csv"
    monkeypatch.setattr(ingester, "FIELD_DATA_CSV", str(csv_path))

    row1 = {
        "Observation_ID": "OBS-1",
        "Photo_Filename": "a.jpg",
        "Observation_Type": "photo",
        "Timestamp": "t1",
        "Date": "d1",
        "Time_Of_Day": "morning",
        "GPS": "g1",
        "Human_Influence_Score": 1,
        "Human_Influence_Note": "note1",
        "Notes": "n1",
    }
    row2 = dict(row1, Observation_ID="OBS-2", Photo_Filename="b.jpg")

    ingester.append_to_csv(row1)
    ingester.append_to_csv(row2)

    with csv_path.open() as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 2
    assert rows[0]["Observation_ID"] == "OBS-1"
    assert rows[1]["Observation_ID"] == "OBS-2"



