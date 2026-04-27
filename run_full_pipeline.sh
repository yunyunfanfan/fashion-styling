#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

USE_IMAGES=1
USE_GLM_LABELS=0
USE_GLM_REPORT=0
MODEL="${GLM_MODEL:-glm-4.6v-flash}"
ITEMS_PER_QUERY="${ITEMS_PER_QUERY:-50}"
PAGES="${PAGES:-2}"
DELAY="${DELAY:-2.0}"

for arg in "$@"; do
  case "$arg" in
    --no-images)
      USE_IMAGES=0
      ;;
    --use-glm-labels)
      USE_GLM_LABELS=1
      ;;
    --use-glm-report)
      USE_GLM_REPORT=1
      ;;
    --text-only-glm)
      MODEL="glm-4-flash-250414"
      ;;
    *)
      echo "Unknown argument: $arg" >&2
      echo "Supported: --no-images --use-glm-labels --use-glm-report --text-only-glm" >&2
      exit 1
      ;;
  esac
done

echo "== Amazon Fashion Pipeline: Full Run =="
echo "Items per query: ${ITEMS_PER_QUERY}"
echo "Pages per query: ${PAGES}"
echo "Request delay: ${DELAY}s"
echo "Download images: ${USE_IMAGES}"
echo "Use GLM labels: ${USE_GLM_LABELS}"
echo "Use GLM report: ${USE_GLM_REPORT}"
echo "GLM model: ${MODEL}"
echo

python -m pip install -r requirements.txt

RUN_ID="$(date +%Y%m%d_%H%M%S)"
SCRAPE_DIR="scraped/full_${RUN_ID}"
ANALYSIS_DIR="analysis/full_${RUN_ID}"

echo "== Step 1: Scrape Amazon data =="
SCRAPE_ARGS=(
  --items-per-query "${ITEMS_PER_QUERY}"
  --pages "${PAGES}"
  --delay "${DELAY}"
  --out-dir "${SCRAPE_DIR}"
)
if [[ "${USE_IMAGES}" -eq 0 ]]; then
  SCRAPE_ARGS+=(--no-images)
fi
python scrape_latest_amazon.py "${SCRAPE_ARGS[@]}"

BATCH_CSV="$(ls -t "${SCRAPE_DIR}"/amazon_fashion_batch_*.csv | head -1)"
echo "Batch CSV: ${BATCH_CSV}"

echo
echo "== Step 2: Clean data =="
python clean_amazon_data.py "${BATCH_CSV}" --out-dir "${SCRAPE_DIR}/cleaned" --export-manual-template
CLEANED_CSV="$(ls -t "${SCRAPE_DIR}"/cleaned/*_rating_cleaned.csv | head -1)"
echo "Cleaned CSV: ${CLEANED_CSV}"

ANALYSIS_INPUT="${CLEANED_CSV}"

if [[ "${USE_GLM_LABELS}" -eq 1 ]]; then
  echo
  echo "== Step 3: Fill unknown labels with GLM =="
  if [[ -z "${ZHIPUAI_API_KEY:-}" ]]; then
    echo "ZHIPUAI_API_KEY is not set. Cannot run GLM labeling." >&2
    exit 1
  fi

  GLM_ARGS=(
    "${CLEANED_CSV}"
    --model "${MODEL}"
    --max-retries 6
    --retry-delay 20
  )
  if [[ "${MODEL}" == "glm-4-flash-250414" ]]; then
    GLM_ARGS+=(--no-remote-image)
  fi
  python fill_labels_with_glm.py "${GLM_ARGS[@]}"
  ANALYSIS_INPUT="${CLEANED_CSV%.*}_glm_labeled.csv"
else
  echo
  echo "== Step 3: Skip GLM label completion =="
fi

echo
echo "== Step 4: Analyze trends with CRITIC =="
python analyze_trends.py "${ANALYSIS_INPUT}" --out-dir "${ANALYSIS_DIR}"

echo
echo "== Step 5: Generate brand recommendations =="
RECOMMEND_ARGS=(
  "${ANALYSIS_DIR}/trend_scores_all_dimensions.csv"
  --products-csv "${ANALYSIS_INPUT}"
  --out-dir "${ANALYSIS_DIR}/recommendations"
)
if [[ "${USE_GLM_REPORT}" -eq 1 ]]; then
  if [[ -z "${ZHIPUAI_API_KEY:-}" ]]; then
    echo "ZHIPUAI_API_KEY is not set. Cannot run GLM report generation." >&2
    exit 1
  fi
  RECOMMEND_ARGS+=(--use-glm --model "${MODEL}")
fi
python brand_recommendations.py "${RECOMMEND_ARGS[@]}"

echo
echo "== Done =="
echo "Scraped data:"
echo "  ${BATCH_CSV}"
echo "Cleaned data:"
echo "  ${CLEANED_CSV}"
if [[ "${USE_GLM_LABELS}" -eq 1 ]]; then
  echo "GLM-labeled data:"
  echo "  ${ANALYSIS_INPUT}"
fi
echo "Trend report:"
echo "  ${ANALYSIS_DIR}/trend_analysis_report.md"
echo "Brand recommendations:"
echo "  ${ANALYSIS_DIR}/recommendations/brand_recommendations.md"
echo "CSV recommendations:"
echo "  ${ANALYSIS_DIR}/recommendations/brand_recommendations.csv"
