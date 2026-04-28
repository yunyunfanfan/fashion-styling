import argparse
from pathlib import Path

import pandas as pd

from scrape_latest_amazon import FIELDNAMES, PLACEHOLDER


VIDEO_DEFAULTS = {
    "has_product_video": "not_applicable",
    "video_count_detected": "",
    "video_thumbnail_url": PLACEHOLDER,
    "video_url": PLACEHOLDER,
    "local_video_path": PLACEHOLDER,
    "local_video_thumbnail_path": PLACEHOLDER,
    "local_video_cover_path": PLACEHOLDER,
    "local_video_frame_paths": PLACEHOLDER,
    "video_frame_extraction_status": "not_applicable",
    "video_extraction_status": "not_applicable",
}


def load_source_csv(path):
    df = pd.read_csv(path, keep_default_na=False)
    for column, value in VIDEO_DEFAULTS.items():
        if column not in df.columns:
            df[column] = value
    return df


def ordered_columns(frames):
    columns = list(FIELDNAMES)
    for df in frames:
        for column in df.columns:
            if column not in columns:
                columns.append(column)
    return columns


def combine_csvs(input_csvs, output_csv):
    frames = [load_source_csv(path) for path in input_csvs]
    columns = ordered_columns(frames)
    combined = pd.concat([df.reindex(columns=columns, fill_value="") for df in frames], ignore_index=True)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(output_csv, index=False)
    return combined


def main():
    parser = argparse.ArgumentParser(description="Combine Amazon-format source CSV files into one multi-source dataset.")
    parser.add_argument("input_csvs", nargs="+", help="Source CSV files to combine")
    parser.add_argument("--output-csv", required=True, help="Combined output CSV path")
    args = parser.parse_args()

    input_csvs = [Path(path) for path in args.input_csvs]
    output_csv = Path(args.output_csv)
    combined = combine_csvs(input_csvs, output_csv)

    print(f"Saved combined CSV to {output_csv}")
    print(f"Rows: {len(combined)}")
    if "source" in combined:
        print("Rows by source:")
        print(combined["source"].value_counts().to_string())


if __name__ == "__main__":
    main()
