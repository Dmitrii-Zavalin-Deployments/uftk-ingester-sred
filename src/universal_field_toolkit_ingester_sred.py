import argparse
import os
import csv
import shutil
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS

# ---------------------------------------------------------
# Unified working directory for input and output
# ---------------------------------------------------------

WORKING_DIR = "/data/testing-input-output"
FIELD_DATA_CSV = os.path.join(WORKING_DIR, "field_data.csv")

# ---------------------------------------------------------
# Utility functions
# ---------------------------------------------------------

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
    # Placeholder normalization logic
    return {
        "timestamp": "...",
        "date": "...",
        "time_of_day": "...",
        "gps": "...",
    }

def generate_observation_id():
    today = datetime.now().strftime("%Y%m%d")
    return f"OBS-{today}-001"

def manual_entry_prompt():
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

def append_to_csv(row, csv_path=FIELD_DATA_CSV):
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    file_exists = os.path.isfile(csv_path)

    with open(csv_path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

# ---------------------------------------------------------
# Main ingestion logic
# ---------------------------------------------------------

def process_photo(photo_path):
    """Process a single photo: extract metadata, rename, copy forward."""
    obs_id = generate_observation_id()

    # Load and extract EXIF
    image = load_image(photo_path)
    exif = extract_exif(image)
    metadata = normalize_metadata(exif)

    # Prepare output filename
    base = os.path.basename(photo_path)
    name, ext = os.path.splitext(base)
    output_filename = f"{name}_ingested{ext}"
    output_path = os.path.join(WORKING_DIR, output_filename)

    # Copy image forward
    shutil.copy2(photo_path, output_path)

    # Write CSV row
    row = create_csv_row(obs_id, metadata, output_filename, "photo")
    append_to_csv(row)

    print(f"✓ Ingested: {photo_path} → {output_path}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manual", action="store_true")
    args = parser.parse_args()

    os.makedirs(WORKING_DIR, exist_ok=True)

    if args.manual:
        obs_id = generate_observation_id()
        metadata = manual_entry_prompt()
        row = create_csv_row(obs_id, metadata, "MANUAL_ENTRY", "manual")
        append_to_csv(row)
        print("✓ Manual entry added to field_data.csv")
        return

    # Process all photos in the working directory
    for filename in os.listdir(WORKING_DIR):
        path = os.path.join(WORKING_DIR, filename)
        if os.path.isfile(path) and filename.lower().endswith((".jpg", ".jpeg", ".png")):
            process_photo(path)

    print("🎉 Ingestion complete. Outputs written to /data/testing-input-output")

if __name__ == "__main__":
    main()



