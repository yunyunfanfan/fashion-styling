import argparse
from datetime import datetime
from pathlib import Path

import pandas as pd


REQUIRED_NUMERIC_FIELDS = ["rating_numeric", "number_of_ratings_numeric"]
MANUAL_LABEL_FIELDS = [
    "derived_style",
    "derived_scene",
    "derived_colour",
    "derived_material",
    "derived_pattern",
]


def load_data(input_csv):
    return pd.read_csv(input_csv)


def drop_missing_rating_rows(df):
    before = len(df)
    cleaned = df.dropna(subset=REQUIRED_NUMERIC_FIELDS).copy()
    after = len(cleaned)
    return cleaned, before - after


def normalize_missing_labels(df):
    cleaned = df.copy()
    for field in MANUAL_LABEL_FIELDS:
        if field in cleaned:
            cleaned[field] = cleaned[field].fillna("unknown")
            cleaned[field] = cleaned[field].replace("", "unknown")
    return cleaned


def export_manual_label_template(df, template_path):
    template_path.parent.mkdir(parents=True, exist_ok=True)
    mask = False
    for field in MANUAL_LABEL_FIELDS:
        if field in df:
            mask = mask | (df[field].fillna("unknown") == "unknown")

    columns = [
        "asin",
        "query",
        "brand_name",
        "product_name",
        "image_url",
        *MANUAL_LABEL_FIELDS,
        "manual_note",
    ]
    available_columns = [column for column in columns if column in df.columns or column == "manual_note"]
    template = df.loc[mask, [column for column in available_columns if column != "manual_note"]].copy()
    template["manual_note"] = ""
    template.to_csv(template_path, index=False)
    return len(template)


def apply_manual_labels(df, manual_labels_csv):
    manual_path = Path(manual_labels_csv)
    manual = pd.read_csv(manual_path)
    if "asin" not in manual.columns:
        raise ValueError("Manual label file must contain an 'asin' column.")

    cleaned = df.copy()
    cleaned = cleaned.set_index("asin", drop=False)
    manual = manual.set_index("asin", drop=False)

    updated_cells = 0
    for asin, row in manual.iterrows():
        if asin not in cleaned.index:
            continue
        for field in MANUAL_LABEL_FIELDS:
            if field not in manual.columns or field not in cleaned.columns:
                continue
            value = row[field]
            if pd.isna(value) or str(value).strip() in {"", "unknown"}:
                continue
            cleaned.loc[asin, field] = str(value).strip()
            updated_cells += 1

    return cleaned.reset_index(drop=True), updated_cells


def write_quality_report(
    input_csv,
    output_csv,
    df_before,
    df_after,
    removed_rows,
    report_path,
    manual_labels_csv=None,
    updated_manual_cells=0,
    manual_template_path=None,
    manual_template_rows=0,
):
    report_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Amazon Data Cleaning Report",
        "",
        f"Generated at: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## Files",
        "",
        f"- Input: `{input_csv}`",
        f"- Output: `{output_csv}`",
        "",
        "## Step 1: Remove Products Without Rating Signals",
        "",
        "Rows are removed if either field is missing:",
        "",
        "- `rating_numeric`",
        "- `number_of_ratings_numeric`",
        "",
        "## Row Counts",
        "",
        f"- Rows before cleaning: {len(df_before)}",
        f"- Rows removed: {removed_rows}",
        f"- Rows after cleaning: {len(df_after)}",
        "",
        "## Manual Labeling",
        "",
        f"- Manual label file: `{manual_labels_csv}`" if manual_labels_csv else "- Manual label file: not used",
        f"- Manual label cells updated: {updated_manual_cells}",
        f"- Manual label template: `{manual_template_path}`" if manual_template_path else "- Manual label template: not exported",
        f"- Manual label template rows: {manual_template_rows}",
        "",
        "## Missing Values After Cleaning",
        "",
        "```text",
        df_after.isna().sum().to_string(),
        "```",
        "",
        "## Rows Per Query After Cleaning",
        "",
        "```text",
        df_after["query"].value_counts().to_string() if "query" in df_after else "query column not found",
        "```",
    ]

    report_path.write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Clean Amazon fashion trend data.")
    parser.add_argument("input_csv", help="Path to the Amazon CSV file to clean")
    parser.add_argument(
        "--out-dir",
        default="scraped/cleaned",
        help="Directory for cleaned CSV and quality report",
    )
    parser.add_argument(
        "--manual-labels",
        help="Optional CSV with manually corrected derived labels keyed by asin",
    )
    parser.add_argument(
        "--export-manual-template",
        action="store_true",
        help="Export a CSV template for rows whose derived labels contain unknown values",
    )
    args = parser.parse_args()

    input_csv = Path(args.input_csv)
    output_dir = Path(args.out_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    output_csv = output_dir / f"{input_csv.stem}_rating_cleaned.csv"
    report_path = output_dir / f"{input_csv.stem}_cleaning_report.md"
    manual_template_path = output_dir / f"{input_csv.stem}_manual_label_template.csv"

    df_before = load_data(input_csv)
    df_after, removed_rows = drop_missing_rating_rows(df_before)
    df_after = normalize_missing_labels(df_after)

    updated_manual_cells = 0
    if args.manual_labels:
        df_after, updated_manual_cells = apply_manual_labels(df_after, args.manual_labels)

    manual_template_rows = 0
    if args.export_manual_template:
        manual_template_rows = export_manual_label_template(df_after, manual_template_path)

    df_after.to_csv(output_csv, index=False)

    write_quality_report(
        input_csv=input_csv,
        output_csv=output_csv,
        df_before=df_before,
        df_after=df_after,
        removed_rows=removed_rows,
        report_path=report_path,
        manual_labels_csv=args.manual_labels,
        updated_manual_cells=updated_manual_cells,
        manual_template_path=manual_template_path if args.export_manual_template else None,
        manual_template_rows=manual_template_rows,
    )

    print(f"Rows before cleaning: {len(df_before)}")
    print(f"Rows removed: {removed_rows}")
    print(f"Rows after cleaning: {len(df_after)}")
    print(f"Manual label cells updated: {updated_manual_cells}")
    if args.export_manual_template:
        print(f"Saved manual label template to {manual_template_path}")
    print(f"Saved cleaned CSV to {output_csv}")
    print(f"Saved cleaning report to {report_path}")


if __name__ == "__main__":
    main()
