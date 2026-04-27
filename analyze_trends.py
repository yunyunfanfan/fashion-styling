import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from tqdm import tqdm


DEFAULT_DIMENSIONS = [
    "derived_style",
    "derived_scene",
    "derived_colour",
    "derived_material",
    "derived_pattern",
]

CRITERIA = [
    "frequency_score",
    "rating_count_score",
    "rank_score",
    "cross_category_score",
]


def min_max_normalize(series):
    min_value = series.min()
    max_value = series.max()
    if pd.isna(min_value) or pd.isna(max_value) or max_value == min_value:
        return pd.Series(1.0, index=series.index)
    return (series - min_value) / (max_value - min_value)


def calculate_critic_weights(criteria_df):
    normalized = criteria_df.copy()
    for column in normalized.columns:
        normalized[column] = min_max_normalize(normalized[column].astype(float))

    if len(normalized) <= 1:
        return pd.Series(1 / len(CRITERIA), index=CRITERIA), normalized

    std = normalized.std(axis=0, ddof=0)
    corr = normalized.corr(method="pearson").fillna(0)
    conflict = (1 - corr).sum(axis=0)
    information = std * conflict

    if information.sum() == 0:
        weights = pd.Series(1 / len(information), index=information.index)
    else:
        weights = information / information.sum()

    return weights, normalized


def aggregate_dimension(df, dimension, include_unknown):
    working = df.copy()
    working[dimension] = working[dimension].fillna("unknown").astype(str).str.strip()
    if not include_unknown:
        working = working[working[dimension] != "unknown"]

    if working.empty:
        return pd.DataFrame(), pd.Series(dtype=float)

    total_rows = len(df)
    total_queries = df["query"].nunique()
    max_rank = max(df["result_rank"].max(), 1)

    grouped = working.groupby(dimension)
    result = grouped.agg(
        item_count=("asin", "count"),
        avg_rating=("rating_numeric", "mean"),
        avg_rating_count=("number_of_ratings_numeric", "mean"),
        total_rating_count=("number_of_ratings_numeric", "sum"),
        avg_rank=("result_rank", "mean"),
        query_count=("query", "nunique"),
    ).reset_index()

    result = result.rename(columns={dimension: "label"})
    result.insert(0, "dimension", dimension)

    result["frequency_score"] = result["item_count"] / total_rows
    result["rating_count_score"] = np.log1p(result["avg_rating_count"])
    result["rank_score"] = 1 - ((result["avg_rank"] - 1) / max(max_rank - 1, 1))
    result["cross_category_score"] = result["query_count"] / total_queries

    weights, normalized = calculate_critic_weights(result[CRITERIA])
    result["trend_score"] = normalized.mul(weights, axis=1).sum(axis=1)

    for criterion in CRITERIA:
        result[f"{criterion}_normalized"] = normalized[criterion]

    result = result.sort_values("trend_score", ascending=False).reset_index(drop=True)
    result["rank_in_dimension"] = result.index + 1
    return result, weights


def write_weights(weights_by_dimension, output_path):
    rows = []
    for dimension, weights in tqdm(weights_by_dimension.items(), desc="Writing CRITIC weights", unit="dimension"):
        row = {"dimension": dimension}
        row.update(weights.to_dict())
        rows.append(row)
    pd.DataFrame(rows).to_csv(output_path, index=False)


def write_report(df, all_results, weights_by_dimension, output_path, include_unknown):
    lines = [
        "# Amazon Trend Analysis Report",
        "",
        "## Input Summary",
        "",
        f"- Rows: {len(df)}",
        f"- Queries: {df['query'].nunique()}",
        f"- Include unknown labels: {include_unknown}",
        "",
        "## CRITIC Criteria",
        "",
        "- `frequency_score`: label frequency in all products",
        "- `rating_count_score`: log-normalized average rating count",
        "- `rank_score`: higher when products rank closer to the top",
        "- `cross_category_score`: label coverage across search queries",
        "",
        "## CRITIC Weights",
        "",
    ]

    for dimension, weights in tqdm(weights_by_dimension.items(), desc="Writing report weights", unit="dimension"):
        lines.append(f"### {dimension}")
        lines.append("")
        for criterion, value in weights.items():
            lines.append(f"- `{criterion}`: {value:.4f}")
        lines.append("")

    lines.extend(["## Top Trend Labels", ""])
    for dimension in tqdm(DEFAULT_DIMENSIONS, desc="Writing top labels", unit="dimension"):
        subset = all_results[all_results["dimension"] == dimension].head(10)
        lines.append(f"### {dimension}")
        lines.append("")
        if subset.empty:
            lines.append("No labels available.")
            lines.append("")
            continue
        lines.append("```text")
        lines.append(subset[["label", "trend_score", "item_count", "avg_rating", "total_rating_count", "query_count"]].to_string(index=False))
        lines.append("```")
        lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Analyze Amazon fashion trend labels with CRITIC weighting.")
    parser.add_argument(
        "input_csv",
        help="Cleaned Amazon CSV, usually scraped/cleaned/*_rating_cleaned.csv",
    )
    parser.add_argument("--out-dir", default="analysis", help="Output directory")
    parser.add_argument(
        "--include-unknown",
        action="store_true",
        help="Include unknown labels in trend scoring",
    )
    args = parser.parse_args()

    input_csv = Path(args.input_csv)
    output_dir = Path(args.out_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(input_csv)
    required = ["query", "asin", "rating_numeric", "number_of_ratings_numeric", "result_rank"]
    missing = [column for column in required if column not in df.columns]
    missing += [column for column in DEFAULT_DIMENSIONS if column not in df.columns]
    if missing:
        raise SystemExit(f"Input data is missing required columns: {', '.join(missing)}")

    if df[["rating_numeric", "number_of_ratings_numeric", "result_rank"]].isna().any().any():
        raise SystemExit(
            "Input data still has missing numeric fields. Run clean_amazon_data.py before analyze_trends.py."
        )

    results = []
    weights_by_dimension = {}
    for dimension in tqdm(DEFAULT_DIMENSIONS, desc="Analyzing dimensions", unit="dimension"):
        dimension_result, weights = aggregate_dimension(df, dimension, args.include_unknown)
        if not dimension_result.empty:
            dimension_result.to_csv(output_dir / f"trend_{dimension}.csv", index=False)
            results.append(dimension_result)
            weights_by_dimension[dimension] = weights

    if not results:
        raise SystemExit("No trend labels available after filtering.")

    all_results = pd.concat(results, ignore_index=True)
    all_results.to_csv(output_dir / "trend_scores_all_dimensions.csv", index=False)
    write_weights(weights_by_dimension, output_dir / "critic_weights.csv")
    write_report(
        df=df,
        all_results=all_results,
        weights_by_dimension=weights_by_dimension,
        output_path=output_dir / "trend_analysis_report.md",
        include_unknown=args.include_unknown,
    )

    print(f"Rows analyzed: {len(df)}")
    print(f"Dimensions analyzed: {len(weights_by_dimension)}")
    print(f"Saved trend scores to {output_dir / 'trend_scores_all_dimensions.csv'}")
    print(f"Saved CRITIC weights to {output_dir / 'critic_weights.csv'}")
    print(f"Saved report to {output_dir / 'trend_analysis_report.md'}")


if __name__ == "__main__":
    main()
