import argparse
import csv
import re
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus, urljoin

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

from extract_amazon_product_video import PLACEHOLDER, extract_product_video


BASE_URL = "https://www.amazon.in"
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-IN,en;q=0.9",
}

DEFAULT_FASHION_QUERIES = [
    "bucket hat",
    "denim jacket",
    "floral dress",
    "striped shirt",
    "oversized hoodie",
    "cargo pants",
    "knit cardigan",
    "platform shoes",
    "linen shirt",
    "pleated skirt",
    "leather jacket",
    "wide leg jeans",
]

FIELDNAMES = [
    "scrape_date",
    "source",
    "query",
    "page",
    "page_position",
    "result_rank",
    "is_sponsored",
    "asin",
    "brand_name",
    "product_name",
    "price",
    "currency",
    "price_numeric",
    "rating",
    "rating_numeric",
    "number_of_ratings",
    "number_of_ratings_numeric",
    "derived_gender",
    "derived_style",
    "derived_scene",
    "derived_colour",
    "derived_material",
    "derived_pattern",
    "product_url",
    "image_url",
    "local_image_path",
    "has_product_video",
    "video_count_detected",
    "video_thumbnail_url",
    "video_url",
    "local_video_path",
    "local_video_thumbnail_path",
    "local_video_cover_path",
    "local_video_frame_paths",
    "video_frame_extraction_status",
    "video_extraction_status",
]


def clean_text(value):
    if not value:
        return ""
    aria_label = value.get("aria-label")
    if aria_label:
        return " ".join(aria_label.split())
    return " ".join(value.get_text(" ", strip=True).split())


def parse_price(price_text):
    if not price_text:
        return "", ""
    currency = "INR" if "₹" in price_text else ""
    numeric = re.sub(r"[^0-9.]", "", price_text)
    return currency, numeric


def parse_rating(rating_text):
    match = re.search(r"([0-9.]+)", rating_text or "")
    return match.group(1) if match else ""


def parse_count(count_text):
    if not count_text:
        return ""
    return re.sub(r"[^0-9]", "", count_text)


def infer_metadata(text, query):
    text_lower = f"{query} {text}".lower()

    colors = [
        "black",
        "white",
        "blue",
        "denim",
        "grey",
        "gray",
        "green",
        "red",
        "pink",
        "brown",
        "beige",
        "khaki",
        "yellow",
        "purple",
        "orange",
        "navy",
        "cream",
        "multi",
    ]
    materials = [
        "cotton",
        "denim",
        "polyester",
        "leather",
        "linen",
        "wool",
        "knit",
        "canvas",
        "fleece",
        "silk",
        "synthetic",
    ]
    patterns = [
        "solid",
        "striped",
        "stripe",
        "floral",
        "printed",
        "embroidered",
        "check",
        "checked",
        "plaid",
        "graphic",
        "reversible",
    ]

    gender = ""
    if any(word in text_lower for word in ["women", "womens", "woman", "ladies", "girl"]):
        gender = "women"
    elif any(word in text_lower for word in ["men", "mens", "man", "boys"]):
        gender = "men"
    elif "unisex" in text_lower:
        gender = "unisex"

    style = ""
    if any(word in text_lower for word in ["casual", "street", "oversized", "hoodie"]):
        style = "casual"
    elif any(word in text_lower for word in ["formal", "office", "business"]):
        style = "formal"
    elif any(word in text_lower for word in ["sport", "gym", "running", "training"]):
        style = "sporty"
    elif any(word in text_lower for word in ["party", "glitter", "sequin"]):
        style = "party"
    elif any(word in text_lower for word in ["classic", "regular", "basic"]):
        style = "basic"

    scene = ""
    if any(word in text_lower for word in ["beach", "sun", "summer", "travel", "vacation"]):
        scene = "vacation"
    elif any(word in text_lower for word in ["office", "formal", "business"]):
        scene = "work"
    elif any(word in text_lower for word in ["outdoor", "hiking", "travel"]):
        scene = "outdoor"
    elif any(word in text_lower for word in ["party", "club"]):
        scene = "party"
    elif any(word in text_lower for word in ["casual", "daily"]):
        scene = "daily wear"

    def first_match(options):
        for option in options:
            if option in text_lower:
                return option
        return ""

    return {
        "derived_gender": gender or "unknown",
        "derived_style": style or "unknown",
        "derived_scene": scene or "unknown",
        "derived_colour": first_match(colors) or "unknown",
        "derived_material": first_match(materials) or "unknown",
        "derived_pattern": first_match(patterns) or "unknown",
    }


def build_search_url(query, page):
    return f"{BASE_URL}/s?k={quote_plus(query)}&page={page}"


def safe_name(value):
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def parse_search_page(html, query, page):
    soup = BeautifulSoup(html, "lxml")
    items = soup.select('div[data-component-type="s-search-result"][data-asin]')
    rows = []

    for page_position, item in enumerate(items, start=1):
        asin = item.get("data-asin", "").strip()
        if not asin:
            continue

        title_el = item.select_one("h2 span")
        link_el = item.select_one("a.a-link-normal.s-no-outline") or item.select_one("h2 a")
        image_el = item.select_one("img.s-image")
        price_el = item.select_one("span.a-price span.a-offscreen")
        rating_el = item.select_one("span.a-icon-alt")
        review_el = (
            item.select_one("span.a-size-base.s-underline-text")
            or item.select_one("a[href*='customerReviews'] span.a-size-base")
            or item.select_one("a[href*='customerReviews']")
            or item.select_one("span[aria-label$='ratings']")
        )

        brand_name = clean_text(title_el)
        image_alt = image_el.get("alt", "").strip() if image_el else ""
        title = image_alt if len(image_alt) > len(brand_name) else brand_name
        is_sponsored = title.lower().startswith("sponsored ad -")
        if is_sponsored:
            title = title.split("-", 1)[1].strip()
        product_url = urljoin(BASE_URL, link_el.get("href", "")) if link_el else ""
        image_url = image_el.get("src", "") if image_el else ""
        price = clean_text(price_el)
        currency, price_numeric = parse_price(price)
        rating = clean_text(rating_el)
        review_count = clean_text(review_el)
        metadata = infer_metadata(title, query)

        if not title and not image_url:
            continue

        rows.append(
            {
                "scrape_date": datetime.now().isoformat(timespec="seconds"),
                "source": "amazon.in",
                "query": query,
                "page": page,
                "page_position": page_position,
                "result_rank": "",
                "is_sponsored": "yes" if is_sponsored else "no",
                "asin": asin,
                "brand_name": brand_name,
                "product_name": title,
                "price": price,
                "currency": currency,
                "price_numeric": price_numeric,
                "rating": rating or "not_available",
                "rating_numeric": parse_rating(rating),
                "number_of_ratings": review_count or "not_available",
                "number_of_ratings_numeric": parse_count(review_count),
                **metadata,
                "product_url": product_url,
                "image_url": image_url,
                "local_image_path": "",
                "has_product_video": "not_checked",
                "video_count_detected": "",
                "video_thumbnail_url": PLACEHOLDER,
                "video_url": PLACEHOLDER,
                "local_video_path": PLACEHOLDER,
                "local_video_thumbnail_path": PLACEHOLDER,
                "local_video_cover_path": PLACEHOLDER,
                "local_video_frame_paths": PLACEHOLDER,
                "video_frame_extraction_status": "not_checked",
                "video_extraction_status": "not_checked",
            }
        )

    return rows


def download_image(session, image_url, output_path, delay):
    if not image_url:
        return False

    response = session.get(image_url, timeout=20)
    response.raise_for_status()
    output_path.write_bytes(response.content)
    time.sleep(delay)
    return True


def save_rows(rows, output_csv):
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    with output_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def scrape_query(session, query, pages, max_items, delay):
    rows = []
    for page in tqdm(range(1, pages + 1), desc=f"Pages for {query}", unit="page"):
        url = build_search_url(query, page)
        print(f"Scraping {query!r}, page {page}: {url}")

        response = session.get(url, timeout=30)
        response.raise_for_status()

        page_rows = parse_search_page(response.text, query, page)
        print(f"Found {len(page_rows)} products for {query!r} on page {page}")
        rows.extend(page_rows)

        if max_items and len(rows) >= max_items:
            rows = rows[:max_items]
            break

        time.sleep(delay)

    seen = set()
    unique_rows = []
    for row in rows:
        dedupe_key = row["asin"] or row["product_url"] or row["image_url"]
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        unique_rows.append(row)

    if max_items:
        unique_rows = unique_rows[:max_items]

    for result_rank, row in enumerate(unique_rows, start=1):
        row["result_rank"] = result_rank

    return unique_rows


def download_images_for_rows(session, rows, image_dir, delay):
    image_dir.mkdir(parents=True, exist_ok=True)
    for index, row in enumerate(tqdm(rows, desc=f"Downloading {image_dir.name}", unit="image"), start=1):
        image_path = image_dir / f"{index:04d}_{row['asin'] or 'unknown'}.jpg"
        try:
            if download_image(session, row["image_url"], image_path, delay):
                row["local_image_path"] = str(image_path)
        except requests.RequestException as error:
            print(f"Could not download image for {row['asin']}: {error}")
            row["local_image_path"] = "download_failed"


def enrich_rows_with_product_videos(
    session,
    rows,
    video_dir,
    download_videos,
    delay,
    max_videos,
    extract_video_frames,
    video_frame_count,
):
    video_dir.mkdir(parents=True, exist_ok=True)
    checked = 0
    downloaded_or_found = 0

    for row in tqdm(rows, desc=f"Checking {video_dir.name}", unit="product"):
        if max_videos and downloaded_or_found >= max_videos:
            row["has_product_video"] = "not_checked"
            row["video_extraction_status"] = "video_limit_reached"
            continue

        try:
            video_record = extract_product_video(
                session=session,
                asin_or_url=row["asin"] or row["product_url"],
                out_dir=video_dir,
                download=download_videos,
                delay=delay,
                extract_frames=extract_video_frames,
                frame_count=video_frame_count,
            )
            for field in [
                "has_product_video",
                "video_count_detected",
                "video_thumbnail_url",
                "video_url",
                "local_video_path",
                "local_video_thumbnail_path",
                "local_video_cover_path",
                "local_video_frame_paths",
                "video_frame_extraction_status",
                "video_extraction_status",
            ]:
                row[field] = video_record[field]
            checked += 1
            if video_record["has_product_video"] == "yes":
                downloaded_or_found += 1
        except (requests.RequestException, ValueError) as error:
            print(f"Could not extract video for {row['asin']}: {error}")
            row["has_product_video"] = "unknown"
            row["video_count_detected"] = ""
            row["video_thumbnail_url"] = PLACEHOLDER
            row["video_url"] = PLACEHOLDER
            row["local_video_path"] = PLACEHOLDER
            row["local_video_thumbnail_path"] = PLACEHOLDER
            row["local_video_cover_path"] = PLACEHOLDER
            row["local_video_frame_paths"] = PLACEHOLDER
            row["video_frame_extraction_status"] = "extract_failed"
            row["video_extraction_status"] = "extract_failed"

        time.sleep(delay)

    print(f"Checked videos for {checked} products; found videos for {downloaded_or_found}.")


def main():
    parser = argparse.ArgumentParser(description="Scrape current Amazon India search results.")
    parser.add_argument("--query", help="Single search keyword, for example: bucket hat")
    parser.add_argument(
        "--queries",
        help="Comma-separated keywords for batch mode. Defaults to built-in fashion keywords.",
    )
    parser.add_argument("--pages", type=int, default=2, help="Number of search result pages to scrape per keyword")
    parser.add_argument("--max-items", type=int, default=0, help="Maximum products to keep. 0 means no limit")
    parser.add_argument("--items-per-query", type=int, default=50, help="Products to keep for each keyword in batch mode")
    parser.add_argument("--delay", type=float, default=2.0, help="Delay between requests in seconds")
    parser.add_argument("--out-dir", default="scraped", help="Output directory")
    parser.add_argument("--no-images", action="store_true", help="Only save CSV, do not download images")
    parser.add_argument(
        "--include-videos",
        action="store_true",
        help="Visit product detail pages and extract product video metadata.",
    )
    parser.add_argument(
        "--download-videos",
        action="store_true",
        help="Download product videos when --include-videos is enabled.",
    )
    parser.add_argument(
        "--no-video-frames",
        action="store_true",
        help="Do not extract cover/frame images from downloaded videos.",
    )
    parser.add_argument(
        "--video-frame-count",
        type=int,
        default=3,
        help="Number of inner frames to extract from each downloaded video.",
    )
    parser.add_argument(
        "--max-videos",
        type=int,
        default=0,
        help="Maximum number of products with videos to keep checking/downloading per query. 0 means no limit.",
    )
    parser.add_argument(
        "--single-only",
        action="store_true",
        help="Only save the per-query CSV files, not the combined batch CSV.",
    )
    args = parser.parse_args()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(args.out_dir)

    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)

    if args.query:
        queries = [args.query]
        items_per_query = args.max_items
    elif args.queries:
        queries = [query.strip() for query in args.queries.split(",") if query.strip()]
        items_per_query = args.items_per_query
    else:
        queries = DEFAULT_FASHION_QUERIES
        items_per_query = args.items_per_query

    batch_rows = []
    for query in tqdm(queries, desc="Scraping queries", unit="query"):
        query_slug = safe_name(query)
        query_rows = scrape_query(
            session=session,
            query=query,
            pages=args.pages,
            max_items=items_per_query,
            delay=args.delay,
        )

        if not args.no_images:
            image_dir = output_dir / f"images_{query_slug}_{timestamp}"
            download_images_for_rows(session, query_rows, image_dir, args.delay)
            print(f"Saved images for {query!r} to {image_dir}")
        else:
            for row in query_rows:
                row["local_image_path"] = "not_downloaded"

        if args.include_videos:
            video_dir = output_dir / f"videos_{query_slug}_{timestamp}"
            enrich_rows_with_product_videos(
                session=session,
                rows=query_rows,
                video_dir=video_dir,
                download_videos=args.download_videos,
                delay=args.delay,
                max_videos=args.max_videos,
                extract_video_frames=args.download_videos and not args.no_video_frames,
                video_frame_count=args.video_frame_count,
            )

        query_csv = output_dir / f"amazon_{query_slug}_{timestamp}.csv"
        save_rows(query_rows, query_csv)
        print(f"Saved {len(query_rows)} products for {query!r} to {query_csv}")
        batch_rows.extend(query_rows)

    if len(queries) > 1 and not args.single_only:
        combined_csv = output_dir / f"amazon_fashion_batch_{timestamp}.csv"
        save_rows(batch_rows, combined_csv)
        print(f"Saved {len(batch_rows)} total products to {combined_csv}")


if __name__ == "__main__":
    main()
