#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

echo "== Amazon Fashion Pipeline: Quick Start =="
echo "This runs a small CSV-only demo with 3 keywords and 8 products per keyword."
echo

python -m pip install -r requirements.txt

QUERIES="bucket hat,denim jacket,floral dress"
ITEMS_PER_QUERY=8
PAGES=1
RUN_ID="$(date +%Y%m%d_%H%M%S)"
SCRAPE_DIR="scraped/quick_start_${RUN_ID}"
ANALYSIS_DIR="analysis/quick_start_${RUN_ID}"

echo "== Step 1: Scrape small demo data =="
python scrape_latest_amazon.py \
  --queries "${QUERIES}" \
  --items-per-query "${ITEMS_PER_QUERY}" \
  --pages "${PAGES}" \
  --delay 0.8 \
  --no-images \
  --out-dir "${SCRAPE_DIR}"

BATCH_CSV="$(ls -t "${SCRAPE_DIR}"/amazon_fashion_batch_*.csv | head -1)"
echo "Batch CSV: ${BATCH_CSV}"

echo
echo "== Step 2: Clean data =="
python clean_amazon_data.py "${BATCH_CSV}" --out-dir "${SCRAPE_DIR}/cleaned"
CLEANED_CSV="$(ls -t "${SCRAPE_DIR}"/cleaned/*_rating_cleaned.csv | head -1)"
echo "Cleaned CSV: ${CLEANED_CSV}"

echo
echo "== Step 3: Analyze trends with CRITIC =="
python analyze_trends.py "${CLEANED_CSV}" --out-dir "${ANALYSIS_DIR}"

echo
echo "== Step 4: Generate brand recommendations =="
python brand_recommendations.py \
  "${ANALYSIS_DIR}/trend_scores_all_dimensions.csv" \
  --products-csv "${CLEANED_CSV}" \
  --out-dir "${ANALYSIS_DIR}/recommendations"

echo
echo "== Done =="
echo "Trend report:"
echo "  ${ANALYSIS_DIR}/trend_analysis_report.md"
echo "Brand recommendations:"
echo "  ${ANALYSIS_DIR}/recommendations/brand_recommendations.md"
echo "CSV recommendations:"
echo "  ${ANALYSIS_DIR}/recommendations/brand_recommendations.csv"
