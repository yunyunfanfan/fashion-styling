import argparse
import csv
import json
import random
import re
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus, urljoin, urlsplit, urlunsplit

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
except ImportError:
    sync_playwright = None
    PlaywrightTimeoutError = Exception

DEFAULT_QUERIES = [
    "bucket hat",
    "baseball cap",
    "women top",
    "linen shirt",
    "t shirt",
    "summer dress",
    "skirt",
    "wide leg pants",
    "jeans",
    "denim jacket",
    "cardigan",
    "sweater",
    "blazer",
    "bag",
    "sandals",
]

PLACEHOLDER = "no_video"

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
    "bucket", "hat", "cap", "beanie", "shirt", "tee", "t-shirt", "jacket", "coat", "hoodie",
    "pant", "pants", "jeans", "trouser", "short", "dress", "skirt", "sweater", "cardigan",
    "blazer", "vest", "bra", "tank", "camisole", "polo", "sandal", "shoe", "bag", "belt", "sock",
    "casual", "streetwear", "classic", "basic", "workwear", "active", "sport", "loungewear",
]

SCENE_TERMS = {
    "vacation": ["vacation", "beach", "travel", "resort", "summer", "linen"],
    "outdoor": ["outdoor", "hiking", "trail", "rain", "sun", "uv", "parka"],
    "sports": ["sport", "active", "running", "training", "yoga", "airism", "dry-ex"],
    "work": ["work", "workwear", "office", "blazer", "shirt", "trouser"],
    "party": ["party", "evening", "festival", "dress"],
    "daily": ["basic", "everyday", "casual", "lounge", "relaxed"],
}

COLOUR_TERMS = [
    "black", "white", "red", "blue", "green", "yellow", "pink", "purple", "orange", "brown", "grey", "gray",
    "navy", "cream", "beige", "tan", "ivory", "silver", "gold", "natural", "charcoal", "khaki", "olive",
    "off white", "dark gray", "light gray", "wine", "mint", "lavender",
]

MATERIAL_TERMS = [
    "cotton", "polyester", "nylon", "wool", "merino", "leather", "denim", "linen", "silk", "cashmere",
    "spandex", "elastane", "viscose", "rayon", "fleece", "canvas", "straw", "felt", "corduroy",
    "ribbed", "knit", "jersey", "flannel", "satin", "mesh", "chiffon", "down", "heattech", "airism",
]

PATTERN_TERMS = [
    "stripe", "striped", "floral", "plaid", "check", "checked", "print", "printed", "reversible",
    "embroidered", "logo", "solid", "tie dye", "leopard", "camo", "woven", "rib", "graphic",
]


def normalize_text(value):
    if isinstance(value, list):
        value = " ".join(str(item) for item in value)
    return re.sub(r"\s+", " ", str(value or "")).strip().lower()


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


def clean_url(url):
    if not url:
        return ""
    parts = urlsplit(url)
    # Keep path only to deduplicate color/size variants.
    return urlunsplit((parts.scheme, parts.netloc, parts.path.rstrip("/"), "", ""))


def is_valid_uniqlo_product_url(url):
    """Return True only for real UNIQLO product-detail URLs.

    Search/listing/navigation URLs can contain generic product-related strings or
    redirect back to search pages. Real UNIQLO US product pages normally contain
    /products/E + digits, for example /products/E467074-000/.
    """
    if not url:
        return False
    parts = urlsplit(url)
    path = parts.path.rstrip("/")
    if "/products/" not in path:
        return False
    return bool(re.search(r"/products/[A-Za-z]\d{5,}(?:[-_]\d+)?(?:/|$)", path))


def looks_like_search_or_listing_page(info, page):
    name = normalize_text(info.get("product_name", ""))
    current_url = page.url or info.get("product_url", "") or ""
    if name.startswith("search results") or "search results for" in name:
        return True
    if "/search" in urlsplit(current_url).path.lower():
        return True
    return False


def uniqlo_product_id(url):
    text = url or ""
    m = re.search(r"/products/([^/?#]+)", text)
    if m:
        return m.group(1)
    m = re.search(r"pid=([A-Za-z0-9_-]+)", text)
    if m:
        return m.group(1)
    return re.sub(r"\W+", "_", text.strip("/").split("/")[-1])[:80]


def price_numeric(price):
    match = re.search(r"\d+(?:\.\d+)?", str(price or ""))
    return match.group(0) if match else ""


def write_csv(path, rows, columns):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def safe_json_loads(text):
    try:
        return json.loads(text)
    except Exception:
        # Some sites put multiple JSON-LD blocks or invalid HTML entities; keep it conservative.
        return None


def walk_json(obj):
    if isinstance(obj, dict):
        yield obj
        for value in obj.values():
            yield from walk_json(value)
    elif isinstance(obj, list):
        for item in obj:
            yield from walk_json(item)


def extract_jsonld_products(html):
    products = []
    for m in re.finditer(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, re.I | re.S):
        raw = re.sub(r"<!--|-->", "", m.group(1)).strip()
        data = safe_json_loads(raw)
        if data is None:
            continue
        for node in walk_json(data):
            typ = node.get("@type") or node.get("type")
            if isinstance(typ, list):
                is_product = any(str(t).lower() == "product" for t in typ)
            else:
                is_product = str(typ).lower() == "product"
            if is_product:
                products.append(node)
    return products


def meta_content(html, prop):
    patterns = [
        rf'<meta[^>]+property=["\']{re.escape(prop)}["\'][^>]+content=["\']([^"\']+)["\']',
        rf'<meta[^>]+name=["\']{re.escape(prop)}["\'][^>]+content=["\']([^"\']+)["\']',
        rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']{re.escape(prop)}["\']',
        rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']{re.escape(prop)}["\']',
    ]
    for pat in patterns:
        m = re.search(pat, html, re.I | re.S)
        if m:
            return re.sub(r"\s+", " ", m.group(1)).strip()
    return ""


def extract_from_product_jsonld(product):
    name = product.get("name", "") or ""
    image = product.get("image", "") or ""
    if isinstance(image, list):
        image = image[0] if image else ""
    offers = product.get("offers") or {}
    if isinstance(offers, list):
        offers = offers[0] if offers else {}
    price = str(offers.get("price", "") or offers.get("lowPrice", "") or "") if isinstance(offers, dict) else ""
    currency = offers.get("priceCurrency", "") if isinstance(offers, dict) else ""
    agg = product.get("aggregateRating") or {}
    rating_value = ""
    review_count = ""
    if isinstance(agg, dict):
        rating_value = agg.get("ratingValue") or agg.get("rating") or ""
        review_count = agg.get("reviewCount") or agg.get("ratingCount") or agg.get("count") or ""
    return {
        "name": str(name or "").strip(),
        "image": str(image or "").strip(),
        "price": str(price or "").strip(),
        "currency": str(currency or "").strip(),
        "rating_value": str(rating_value or "").strip(),
        "review_count": str(review_count or "").strip(),
    }


def extract_rating_from_text(text):
    rating = ""
    count = ""
    text_clean = re.sub(r"\s+", " ", text or " ")

    rating_patterns = [
        r"(\d(?:\.\d)?)\s*out of\s*5",
        r"(\d(?:\.\d)?)\s*/\s*5",
        r"rating\s*[:\-]?\s*(\d(?:\.\d)?)",
        r"(\d(?:\.\d)?)\s*stars?",
    ]
    for pat in rating_patterns:
        m = re.search(pat, text_clean, re.I)
        if m:
            value = float(m.group(1))
            if 0 < value <= 5:
                rating = f"{value:.1f}"
                break

    count_patterns = [
        r"(\d[\d,]*)\s*(?:customer\s*)?reviews?",
        r"(\d[\d,]*)\s*ratings?",
        r"reviews?\s*\(?\s*(\d[\d,]*)\s*\)?",
    ]
    for pat in count_patterns:
        m = re.search(pat, text_clean, re.I)
        if m:
            count = m.group(1).replace(",", "")
            break

    return rating, count


def parse_product_page(page, url):
    html = page.content()
    visible_text = page.locator("body").inner_text(timeout=10000)
    product_info = {}
    products = extract_jsonld_products(html)
    if products:
        product_info = extract_from_product_jsonld(products[0])

    name = product_info.get("name") or meta_content(html, "og:title") or page.title()
    name = re.sub(r"\s*\|\s*UNIQLO.*$", "", name, flags=re.I).strip()

    image = product_info.get("image") or meta_content(html, "og:image")
    price = product_info.get("price") or ""
    currency = product_info.get("currency") or "USD"

    if not price:
        m = re.search(r"\$\s*\d+(?:\.\d{2})?", visible_text)
        if m:
            price = m.group(0).replace(" ", "")

    rating_value = product_info.get("rating_value") or ""
    review_count = product_info.get("review_count") or ""
    if not rating_value or not review_count:
        r2, c2 = extract_rating_from_text(visible_text)
        rating_value = rating_value or r2
        review_count = review_count or c2

    rating_numeric = ""
    rating_text = ""
    try:
        value = float(str(rating_value).replace(",", ""))
        if 0 < value <= 5:
            rating_numeric = f"{value:.6g}"
            rating_text = f"{value:.1f} out of 5 stars"
    except Exception:
        pass

    review_count_numeric = ""
    review_count_text = ""
    try:
        count = int(float(str(review_count).replace(",", "")))
        if count > 0:
            review_count_numeric = str(count)
            review_count_text = f"{count:,} ratings"
    except Exception:
        pass

    return {
        "product_name": name,
        "price": str(price or ""),
        "currency": str(currency or "USD"),
        "rating": rating_text,
        "rating_numeric": rating_numeric,
        "number_of_ratings": review_count_text,
        "number_of_ratings_numeric": review_count_numeric,
        "image_url": image,
        "product_url": url,
    }


def handle_popups(page):
    labels = [
        "Accept All", "Accept all", "Accept Cookies", "I Agree", "Agree", "Got it", "OK", "No thanks", "Close",
    ]
    for label in labels:
        try:
            loc = page.get_by_role("button", name=re.compile(re.escape(label), re.I))
            if loc.count() > 0:
                loc.first.click(timeout=1500)
                page.wait_for_timeout(500)
        except Exception:
            pass
    try:
        page.keyboard.press("Escape")
    except Exception:
        pass


def build_search_url(base_url, query):
    base_url = base_url.rstrip("/")
    # Tested-style URL pattern for UNIQLO US. Other regions may differ.
    return f"{base_url}/search?q={quote_plus(query)}"


def collect_links_for_query(page, base_url, query, max_products_per_query, delay):
    search_url = build_search_url(base_url, query)
    page.goto(search_url, wait_until="domcontentloaded", timeout=45000)
    handle_popups(page)
    page.wait_for_timeout(int(delay * 1000))

    for _ in range(5):
        try:
            page.mouse.wheel(0, 1800)
            page.wait_for_timeout(900)
        except Exception:
            break

    hrefs = page.eval_on_selector_all(
        "a[href]",
        "els => els.map(a => a.href).filter(Boolean)",
    )
    links = []
    seen = set()
    for href in hrefs:
        if "uniqlo.com" not in href:
            href = urljoin(base_url, href)
        url = clean_url(href)
        if not is_valid_uniqlo_product_url(url):
            continue
        if url and url not in seen:
            seen.add(url)
            links.append(url)
        if len(links) >= max_products_per_query:
            break
    return links, search_url


def make_row(scrape_date, source, query, page_no, page_position, result_rank, brand_name, info):
    combined_text = normalize_text([info.get("product_name"), info.get("price"), info.get("product_url")])
    pid = uniqlo_product_id(info.get("product_url", ""))
    return {
        "scrape_date": scrape_date,
        "source": source,
        "query": query,
        "page": page_no,
        "page_position": page_position,
        "result_rank": result_rank,
        "is_sponsored": "no",
        "asin": f"uniqlo_{pid}" if pid else "",
        "brand_name": brand_name,
        "product_name": info.get("product_name", ""),
        "price": info.get("price", ""),
        "currency": info.get("currency", "USD") or "USD",
        "price_numeric": price_numeric(info.get("price", "")),
        "rating": info.get("rating", ""),
        "rating_numeric": info.get("rating_numeric", ""),
        "number_of_ratings": info.get("number_of_ratings", ""),
        "number_of_ratings_numeric": info.get("number_of_ratings_numeric", ""),
        "derived_gender": derive_gender(combined_text),
        "derived_style": first_match(combined_text, STYLE_TERMS),
        "derived_scene": derive_from_map(combined_text, SCENE_TERMS),
        "derived_colour": first_match(combined_text, COLOUR_TERMS),
        "derived_material": first_match(combined_text, MATERIAL_TERMS),
        "derived_pattern": first_match(combined_text, PATTERN_TERMS),
        "product_url": info.get("product_url", ""),
        "image_url": info.get("image_url", ""),
        "local_image_path": "",
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


def run(args):
    if sync_playwright is None:
        raise SystemExit(
            "Missing dependency: playwright. Install it with:\n"
            "  pip install playwright\n"
            "  python -m playwright install chromium"
        )

    queries = [q.strip() for q in args.queries.split(",") if q.strip()]
    output_dir = Path(args.output_dir)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    data_path = output_dir / f"uniqlo_fashion_batch_{stamp}.csv"
    error_path = output_dir / f"uniqlo_review_errors_{stamp}.csv"
    scrape_date = datetime.now().replace(microsecond=0).isoformat()

    rows = []
    errors = []
    candidates = []
    seen = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not args.headed)
        context = browser.new_context(
            viewport={"width": 1366, "height": 900},
            locale="en-US",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
            ),
        )
        page = context.new_page()

        for query in queries:
            if len(candidates) >= args.max_total_products:
                break
            try:
                links, search_url = collect_links_for_query(
                    page, args.base_url, query, args.max_products_per_query, args.delay
                )
                added = 0
                for link in links:
                    if link not in seen:
                        seen.add(link)
                        candidates.append({"query": query, "url": link, "position": len(candidates) + 1})
                        added += 1
                    if len(candidates) >= args.max_total_products:
                        break
                print(f"query='{query}': links={len(links)} added={added} total={len(candidates)}")
                if not links:
                    errors.append({"url": search_url, "product_name": "", "error": "no product links found"})
                time.sleep(args.delay + random.random() * args.jitter)
            except Exception as exc:
                search_url = build_search_url(args.base_url, query)
                print(f"query='{query}': no links ({type(exc).__name__}: {str(exc)[:180]})")
                errors.append({"url": search_url, "product_name": "", "error": f"search: {type(exc).__name__}: {str(exc)[:240]}"})

        print(f"candidate_products={len(candidates)}")

        for index, item in enumerate(candidates, start=1):
            url = item["url"]
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=45000)
                handle_popups(page)
                page.wait_for_timeout(int(args.delay * 1000))
                info = parse_product_page(page, url)
                info["product_url"] = url
                if looks_like_search_or_listing_page(info, page):
                    print(f"[{index}/{len(candidates)}] skip | not product page | {info.get('product_name', '')[:70]}")
                    errors.append({"url": url, "product_name": info.get("product_name", ""), "error": "not product page"})
                    continue
                has_rating = bool(info.get("rating_numeric") and info.get("number_of_ratings_numeric"))
                if has_rating or args.keep_unrated:
                    row = make_row(
                        scrape_date,
                        args.source,
                        item["query"],
                        1,
                        index,
                        len(rows) + 1,
                        args.brand_name,
                        info,
                    )
                    rows.append(row)
                    status = "rated" if has_rating else "unrated"
                    print(f"[{index}/{len(candidates)}] keep {status} | {row['rating_numeric']} | {row['number_of_ratings_numeric']} | {row['product_name'][:70]}")
                else:
                    print(f"[{index}/{len(candidates)}] skip | no rating | {info.get('product_name', '')[:70]}")
                    errors.append({"url": url, "product_name": info.get("product_name", ""), "error": "no rating"})
                time.sleep(args.delay + random.random() * args.jitter)
            except Exception as exc:
                print(f"[{index}/{len(candidates)}] error | {type(exc).__name__}: {str(exc)[:160]}")
                errors.append({"url": url, "product_name": "", "error": f"detail: {type(exc).__name__}: {str(exc)[:240]}"})

        context.close()
        browser.close()

    write_csv(data_path, rows, COLUMNS)
    write_csv(error_path, errors, ["url", "product_name", "error"])
    rated_count = sum(1 for r in rows if r.get("rating_numeric") and r.get("number_of_ratings_numeric"))
    print(f"data_csv={data_path.resolve()}")
    print(f"error_csv={error_path.resolve()}")
    print(f"rows={len(rows)}")
    print(f"rated_products={rated_count}")
    print(f"errors={len(errors)}")
    if not rows:
        print("WARNING: no rows written. Try --headed to diagnose, or add --keep-unrated to see products without ratings.")


def main():
    parser = argparse.ArgumentParser(description="UNIQLO fashion scraper aligned to the Amazon-format multi-source CSV.")
    parser.add_argument("--base-url", default="https://www.uniqlo.com/us/en", help="UNIQLO regional base URL, default US English site.")
    parser.add_argument("--source", default="www.uniqlo.com", help="Value for source column.")
    parser.add_argument("--brand-name", default="UNIQLO", help="Value for brand_name column.")
    parser.add_argument("--queries", default=",".join(DEFAULT_QUERIES), help="Comma-separated search queries.")
    parser.add_argument("--output-dir", default="uniqlo_scrape", help="Output directory.")
    parser.add_argument("--max-products-per-query", type=int, default=8)
    parser.add_argument("--max-total-products", type=int, default=80)
    parser.add_argument("--delay", type=float, default=2.5, help="Delay between browser actions.")
    parser.add_argument("--jitter", type=float, default=1.5, help="Random extra delay.")
    parser.add_argument("--headed", action="store_true", help="Show browser window for debugging.")
    parser.add_argument("--keep-unrated", action="store_true", help="Keep products even if rating/review count is missing.")
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
