#!/usr/bin/env python3
"""
Convert agentic-kpi-assistant JSON data to CSV format for sustainability-langgraph
"""

import json
import csv
import os
from pathlib import Path

# Source and destination paths
SOURCE_DIR = Path("/Users/devesh.b.sharma/Astra Zeneca/agentic-kpi-assistant/backend/src/data/json")
DEST_DIR = Path("/Users/devesh.b.sharma/Astra Zeneca/sustainability-langgraph/backend/data")

def json_to_csv(json_path: Path, csv_path: Path):
    """Convert a JSON file to CSV"""
    with open(json_path, 'r') as f:
        data = json.load(f)

    if not data:
        print(f"  Skipping {json_path.name} - empty data")
        return

    # Get all unique keys across all records
    all_keys = set()
    for record in data:
        all_keys.update(record.keys())

    # Sort keys for consistent column order
    fieldnames = sorted(list(all_keys))

    csv_path.parent.mkdir(parents=True, exist_ok=True)

    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

    print(f"  Converted: {json_path.name} -> {csv_path.name} ({len(data)} records)")

def main():
    # KPI data
    kpi_source = SOURCE_DIR / "kpi"
    kpi_dest = DEST_DIR / "KPI"

    print("Converting KPI data...")
    for json_file in kpi_source.glob("*.json"):
        if json_file.name == "regenerate_data.py":
            continue
        csv_name = json_file.stem + ".csv"
        json_to_csv(json_file, kpi_dest / csv_name)

    # Master data
    master_source = SOURCE_DIR / "masterData"
    master_dest = DEST_DIR / "Master"

    print("\nConverting Master data...")
    for json_file in master_source.glob("*.json"):
        csv_name = json_file.stem + ".csv"
        json_to_csv(json_file, master_dest / csv_name)

    # Transaction data
    trans_source = SOURCE_DIR / "transactionData"
    trans_dest = DEST_DIR / "Transactional"

    print("\nConverting Transaction data...")
    for json_file in trans_source.glob("*.json"):
        csv_name = json_file.stem + ".csv"
        json_to_csv(json_file, trans_dest / csv_name)

    print("\nDone!")

if __name__ == "__main__":
    main()
