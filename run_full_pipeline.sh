#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

USE_IMAGES=1
USE_BRIXTON=1
USE_UNIQLO=1
USE_VIDEOS=0
DOWNLOAD_VIDEOS=0
USE_GLM_LABELS=0
USE_GLM_REPORT=0
MODEL="${GLM_MODEL:-glm-4.6v-flash}"
QUERIES="${QUERIES:-bucket hat,denim jacket,floral dress,striped shirt,oversized hoodie,cargo pants,knit cardigan,platform shoes,linen shirt,pleated skirt,leather jacket,wide leg jeans}"
ITEMS_PER_QUERY="${ITEMS_PER_QUERY:-50}"
PAGES="${PAGES:-2}"
DELAY="${DELAY:-2.0}"
MAX_VIDEOS="${MAX_VIDEOS:-0}"
VIDEO_FRAME_COUNT="${VIDEO_FRAME_COUNT:-3}"

for arg in "$@"; do
  case "$arg" in
    --no-images)
      USE_IMAGES=0
      ;;
    --no-brixton)
      USE_BRIXTON=0
      ;;
    --no-uniqlo)
      USE_UNIQLO=0
      ;;
    --use-glm-labels)
      USE_GLM_LABELS=1
      ;;
    --use-glm-report)
      USE_GLM_REPORT=1
      ;;
    --include-videos)
      USE_VIDEOS=1
      ;;
    --download-videos)
      USE_VIDEOS=1
      DOWNLOAD_VIDEOS=1
      ;;
    --text-only-glm)
      MODEL="glm-4-flash-250414"
      ;;
    *)
      echo "Unknown argument: $arg" >&2
      echo "Supported: --no-images --no-brixton --no-uniqlo --include-videos --download-videos --use-glm-labels --use-glm-report --text-only-glm" >&2
      exit 1
      ;;
  esac
done

echo "== Amazon Fashion Pipeline: Full Run =="
echo "Queries: ${QUERIES}"
echo "Items per query: ${ITEMS_PER_QUERY}"
echo "Pages per query: ${PAGES}"
echo "Request delay: ${DELAY}s"
echo "Download images: ${USE_IMAGES}"
echo "Include Brixton source: ${USE_BRIXTON}"
echo "Include UNIQLO source: ${USE_UNIQLO}"
echo "Include videos: ${USE_VIDEOS}"
echo "Download videos and extract frames: ${DOWNLOAD_VIDEOS}"
echo "Max videos per query: ${MAX_VIDEOS}"
echo "Video frames per video: ${VIDEO_FRAME_COUNT}"
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
  --queries "${QUERIES}"
  --items-per-query "${ITEMS_PER_QUERY}"
  --pages "${PAGES}"
  --delay "${DELAY}"
  --out-dir "${SCRAPE_DIR}"
)
if [[ "${USE_IMAGES}" -eq 0 ]]; then
  SCRAPE_ARGS+=(--no-images)
fi
if [[ "${USE_VIDEOS}" -eq 1 ]]; then
  SCRAPE_ARGS+=(--include-videos --max-videos "${MAX_VIDEOS}")
fi
if [[ "${DOWNLOAD_VIDEOS}" -eq 1 ]]; then
  SCRAPE_ARGS+=(--download-videos --video-frame-count "${VIDEO_FRAME_COUNT}")
fi
python scrape_latest_amazon.py "${SCRAPE_ARGS[@]}"

AMAZON_CSV="$(ls -t "${SCRAPE_DIR}"/amazon_fashion_batch_*.csv | head -1)"
echo "Amazon CSV: ${AMAZON_CSV}"

if [[ "${USE_BRIXTON}" -eq 1 ]]; then
  echo
  echo "== Step 1b: Scrape Brixton data =="
  BRIXTON_DIR="${SCRAPE_DIR}/brixton"
  BRIXTON_ARGS=(--queries "${QUERIES}" --items-per-query "${ITEMS_PER_QUERY}" --out-dir "${BRIXTON_DIR}")
  if [[ "${USE_IMAGES}" -eq 1 ]]; then
    BRIXTON_ARGS+=(--download-images)
  fi
  python brixton/brixton_amazon_format_scraper.py "${BRIXTON_ARGS[@]}"
  BRIXTON_CSV="$(ls -t "${BRIXTON_DIR}"/brixton_fashion_batch_*.csv | head -1)"
  echo "Brixton CSV: ${BRIXTON_CSV}"

fi

if [[ "${USE_UNIQLO}" -eq 1 ]]; then
  echo
  echo "== Step 1c: Scrape UNIQLO data =="
  UNIQLO_DIR="${SCRAPE_DIR}/uniqlo"
  python -m playwright install chromium
  UNIQLO_ARGS=(
    --queries "${QUERIES}"
    --max-products-per-query "${ITEMS_PER_QUERY}"
    --max-total-products "$((ITEMS_PER_QUERY * 12))"
    --delay "${DELAY}"
    --keep-unrated
    --output-dir "${UNIQLO_DIR}"
  )
  if [[ "${USE_IMAGES}" -eq 1 ]]; then
    UNIQLO_ARGS+=(--download-images)
  fi
  python uniqlo/uniqlo_playwright_fashion_scraper_fixed.py \
    "${UNIQLO_ARGS[@]}"
  UNIQLO_CSV="$(ls -t "${UNIQLO_DIR}"/uniqlo_fashion_batch_*.csv | head -1)"
  echo "UNIQLO CSV: ${UNIQLO_CSV}"
fi

BATCH_CSV="${SCRAPE_DIR}/fashion_multisource_batch_${RUN_ID}.csv"
COMBINE_INPUTS=("${AMAZON_CSV}")
if [[ "${USE_BRIXTON}" -eq 1 ]]; then
  COMBINE_INPUTS+=("${BRIXTON_CSV}")
fi
if [[ "${USE_UNIQLO}" -eq 1 ]]; then
  COMBINE_INPUTS+=("${UNIQLO_CSV}")
fi
if [[ "${#COMBINE_INPUTS[@]}" -gt 1 ]]; then
  python combine_source_csvs.py "${COMBINE_INPUTS[@]}" --output-csv "${BATCH_CSV}"
else
  BATCH_CSV="${AMAZON_CSV}"
fi
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
echo "Amazon data:"
echo "  ${AMAZON_CSV}"
if [[ "${USE_BRIXTON}" -eq 1 ]]; then
  echo "Brixton data:"
  echo "  ${BRIXTON_CSV}"
fi
if [[ "${USE_UNIQLO}" -eq 1 ]]; then
  echo "UNIQLO data:"
  echo "  ${UNIQLO_CSV}"
fi
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
