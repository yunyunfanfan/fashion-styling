import csv
import mimetypes
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import requests


SOURCE = "www.brixton.com"
BASE_URL = "https://www.brixton.com"
PRODUCTS_URL = f"{BASE_URL}/products.json"
STAMPED_WIDGET_URL = "https://stamped.io/api/widget"
STAMPED_API_KEY = "pubkey-050MQKbS9PC61MxYCL1452FN5j50Xt"
STAMPED_STORE_URL = "197746"
CURRENCY = "USD"
LIMIT = 250
REVIEW_WORKERS = 8
PLACEHOLDER = "no_video"
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

COLUMNS = [
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

GENDER_TERMS = {
    "women": ["women", "woman", "female", "womens", "women's", "ladies", "girl"],
    "men": ["men", "man", "male", "mens", "men's", "boys"],
    "unisex": ["unisex"],
}

STYLE_TERMS = [
    "bucket",
    "hat",
    "cap",
    "beanie",
    "snapback",
    "fedora",
    "panama",
    "straw",
    "shirt",
    "tee",
    "t-shirt",
    "jacket",
    "hoodie",
    "pant",
    "short",
    "dress",
    "skirt",
    "swim",
    "bikini",
    "casual",
    "streetwear",
    "classic",
    "vintage",
    "western",
    "workwear",
]

SCENE_TERMS = {
    "vacation": ["vacation", "beach", "travel", "resort", "summer", "sunny"],
    "outdoor": ["outdoor", "hiking", "trail", "rain", "sun", "field"],
    "sports": ["sport", "active", "running", "training", "skate", "surf"],
    "work": ["work", "workwear", "office"],
    "party": ["party", "evening", "festival"],
}

COLOUR_TERMS = [
    "black",
    "white",
    "red",
    "blue",
    "green",
    "yellow",
    "pink",
    "purple",
    "orange",
    "brown",
    "grey",
    "gray",
    "navy",
    "cream",
    "beige",
    "tan",
    "ivory",
    "silver",
    "gold",
    "natural",
    "charcoal",
    "khaki",
    "olive",
]

MATERIAL_TERMS = [
    "cotton",
    "polyester",
    "nylon",
    "wool",
    "merino",
    "leather",
    "denim",
    "linen",
    "silk",
    "cashmere",
    "spandex",
    "elastane",
    "viscose",
    "fleece",
    "canvas",
    "straw",
    "felt",
    "corduroy",
]

PATTERN_TERMS = [
    "stripe",
    "striped",
    "floral",
    "plaid",
    "check",
    "checked",
    "print",
    "printed",
    "reversible",
    "embroidered",
    "logo",
    "solid",
    "tie dye",
    "leopard",
    "camo",
    "woven",
]


def normalize_text(value):
    if isinstance(value, list):
        value = " ".join(str(item) for item in value)
    return re.sub(r"\s+", " ", str(value or "")).strip().lower()


def safe_name(value):
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def query_tokens(query):
    return [token for token in re.findall(r"[a-z0-9]+", query.lower()) if token]


def product_search_text(product):
    return normalize_text(
        [
            product.get("title", ""),
            product.get("product_type", ""),
            product.get("vendor", ""),
            product.get("handle", ""),
            product.get("tags") or [],
        ]
    )


def query_score(item, query):
    text = product_search_text(item["product"])
    tokens = query_tokens(query)
    if not tokens:
        return 0
    token_hits = sum(1 for token in tokens if re.search(rf"\b{re.escape(token)}\b", text))
    phrase_bonus = len(tokens) if query.lower() in text else 0
    return token_hits + phrase_bonus


def select_items_for_query(items, query, max_items):
    scored = []
    for original_index, item in enumerate(items):
        score = query_score(item, query)
        if score > 0:
            scored.append((score, original_index, item))
    scored.sort(key=lambda value: (-value[0], value[1]))
    selected = [item for _, _, item in scored]
    return selected[:max_items] if max_items else selected


def first_match(text, terms):
    for term in terms:
        if re.search(rf"\b{re.escape(term)}\b", text):
            return term
    return ""


def derive_gender(text):
    for label, terms in GENDER_TERMS.items():
        if first_match(text, terms):
            return label
    return ""


def derive_from_map(text, term_map):
    for label, terms in term_map.items():
        if first_match(text, terms):
            return label
    return ""


def select_variant(product):
    variants = product.get("variants") or []
    for variant in variants:
        if variant.get("available"):
            return variant
    return variants[0] if variants else {}


def price_numeric(price):
    match = re.search(r"\d+(?:\.\d+)?", str(price or ""))
    return match.group(0) if match else ""


def product_image(product):
    images = product.get("images") or []
    return images[0].get("src", "") if images else ""


def image_extension(url, content_type=""):
    clean_url = url.split("?", 1)[0].lower()
    suffix = Path(clean_url).suffix
    if suffix in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
        return ".jpg" if suffix == ".jpeg" else suffix
    guessed = mimetypes.guess_extension(content_type.split(";", 1)[0].strip()) if content_type else ""
    return ".jpg" if guessed in {".jpe", ".jpeg"} else guessed or ".jpg"


def download_image(session, image_url, output_dir, product_id):
    if not image_url or not product_id:
        return ""
    output_dir.mkdir(parents=True, exist_ok=True)
    response = session.get(image_url, timeout=35)
    response.raise_for_status()
    ext = image_extension(image_url, response.headers.get("content-type", ""))
    path = output_dir / f"shopify_{product_id}{ext}"
    path.write_bytes(response.content)
    return str(path.resolve())


def product_url(product):
    handle = product.get("handle")
    return f"{BASE_URL}/products/{handle}" if handle else BASE_URL


def make_session():
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
            ),
            "Accept": "application/json,text/html,*/*",
            "Accept-Language": "en-US,en;q=0.9",
        }
    )
    return session


def fetch_products():
    session = make_session()
    products = []
    page = 1
    while True:
        response = session.get(PRODUCTS_URL, params={"limit": LIMIT, "page": page}, timeout=30)
        response.raise_for_status()
        data = response.json()
        page_products = data.get("products") or []
        if not page_products:
            break
        for page_position, product in enumerate(page_products, start=1):
            products.append({"page": page, "page_position": page_position, "product": product})
        print(f"products page {page}: {len(page_products)}")
        if len(page_products) < LIMIT:
            break
        page += 1
        time.sleep(0.4)
    return products


def fetch_stamped_summary(item):
    product = item["product"]
    variant = select_variant(product)
    session = make_session()
    params = {
        "productId": str(product.get("id", "")),
        "productName": product.get("title", "") or "",
        "productSKU": variant.get("sku", "") or "",
        "page": "1",
        "apiKey": STAMPED_API_KEY,
        "storeUrl": STAMPED_STORE_URL,
        "take": "1",
    }
    try:
        response = session.get(
            STAMPED_WIDGET_URL,
            params=params,
            timeout=35,
            headers={"Referer": product_url(product)},
        )
        response.raise_for_status()
        data = response.json()
        count = data.get("count")
        rating = data.get("rating")
        count_int = int(count) if count not in (None, "") else 0
        rating_float = float(rating) if rating not in (None, "") else 0.0
        if count_int <= 0:
            return product.get("id"), "", "", "", "", ""
        rating_text = f"{rating_float:.1f} out of 5 stars"
        return (
            product.get("id"),
            rating_text,
            f"{rating_float:.6g}",
            f"{count_int:,} ratings",
            str(count_int),
            "",
        )
    except Exception as exc:
        return product.get("id"), "", "", "", "", f"{type(exc).__name__}: {str(exc)[:160]}"


def fetch_all_review_summaries(items):
    review_by_id = {}
    errors = []
    done = 0
    with ThreadPoolExecutor(max_workers=REVIEW_WORKERS) as executor:
        futures = [executor.submit(fetch_stamped_summary, item) for item in items]
        for future in as_completed(futures):
            product_id, rating, rating_numeric, review_count, review_count_numeric, error = future.result()
            review_by_id[product_id] = {
                "rating": rating,
                "rating_numeric": rating_numeric,
                "number_of_ratings": review_count,
                "number_of_ratings_numeric": review_count_numeric,
            }
            if error:
                errors.append({"product_id": product_id, "error": error})
            done += 1
            if done % 50 == 0 or done == len(items):
                print(f"reviews checked: {done}/{len(items)}")
    return review_by_id, errors


def make_row(scrape_date, query, item, result_rank, review):
    product = item["product"]
    variant = select_variant(product)
    tags = product.get("tags") or []
    combined_text = normalize_text(
        [
            product.get("title", ""),
            product.get("product_type", ""),
            product.get("vendor", ""),
            tags,
        ]
    )
    price = str(variant.get("price", "") or "")
    product_id = product.get("id", "")

    return {
        "scrape_date": scrape_date,
        "source": SOURCE,
        "query": query,
        "page": item["page"],
        "page_position": item["page_position"],
        "result_rank": result_rank,
        "is_sponsored": "no",
        "asin": f"shopify_{product_id}" if product_id else "",
        "brand_name": product.get("vendor", "") or "Brixton",
        "product_name": product.get("title", "") or "",
        "price": price,
        "currency": CURRENCY,
        "price_numeric": price_numeric(price),
        "rating": review.get("rating", ""),
        "rating_numeric": review.get("rating_numeric", ""),
        "number_of_ratings": review.get("number_of_ratings", ""),
        "number_of_ratings_numeric": review.get("number_of_ratings_numeric", ""),
        "derived_gender": derive_gender(combined_text),
        "derived_style": first_match(combined_text, STYLE_TERMS),
        "derived_scene": derive_from_map(combined_text, SCENE_TERMS),
        "derived_colour": first_match(combined_text, COLOUR_TERMS),
        "derived_material": first_match(combined_text, MATERIAL_TERMS),
        "derived_pattern": first_match(combined_text, PATTERN_TERMS),
        "product_url": product_url(product),
        "image_url": product_image(product),
        "local_image_path": item.get("local_image_path", ""),
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


def write_csv(path, rows, columns):
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def download_image_for_item(session, item, image_dir, image_cache, errors):
    product = item["product"]
    product_id = product.get("id")
    if product_id in image_cache:
        return image_cache[product_id]
    try:
        image_path = download_image(session, product_image(product), image_dir, product_id)
    except requests.RequestException as exc:
        image_path = "download_failed"
        errors.append({"product_id": product_id, "error": f"image {type(exc).__name__}: {str(exc)[:160]}"})
    image_cache[product_id] = image_path
    return image_path


def unique_items(items):
    seen = set()
    result = []
    for item in items:
        product_id = item["product"].get("id")
        if product_id in seen:
            continue
        seen.add(product_id)
        result.append(item)
    return result


def parse_queries(args):
    if args.query:
        return [args.query], args.max_items
    if args.queries:
        queries = [query.strip() for query in args.queries.split(",") if query.strip()]
    else:
        queries = DEFAULT_FASHION_QUERIES
    return queries, args.items_per_query


def main(output_dir, queries, items_per_query, download_images=False, single_only=False):
    output_dir.mkdir(parents=True, exist_ok=True)
    image_dir = output_dir / "images"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    scrape_date = datetime.now().replace(microsecond=0).isoformat()

    items = fetch_products()
    selected_by_query = {
        query: select_items_for_query(items, query, items_per_query)
        for query in queries
    }
    selected_items = unique_items(item for query_items in selected_by_query.values() for item in query_items)
    review_by_id, errors = fetch_all_review_summaries(selected_items)
    session = make_session() if download_images else None
    image_cache = {}
    batch_rows = []

    for query, query_items in selected_by_query.items():
        query_rows = []
        for result_rank, item in enumerate(query_items, start=1):
            product_id = item["product"].get("id")
            row_item = dict(item)
            if download_images:
                row_item["local_image_path"] = download_image_for_item(
                    session=session,
                    item=item,
                    image_dir=image_dir,
                    image_cache=image_cache,
                    errors=errors,
                )
            query_rows.append(make_row(scrape_date, query, row_item, result_rank, review_by_id.get(product_id, {})))

        query_csv = output_dir / f"brixton_{safe_name(query)}_{stamp}.csv"
        write_csv(query_csv, query_rows, COLUMNS)
        print(f"Saved {len(query_rows)} products for {query!r} to {query_csv}")
        batch_rows.extend(query_rows)

    data_path = output_dir / f"brixton_fashion_batch_{stamp}.csv"
    error_path = output_dir / f"brixton_review_errors_{stamp}.csv"
    if len(queries) > 1 and not single_only:
        write_csv(data_path, batch_rows, COLUMNS)
    elif queries:
        data_path = output_dir / f"brixton_{safe_name(queries[0])}_{stamp}.csv"
    write_csv(error_path, errors, ["product_id", "error"])

    rated_count = sum(1 for row in batch_rows if row["rating_numeric"])
    print(f"data_csv={data_path.resolve()}")
    print(f"error_csv={error_path.resolve()}")
    print(f"rows={len(batch_rows)}")
    print(f"rated_products={rated_count}")
    print(f"review_errors={len(errors)}")
    print(f"download_images={download_images}")
    if download_images:
        print(f"image_dir={image_dir.resolve()}")


def sample_images(sample_size=5, output_dir=Path("brixton_scrape")):
    output_dir.mkdir(parents=True, exist_ok=True)
    image_dir = output_dir / "sample_images"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    scrape_date = datetime.now().replace(microsecond=0).isoformat()

    items = fetch_products()[:sample_size]
    review_by_id, errors = fetch_all_review_summaries(items)
    session = make_session()

    rows = []
    for index, item in enumerate(items, start=1):
        product = item["product"]
        product_id = product.get("id")
        image_path = download_image(session, product_image(product), image_dir, product_id)
        item["local_image_path"] = image_path
        rows.append(make_row(scrape_date, "sample", item, index, review_by_id.get(product_id, {})))

    data_path = output_dir / f"brixton_sample_with_images_{stamp}.csv"
    error_path = output_dir / f"brixton_sample_review_errors_{stamp}.csv"
    write_csv(data_path, rows, COLUMNS)
    write_csv(error_path, errors, ["product_id", "error"])

    print(f"sample_csv={data_path.resolve()}")
    print(f"image_dir={image_dir.resolve()}")
    print(f"rows={len(rows)}")
    print(f"review_errors={len(errors)}")
    for row in rows:
        print(f"{row['asin']} | {row['product_name']} | {row['local_image_path']}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--query", help="Single search keyword, for example: bucket hat")
    parser.add_argument(
        "--queries",
        help="Comma-separated keywords for batch mode. Defaults to built-in fashion keywords.",
    )
    parser.add_argument("--max-items", type=int, default=0, help="Maximum products to keep for --query. 0 means no limit")
    parser.add_argument("--items-per-query", type=int, default=50, help="Products to keep for each keyword in batch mode")
    parser.add_argument("--sample-images", type=int, default=0, help="Download image samples instead of running full scrape.")
    parser.add_argument("--out-dir", default="brixton_scrape", help="Directory for Brixton CSV outputs.")
    parser.add_argument("--download-images", action="store_true", help="Download Brixton product images during full scrape.")
    parser.add_argument(
        "--single-only",
        action="store_true",
        help="Only save the per-query CSV files, not the combined batch CSV.",
    )
    args = parser.parse_args()
    output_dir = Path(args.out_dir)

    if args.sample_images:
        sample_images(args.sample_images, output_dir=output_dir)
    else:
        queries, items_per_query = parse_queries(args)
        main(
            output_dir=output_dir,
            queries=queries,
            items_per_query=items_per_query,
            download_images=args.download_images,
            single_only=args.single_only,
        )
