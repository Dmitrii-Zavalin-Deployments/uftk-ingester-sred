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

WORKING_DIR = os.environ.get("WORKING_DIR", "/data/testing-input-output")
FIELD_DATA_CSV = os.environ.get("FIELD_DATA_CSV", os.path.join(WORKING_DIR, "field_data.csv"))

# ---------------------------------------------------------
# Utility functions
# ---------------------------------------------------------

def load_image(path):
    return Image.open(path)

def extract_exif(image):
    """Extract EXIF metadata and decode tag names."""
    exif_data = {}
    raw = image._getexif() or {}

    for tag, value in raw.items():
        decoded = TAGS.get(tag, tag)
        exif_data[decoded] = value

    print("📸 EXIF keys found:", list(exif_data.keys()))
    return exif_data

# ---------------------------------------------------------
# Metadata normalization (RAW GPSINFO ONLY)
# ---------------------------------------------------------

def normalize_metadata(exif):
    """Extract timestamp, time, part_of_day, RAW GPSINFO, camera info, and confidence score."""

    timestamp = exif.get("DateTimeOriginal") or exif.get("DateTime")

    # Default placeholders required by tests
    date = "..."
    time_of_day = "..."
    part_of_day = "..."

    if timestamp:
        try:
            dt = datetime.strptime(timestamp, "%Y:%m:%d %H:%M:%S")
            date = dt.strftime("%Y-%m-%d")
            time_of_day = dt.strftime("%H:%M:%S")

            hour = dt.hour
            if hour < 6:
                part_of_day = "night"
            elif hour < 12:
                part_of_day = "morning"
            elif hour < 18:
                part_of_day = "afternoon"
            else:
                part_of_day = "evening"

        except Exception:
            timestamp = "..."
    else:
        timestamp = "..."

    # ---------------------------------------------------------
    # GPS — store RAW GPSINFO block exactly as-is
    # ---------------------------------------------------------
    gps_info = exif.get("GPSInfo")
    print(f"GPSInfo: {gps_info}")

    gps = str(gps_info) if gps_info else "..."

    # Camera metadata
    camera_model = exif.get("Model", "...") or "..."
    exposure_time = exif.get("ExposureTime", "...") or "..."
    iso = exif.get("ISOSpeedRatings", "...") or "..."
    focal_length = exif.get("FocalLength", "...") or "..."

    # Confidence score
    score = 0
    if timestamp != "...": score += 1
    if gps != "...": score += 1
    if camera_model != "...": score += 1
    if iso != "...": score += 1
    if focal_length != "...": score += 1

    confidence = f"{score}/5"

    return {
        "timestamp": timestamp,
        "date": date,
        "time_of_day": time_of_day,
        "part_of_day": part_of_day,
        "gps": gps,  # RAW GPSINFO stored here
        "camera_model": camera_model,
        "exposure_time": str(exposure_time),
        "iso": str(iso),
        "focal_length": str(focal_length),
        "confidence": confidence,
    }

# ---------------------------------------------------------
# Observation ID
# ---------------------------------------------------------

def generate_observation_id():
    today = datetime.now().strftime("%Y%m%d")
    return f"OBS-{today}-001"

# ---------------------------------------------------------
# Manual entry (tests require "..." placeholders)
# ---------------------------------------------------------

def manual_entry_prompt():
    return {
        "timestamp": "...",
        "date": "...",
        "time_of_day": "...",
        "part_of_day": "...",
        "gps": "...",
        "camera_model": "...",
        "exposure_time": "...",
        "iso": "...",
        "focal_length": "...",
        "confidence": "...",
        "notes": "",
        "human_influence_score": 0,
        "human_influence_note": "",
    }

# ---------------------------------------------------------
# CSV row creation
# ---------------------------------------------------------

def create_csv_row(obs_id, metadata, filename, observation_type):
    return {
        "Observation_ID": obs_id,
        "Photo_Filename": filename,
        "Observation_Type": observation_type,
        "Timestamp": metadata.get("timestamp", "..."),
        "Date": metadata.get("date", "..."),
        "Time_Of_Day": metadata.get("time_of_day", "..."),
        "Part_Of_Day": metadata.get("part_of_day", "..."),
        "GPS": metadata.get("gps", "..."),
        "Camera_Model": metadata.get("camera_model", "..."),
        "Exposure_Time": metadata.get("exposure_time", "..."),
        "ISO": metadata.get("iso", "..."),
        "Focal_Length": metadata.get("focal_length", "..."),
        "Confidence": metadata.get("confidence", "..."),
        "Human_Influence_Score": metadata.get("human_influence_score", 0),
        "Human_Influence_Note": metadata.get("human_influence_note", ""),
        "Notes": metadata.get("notes", "")
    }

# ---------------------------------------------------------
# CSV writer
# ---------------------------------------------------------

def append_to_csv(row, csv_path=None):
    if csv_path is None:
        csv_path = FIELD_DATA_CSV

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
    obs_id = generate_observation_id()

    image = load_image(photo_path)
    exif = extract_exif(image)
    metadata = normalize_metadata(exif)

    base = os.path.basename(photo_path)
    name, ext = os.path.splitext(base)
    output_filename = f"{name}_ingested{ext}"
    output_path = os.path.join(WORKING_DIR, output_filename)

    shutil.copy2(photo_path, output_path)

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

    for filename in os.listdir(WORKING_DIR):
        path = os.path.join(WORKING_DIR, filename)
        if os.path.isfile(path) and filename.lower().endswith((".jpg", ".jpeg", ".png")):
            process_photo(path)

    print(f"🎉 Ingestion complete. Outputs written to {WORKING_DIR}")

if __name__ == "__main__":
    main()



