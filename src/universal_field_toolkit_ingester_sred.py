import argparse
import os
import csv
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS

# -----------------------------
# Utility functions
# -----------------------------

def load_image(path):
    return Image.open(path)

def extract_exif(image):
    exif_data = {}
    raw = image._getexif() or {}
    for tag, value in raw.items():
        decoded = TAGS.get(tag, tag)
        exif_data[decoded] = value
    return exif_data

def normalize_metadata(exif):
    # Extract timestamp, GPS, etc.
    # Convert to ISO, extract hour/day-of-year
    return {
        "timestamp": "...",
        "date": "...",
        "time_of_day": "...",
        "gps": "...",
    }

def generate_observation_id():
    today = datetime.now().strftime("%Y%m%d")
    # Incremental counter logic can be added here
    return f"OBS-{today}-001"

def manual_entry_prompt():
    # Ask user for date, time, notes, etc.
    return {
        "timestamp": "...",
        "date": "...",
        "time_of_day": "...",
        "gps": None,
        "notes": "",
        "human_influence_score": 0,
        "human_influence_note": "",
    }

def create_csv_row(obs_id, metadata, filename, observation_type):
    return {
        "Observation_ID": obs_id,
        "Photo_Filename": filename,
        "Observation_Type": observation_type,
        "Timestamp": metadata["timestamp"],
        "Date": metadata["date"],
        "Time_Of_Day": metadata["time_of_day"],
        "GPS": metadata["gps"],
        "Human_Influence_Score": metadata.get("human_influence_score", 0),
        "Human_Influence_Note": metadata.get("human_influence_note", ""),
        "Notes": metadata.get("notes", "")
    }

def append_to_csv(row, csv_path="field_data.csv"):
    file_exists = os.path.isfile(csv_path)
    with open(csv_path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

# -----------------------------
# Main
# -----------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--photo", help="Path to photo")
    parser.add_argument("--manual", action="store_true")
    args = parser.parse_args()

    obs_id = generate_observation_id()

    if args.manual:
        metadata = manual_entry_prompt()
        row = create_csv_row(obs_id, metadata, "MANUAL_ENTRY", "manual")
        append_to_csv(row)
        return

    image = load_image(args.photo)
    exif = extract_exif(image)
    metadata = normalize_metadata(exif)

    row = create_csv_row(obs_id, metadata, os.path.basename(args.photo), "photo")
    append_to_csv(row)

if __name__ == "__main__":
    main()



