import argparse
import json
import os
from pathlib import Path

import pandas as pd
from tqdm import tqdm


DIMENSION_LABELS = {
    "derived_style": "style",
    "derived_scene": "scene",
    "derived_colour": "colour",
    "derived_material": "material",
    "derived_pattern": "pattern",
}

MISSING_IMAGE_MARKERS = {"", "nan", "none", "not_downloaded", "download_failed", "not_available"}


def classify_tier(score, strong_threshold, weak_threshold):
    if score >= strong_threshold:
        return "Strong Trend"
    if score >= weak_threshold:
        return "Weak Signal"
    return "Noise"


def action_for_tier(tier):
    if tier == "Strong Trend":
        return "Prioritize in assortment and creative direction."
    if tier == "Weak Signal":
        return "Test with limited drops and monitor cross-source validation."
    return "Do not prioritize; keep as background signal."


def evidence_sentence(row):
    return (
        f"{row['label']} appears in {int(row['item_count'])} products, "
        f"covers {int(row['query_count'])} query categories, "
        f"has average rating {row['avg_rating']:.2f}, "
        f"and total rating count {int(row['total_rating_count'])}."
    )


def product_direction_for_strong(label_map):
    material = label_map.get("derived_material", [])
    style = label_map.get("derived_style", [])
    scene = label_map.get("derived_scene", [])
    colour = label_map.get("derived_colour", [])
    pattern = label_map.get("derived_pattern", [])

    material_text = ", ".join(material[:3]) if material else "validated materials"
    style_text = ", ".join(style[:3]) if style else "validated styles"
    scene_text = ", ".join(scene[:3]) if scene else "target wearing scenes"
    colour_text = ", ".join(colour[:3]) if colour else "commercial colours"
    pattern_text = ", ".join(pattern[:3]) if pattern else "visual patterns"

    return (
        f"Develop products around {material_text} with {style_text} positioning, "
        f"for {scene_text}. Use {colour_text} as colour direction and "
        f"{pattern_text} as visual surface direction."
    )


def insight_for_item(item):
    label = item["label"]
    dimension = item["dimension"]
    if dimension == "derived_style":
        return f"`{label}` is the strongest styling signal, suggesting demand for broadly wearable fashion directions."
    if dimension == "derived_scene":
        return f"`{label}` appears as a strong wearing-context signal, indicating where customers may imagine using these products."
    if dimension == "derived_colour":
        return f"`{label}` is a strong colour signal and can guide palette selection for product and visual merchandising."
    if dimension == "derived_material":
        return f"`{label}` is a strong material signal and can guide fabric, texture, and sourcing decisions."
    if dimension == "derived_pattern":
        return f"`{label}` is a strong visual-surface signal and can guide print, graphic, and pattern direction."
    return f"`{label}` is a strong trend signal in `{dimension}`."


def product_direction_for_item(item):
    label = item["label"]
    dimension = item["dimension"]
    if dimension == "derived_style":
        return f"Build a capsule around {label} styling, using the strongest material, colour, and pattern signals as supporting design choices."
    if dimension == "derived_scene":
        return f"Design products and campaign styling around {label} occasions, with product names and visuals that make the usage context explicit."
    if dimension == "derived_colour":
        return f"Use {label} as a hero colour or recurring accent across selected categories."
    if dimension == "derived_material":
        return f"Prioritize {label} in core products and test adjacent categories where the material supports comfort, durability, or seasonal relevance."
    if dimension == "derived_pattern":
        return f"Develop {label} surface treatments across relevant products, then validate with social and community sources."
    return "Translate this signal into a small test collection and validate against other sources."


def brand_recommendation_for_item(item):
    tier_action = "Prioritize this signal in assortment planning, product naming, and campaign visuals."
    validation = "Validate with TikTok and Telegram before treating it as a cross-platform trend."
    return f"{tier_action} {validation}"


def risk_note_for_item(item):
    return (
        "This signal is based on Amazon search results, which may be affected by sponsored placement, "
        "platform ranking, keyword choice, and incomplete automatic labels. Treat it as an e-commerce signal, "
        "not a final market truth."
    )


def build_recommendation_rows(trends, strong_threshold, weak_threshold):
    rows = []
    for _, row in tqdm(trends.iterrows(), total=len(trends), desc="Building recommendation rows", unit="trend"):
        tier = classify_tier(row["trend_score"], strong_threshold, weak_threshold)
        rows.append(
            {
                "dimension": row["dimension"],
                "dimension_name": DIMENSION_LABELS.get(row["dimension"], row["dimension"]),
                "label": row["label"],
                "trend_score": row["trend_score"],
                "tier": tier,
                "item_count": row["item_count"],
                "avg_rating": row["avg_rating"],
                "total_rating_count": row["total_rating_count"],
                "query_count": row["query_count"],
                "evidence": evidence_sentence(row),
                "recommendation": action_for_tier(tier),
            }
        )
    return pd.DataFrame(rows)


def display_image_path(product, markdown_dir):
    local_path = str(product.get("local_image_path", "") or "").strip()
    if local_path.lower() not in MISSING_IMAGE_MARKERS:
        local = Path(local_path)
        if not local.is_absolute():
            local = Path.cwd() / local
        if local.exists():
            try:
                return os.path.relpath(local, start=markdown_dir)
            except ValueError:
                return str(local)

    image_url = str(product.get("image_url", "") or "").strip()
    if image_url.lower() not in MISSING_IMAGE_MARKERS:
        return image_url
    return ""


def sample_products(product_df, dimension, label, limit=3):
    if product_df is None or dimension not in product_df.columns:
        return []
    subset = product_df[product_df[dimension].astype(str) == str(label)].copy()
    if subset.empty:
        return []
    subset = subset.sort_values(["result_rank", "number_of_ratings_numeric"], ascending=[True, False])
    columns = [
        "query",
        "brand_name",
        "product_name",
        "rating_numeric",
        "number_of_ratings_numeric",
        "image_url",
        "local_image_path",
    ]
    columns = [column for column in columns if column in subset.columns]
    return subset[columns].head(limit).to_dict("records")


def build_context(recommendations, product_df):
    strong = recommendations[recommendations["tier"] == "Strong Trend"].copy()
    label_map = {
        dimension: strong[strong["dimension"] == dimension]["label"].head(5).tolist()
        for dimension in DIMENSION_LABELS
    }

    top_evidence = []
    strong_top = strong.sort_values("trend_score", ascending=False).head(12)
    for _, row in tqdm(strong_top.iterrows(), total=len(strong_top), desc="Collecting trend evidence", unit="trend"):
        top_evidence.append(
            {
                "dimension": row["dimension"],
                "dimension_name": row["dimension_name"],
                "label": row["label"],
                "trend_score": round(row["trend_score"], 3),
                "item_count": int(row["item_count"]),
                "avg_rating": round(row["avg_rating"], 2),
                "total_rating_count": int(row["total_rating_count"]),
                "query_count": int(row["query_count"]),
                "sample_products": sample_products(product_df, row["dimension"], row["label"], limit=3),
            }
        )

    return {
        "tier_rules": {
            "Strong Trend": "trend_score >= 0.6",
            "Weak Signal": "0.3 <= trend_score < 0.6",
            "Noise": "trend_score < 0.3",
        },
        "strong_labels_by_dimension": label_map,
        "combined_product_direction": product_direction_for_strong(label_map),
        "top_evidence": top_evidence,
    }


def local_markdown(recommendations, context, markdown_dir):
    lines = [
        "# Amazon Brand Recommendations",
        "",
        "## Tier Rules",
        "",
        "- Strong Trend: `trend_score >= 0.6`",
        "- Weak Signal: `0.3 <= trend_score < 0.6`",
        "- Noise: `trend_score < 0.3`",
        "",
        "## Combined Product Direction",
        "",
        context["combined_product_direction"],
        "",
        "## Strong Trend Labels",
        "",
    ]

    strong = recommendations[recommendations["tier"] == "Strong Trend"].sort_values("trend_score", ascending=False)
    grouped_strong = list(strong.groupby("dimension", sort=False))
    for dimension, subset in tqdm(grouped_strong, desc="Writing strong trend labels", unit="dimension"):
        lines.append(f"### {dimension}")
        lines.append("")
        lines.append("```text")
        lines.append(subset[["label", "trend_score", "item_count", "avg_rating", "total_rating_count", "query_count"]].to_string(index=False))
        lines.append("```")
        lines.append("")

    lines.extend(["## Trend Recommendations", ""])
    for item in tqdm(context["top_evidence"][:8], desc="Writing recommendation sections", unit="trend"):
        lines.append(f"### {item['label']} ({item['dimension_name']})")
        lines.append("")
        lines.append("#### Trend Insight")
        lines.append("")
        lines.append(insight_for_item(item))
        lines.append("")
        lines.append("#### Evidence")
        lines.append("")
        lines.append(
            f"- Trend score: `{item['trend_score']}`\n"
            f"- Product count: `{item['item_count']}`\n"
            f"- Query coverage: `{item['query_count']}` categories\n"
            f"- Average rating: `{item['avg_rating']}`\n"
            f"- Total rating count: `{item['total_rating_count']}`"
        )
        lines.append("")
        lines.append("Visual evidence:")
        for product_index, product in enumerate(item["sample_products"], start=1):
            title = f"{product['query']}: {product['brand_name']} - {product['product_name']}"
            image_path = display_image_path(product, markdown_dir)
            if image_path:
                lines.append("")
                lines.append(f"![{title}]({image_path})")
            lines.append(f"- {title}")
            lines.append(
                f"  Rating: {product['rating_numeric']}; rating count: {int(product['number_of_ratings_numeric'])}"
            )
            if image_path:
                lines.append(f"  Image: {image_path}")
            if product.get("image_url"):
                lines.append(f"  Source image URL: {product['image_url']}")
        lines.append("")
        lines.append("#### Product Direction")
        lines.append("")
        lines.append(product_direction_for_item(item))
        lines.append("")
        lines.append("#### Brand Recommendation")
        lines.append("")
        lines.append(brand_recommendation_for_item(item))
        lines.append("")
        lines.append("#### Risk / Validation Note")
        lines.append("")
        lines.append(risk_note_for_item(item))
        lines.append("")

    return "\n".join(lines)


def glm_markdown(context, model, api_key_env, markdown_dir):
    from zhipuai import ZhipuAI

    api_key = os.getenv(api_key_env)
    if not api_key:
        raise SystemExit(f"Missing API key. Set it with: export {api_key_env}=...")

    prompt = (
        "You are writing a fashion trend intelligence report for a university data curation project.\n"
        "Use the provided Amazon trend context to generate a polished brand recommendations markdown report.\n"
        "Requirements:\n"
        "1. Explain the tier rules.\n"
        "2. Convert multi-dimensional Strong Trend labels into concrete product directions.\n"
        "3. Use evidence from trend scores, item counts, query coverage, ratings, and sample products.\n"
        "4. Mention that Amazon data is one e-commerce source and should later be validated with TikTok and Telegram.\n"
        "5. Do not invent labels outside the context.\n"
        "6. Include product images using Markdown image syntax. Use each product's display_image_path field when available.\n"
        "7. For each trend section, use exactly these subheadings:\n"
        "   - Trend Insight\n"
        "   - Evidence\n"
        "   - Product Direction\n"
        "   - Brand Recommendation\n"
        "   - Risk / Validation Note\n"
        "8. Keep the writing evidence-based and concise.\n\n"
        f"Context JSON:\n{json.dumps(context, ensure_ascii=False)}"
    )

    client = ZhipuAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    return response.choices[0].message.content


def main():
    parser = argparse.ArgumentParser(description="Generate brand recommendations from trend scores.")
    parser.add_argument("trend_scores_csv", help="analysis/trend_scores_all_dimensions.csv")
    parser.add_argument("--products-csv", default="scraped/cleaned/amazon_fashion_batch_20260426_211640_rating_cleaned.csv")
    parser.add_argument("--out-dir", default="analysis")
    parser.add_argument("--strong-threshold", type=float, default=0.6)
    parser.add_argument("--weak-threshold", type=float, default=0.3)
    parser.add_argument("--use-glm", action="store_true", help="Use GLM to generate brand_recommendations.md")
    parser.add_argument("--model", default="glm-4.6v-flash")
    parser.add_argument("--api-key-env", default="ZHIPUAI_API_KEY")
    args = parser.parse_args()

    trend_scores = pd.read_csv(args.trend_scores_csv)
    product_df = pd.read_csv(args.products_csv) if Path(args.products_csv).exists() else None
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    recommendations = build_recommendation_rows(
        trend_scores,
        strong_threshold=args.strong_threshold,
        weak_threshold=args.weak_threshold,
    )
    recommendations_csv = out_dir / "brand_recommendations.csv"
    recommendations.to_csv(recommendations_csv, index=False)

    context = build_context(recommendations, product_df)
    # Add display image paths that are relative to the markdown output directory.
    for item in tqdm(context["top_evidence"], desc="Preparing image paths", unit="trend"):
        for product in item["sample_products"]:
            product["display_image_path"] = display_image_path(product, out_dir)

    if args.use_glm:
        markdown = glm_markdown(context, model=args.model, api_key_env=args.api_key_env, markdown_dir=out_dir)
    else:
        markdown = local_markdown(recommendations, context, markdown_dir=out_dir)

    recommendations_md = out_dir / "brand_recommendations.md"
    recommendations_md.write_text(markdown, encoding="utf-8")

    print(f"Saved recommendations CSV to {recommendations_csv}")
    print(f"Saved recommendations report to {recommendations_md}")
    print(f"Strong trends: {(recommendations['tier'] == 'Strong Trend').sum()}")
    print(f"Weak signals: {(recommendations['tier'] == 'Weak Signal').sum()}")
    print(f"Noise labels: {(recommendations['tier'] == 'Noise').sum()}")


if __name__ == "__main__":
    main()
