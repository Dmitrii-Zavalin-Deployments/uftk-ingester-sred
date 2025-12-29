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
# process_photo
# ---------------------------------------------------------

def test_process_photo_copies_and_updates_csv(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(ingester, "WORKING_DIR", str(tmp_path))
    monkeypatch.setattr(ingester, "FIELD_DATA_CSV", str(tmp_path / "field_data.csv"))

    # deterministic observation ID
    class DummyDateTime:
        @classmethod
        def now(cls):
            return datetime(2024, 1, 2, 3, 4, 5)
    monkeypatch.setattr(ingester, "datetime", DummyDateTime)

    # create source image outside WORKING_DIR
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    src_img = src_dir / "photo.jpg"
    create_dummy_image(src_img)

    ingester.process_photo(str(src_img))

    # check ingested file
    ingested_path = tmp_path / "photo_ingested.jpg"
    assert ingested_path.is_file()

    # check CSV
    csv_path = tmp_path / "field_data.csv"
    with csv_path.open() as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 1
    row = rows[0]
    assert row["Observation_ID"] == "OBS-20240102-001"
    assert row["Photo_Filename"] == "photo_ingested.jpg"
    assert row["Observation_Type"] == "photo"

    captured = capsys.readouterr()
    assert "Ingested:" in captured.out


# ---------------------------------------------------------
# main() manual mode
# ---------------------------------------------------------

def test_main_manual_mode(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(ingester, "WORKING_DIR", str(tmp_path))
    monkeypatch.setattr(ingester, "FIELD_DATA_CSV", str(tmp_path / "field_data.csv"))

    class DummyDateTime:
        @classmethod
        def now(cls):
            return datetime(2024, 1, 2)
    monkeypatch.setattr(ingester, "datetime", DummyDateTime)

    # simulate CLI: --manual
    monkeypatch.setattr("sys.argv", ["prog", "--manual"])

    ingester.main()

    captured = capsys.readouterr()
    assert "Manual entry added" in captured.out

    csv_path = tmp_path / "field_data.csv"
    with csv_path.open() as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 1
    assert rows[0]["Observation_Type"] == "manual"
    assert rows[0]["Photo_Filename"] == "MANUAL_ENTRY"


# ---------------------------------------------------------
# main() auto mode
# ---------------------------------------------------------

def test_main_auto_mode_processes_only_images(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(ingester, "WORKING_DIR", str(tmp_path))
    monkeypatch.setattr(ingester, "FIELD_DATA_CSV", str(tmp_path / "field_data.csv"))

    class DummyDateTime:
        @classmethod
        def now(cls):
            return datetime(2024, 1, 2)
    monkeypatch.setattr(ingester, "datetime", DummyDateTime)

    # create files
    img1 = tmp_path / "img1.jpg"
    img2 = tmp_path / "img2.PNG"
    txt = tmp_path / "notes.txt"

    create_dummy_image(img1)
    create_dummy_image(img2)
    txt.write_text("ignore me")

    # simulate no --manual
    monkeypatch.setattr("sys.argv", ["prog"])

    ingester.main()

    captured = capsys.readouterr()
    assert "Ingestion complete" in captured.out

    # check CSV
    csv_path = tmp_path / "field_data.csv"
    with csv_path.open() as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 2
    filenames = {r["Photo_Filename"] for r in rows}
    assert "img1_ingested.jpg" in filenames
    assert "img2_ingested.PNG" in filenames

    # check ingested files
    assert (tmp_path / "img1_ingested.jpg").is_file()
    assert (tmp_path / "img2_ingested.PNG").is_file()
    assert not (tmp_path / "notes_ingested.txt").exists()



