#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

echo "== Multi-Source Fashion Pipeline: Quick Start =="
echo "This runs a small multi-style, query-matched demo with Amazon and Brixton data."
echo

python -m pip install -r requirements.txt

QUERIES="bucket hat,denim jacket,floral dress,cargo pants,linen shirt,platform shoes"
ITEMS_PER_QUERY=6
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

AMAZON_CSV="$(ls -t "${SCRAPE_DIR}"/amazon_fashion_batch_*.csv | head -1)"
echo "Amazon CSV: ${AMAZON_CSV}"

echo
echo "== Step 1b: Scrape Brixton query-matched data =="
BRIXTON_DIR="${SCRAPE_DIR}/brixton"
python brixton/brixton_amazon_format_scraper.py \
  --queries "${QUERIES}" \
  --items-per-query "${ITEMS_PER_QUERY}" \
  --download-images \
  --out-dir "${BRIXTON_DIR}"
BRIXTON_CSV="$(ls -t "${BRIXTON_DIR}"/brixton_fashion_batch_*.csv | head -1)"
echo "Brixton CSV: ${BRIXTON_CSV}"

BATCH_CSV="${SCRAPE_DIR}/fashion_multisource_quick_start_${RUN_ID}.csv"
python combine_source_csvs.py "${AMAZON_CSV}" "${BRIXTON_CSV}" --output-csv "${BATCH_CSV}"
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
echo "Amazon data:"
echo "  ${AMAZON_CSV}"
echo "Brixton data:"
echo "  ${BRIXTON_CSV}"
echo "Combined data:"
echo "  ${BATCH_CSV}"
echo "Trend report:"
echo "  ${ANALYSIS_DIR}/trend_analysis_report.md"
echo "Brand recommendations:"
echo "  ${ANALYSIS_DIR}/recommendations/brand_recommendations.md"
echo "CSV recommendations:"
echo "  ${ANALYSIS_DIR}/recommendations/brand_recommendations.csv"
