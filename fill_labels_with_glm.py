import argparse
import base64
import json
import os
import sys
import time
from pathlib import Path

import pandas as pd
from tqdm import tqdm
from zhipuai import ZhipuAI


TAXONOMY = {
    "derived_style": [
        "basic",
        "casual",
        "formal",
        "sporty",
        "party",
        "streetwear",
        "romantic",
        "outdoor",
        "minimal",
        "retro",
        "unknown",
    ],
    "derived_scene": [
        "daily wear",
        "work",
        "party",
        "vacation",
        "outdoor",
        "sport",
        "home",
        "school",
        "unknown",
    ],
    "derived_colour": [
        "black",
        "white",
        "blue",
        "denim",
        "grey",
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
        "unknown",
    ],
    "derived_material": [
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
        "unknown",
    ],
    "derived_pattern": [
        "solid",
        "striped",
        "floral",
        "printed",
        "embroidered",
        "check",
        "plaid",
        "graphic",
        "reversible",
        "unknown",
    ],
}

LABEL_FIELDS = list(TAXONOMY)
MISSING_MEDIA_MARKERS = {
    "",
    "nan",
    "none",
    "not_available",
    "not_downloaded",
    "download_failed",
    "no_video",
    "not_checked",
    "extract_failed",
}


def is_missing_label(value):
    return pd.isna(value) or str(value).strip() in {"", "unknown", "not_available"}


def local_image_to_data_uri(path):
    image_path = Path(str(path).strip())
    if not image_path.exists() or not image_path.is_file():
        return ""

    suffix = image_path.suffix.lower()
    mime_type = "image/jpeg"
    if suffix == ".png":
        mime_type = "image/png"
    elif suffix == ".webp":
        mime_type = "image/webp"

    encoded = base64.b64encode(image_path.read_bytes()).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"


def is_missing_media(value):
    if pd.isna(value):
        return True
    text = str(value).strip()
    return text.lower() in MISSING_MEDIA_MARKERS


def split_media_paths(value):
    if is_missing_media(value):
        return []
    return [part.strip() for part in str(value).split("|") if not is_missing_media(part)]


def add_local_visual(visual_inputs, source, path):
    if is_missing_media(path):
        return
    data_uri = local_image_to_data_uri(path)
    if data_uri:
        visual_inputs.append((data_uri, source))


def add_remote_visual(visual_inputs, source, url, use_remote_image):
    if not use_remote_image or is_missing_media(url):
        return
    url = str(url).strip()
    if url.startswith(("http://", "https://")):
        visual_inputs.append((url, source))


def row_visual_inputs(row, use_remote_image, max_visual_inputs):
    visual_inputs = []

    add_local_visual(visual_inputs, "local_image", row.get("local_image_path", ""))
    add_local_visual(visual_inputs, "local_video_cover", row.get("local_video_cover_path", ""))
    for frame_path in split_media_paths(row.get("local_video_frame_paths", "")):
        add_local_visual(visual_inputs, "local_video_frame", frame_path)
    add_local_visual(visual_inputs, "local_video_thumbnail", row.get("local_video_thumbnail_path", ""))

    add_remote_visual(visual_inputs, "remote_image", row.get("image_url", ""), use_remote_image)
    add_remote_visual(visual_inputs, "remote_video_thumbnail", row.get("video_thumbnail_url", ""), use_remote_image)

    if max_visual_inputs > 0:
        visual_inputs = visual_inputs[:max_visual_inputs]

    if not visual_inputs:
        return [], "text_only"

    sources = []
    for _, source in visual_inputs:
        if source not in sources:
            sources.append(source)
    return [url for url, _ in visual_inputs], "+".join(sources)


def build_prompt(row, fields_to_fill):
    compact_taxonomy = {field: TAXONOMY[field] for field in fields_to_fill}
    product_context = {
        "query": row.get("query", ""),
        "brand_name": row.get("brand_name", ""),
        "product_name": row.get("product_name", ""),
        "price": row.get("price", ""),
        "rating": row.get("rating", ""),
        "number_of_ratings": row.get("number_of_ratings", ""),
        "has_product_video": row.get("has_product_video", ""),
        "video_extraction_status": row.get("video_extraction_status", ""),
    }

    return (
        "You are assisting a fashion data curation project.\n"
        "Predict missing fashion labels for one product.\n\n"
        "Rules:\n"
        "1. Return only valid JSON.\n"
        "2. For each requested field, choose exactly one value from its allowed list.\n"
        "3. Do not invent new labels.\n"
        "4. If there is not enough evidence, choose \"unknown\".\n"
        "5. Use the visual inputs if provided. They may include the product image, video cover, video frames, or video thumbnail.\n"
        "6. If no visual input is provided, use text only.\n\n"
        f"Product context:\n{json.dumps(product_context, ensure_ascii=False)}\n\n"
        f"Allowed labels:\n{json.dumps(compact_taxonomy, ensure_ascii=False)}\n\n"
        "Return JSON in this format:\n"
        "{\n"
        '  "derived_style": "casual",\n'
        '  "derived_scene": "daily wear",\n'
        '  "derived_colour": "black",\n'
        '  "derived_material": "cotton",\n'
        '  "derived_pattern": "solid",\n'
        '  "confidence": 0.0,\n'
        '  "reason": "short reason"\n'
        "}\n"
        "Only include requested derived_* fields plus confidence and reason."
    )


def parse_json_response(text):
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].strip()
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        text = text[start : end + 1]
    return json.loads(text)


def call_glm(client, model, row, fields_to_fill, visual_urls, temperature):
    prompt = build_prompt(row, fields_to_fill)
    content = [{"type": "text", "text": prompt}]
    for visual_url in visual_urls:
        content.append({"type": "image_url", "image_url": {"url": visual_url}})

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": content}],
        temperature=temperature,
    )
    return response.choices[0].message.content


def validate_labels(prediction, fields_to_fill):
    validated = {}
    for field in fields_to_fill:
        value = str(prediction.get(field, "unknown")).strip().lower()
        allowed = TAXONOMY[field]
        if value not in allowed:
            value = "unknown"
        validated[field] = value
    return validated


def is_fatal_api_error(error):
    error_text = str(error).lower()
    if is_retryable_api_error(error):
        return False

    fatal_markers = [
        "余额不足",
        "无可用资源包",
        "insufficient",
        "quota",
        "unauthorized",
        "forbidden",
        "invalid api key",
        "401",
        "403",
    ]
    return any(marker in error_text for marker in fatal_markers)


def is_retryable_api_error(error):
    error_text = str(error).lower()
    retryable_markers = [
        "1305",
        "访问量过大",
        "稍后再试",
        "too many requests",
        "rate limit",
        "temporarily",
        "timeout",
        "connection error",
    ]
    return any(marker in error_text for marker in retryable_markers)


def call_glm_with_retries(client, model, row, fields_to_fill, visual_urls, temperature, max_retries, retry_delay):
    for attempt in range(max_retries + 1):
        try:
            return call_glm(
                client=client,
                model=model,
                row=row,
                fields_to_fill=fields_to_fill,
                visual_urls=visual_urls,
                temperature=temperature,
            )
        except Exception as error:
            if not is_retryable_api_error(error) or attempt >= max_retries:
                raise
            wait_seconds = retry_delay * (2**attempt)
            print(f"Retryable API error: {error}")
            print(f"Waiting {wait_seconds:.1f}s before retry {attempt + 1}/{max_retries}...")
            time.sleep(wait_seconds)


def main():
    parser = argparse.ArgumentParser(description="Fill missing Amazon derived labels with GLM vision/text API.")
    parser.add_argument("input_csv", help="Input CSV to label")
    parser.add_argument("--output-csv", help="Output CSV path")
    parser.add_argument(
        "--model",
        default="glm-4.6v-flash",
        help="GLM model name. Default uses the free vision/text flash model.",
    )
    parser.add_argument("--api-key-env", default="ZHIPUAI_API_KEY", help="Environment variable containing API key")
    parser.add_argument("--limit", type=int, default=0, help="Maximum rows to send to GLM. 0 means no limit")
    parser.add_argument("--delay", type=float, default=0.3, help="Delay between API calls")
    parser.add_argument("--max-retries", type=int, default=4, help="Retries for temporary API errors")
    parser.add_argument("--retry-delay", type=float, default=10.0, help="Initial retry delay in seconds")
    parser.add_argument("--temperature", type=float, default=0.0, help="Model temperature")
    parser.add_argument("--no-remote-image", action="store_true", help="Do not use image_url when local image is missing")
    parser.add_argument(
        "--max-visual-inputs",
        type=int,
        default=3,
        help="Maximum product/video visual inputs to send to GLM per row. 0 means no limit.",
    )
    parser.add_argument("--fill-all", action="store_true", help="Ask GLM to relabel all taxonomy fields, not only missing fields")
    parser.add_argument("--dry-run", action="store_true", help="Show rows that would be labeled without calling the API")
    args = parser.parse_args()

    api_key = os.getenv(args.api_key_env)
    if not api_key and not args.dry_run:
        raise SystemExit(f"Missing API key. Set it with: export {args.api_key_env}=...")

    input_csv = Path(args.input_csv)
    output_csv = Path(args.output_csv) if args.output_csv else input_csv.with_name(f"{input_csv.stem}_glm_labeled.csv")

    df = pd.read_csv(input_csv, keep_default_na=False)
    for field in LABEL_FIELDS:
        if field not in df.columns:
            df[field] = "unknown"
    for audit_field in [
        "glm_model",
        "glm_label_source",
        "glm_label_confidence",
        "glm_label_reason",
        "glm_label_status",
        "glm_raw_response",
    ]:
        if audit_field not in df.columns:
            df[audit_field] = ""
        df[audit_field] = df[audit_field].astype("object")

    rows_to_label = []
    for index, row in tqdm(df.iterrows(), total=len(df), desc="Finding missing labels", unit="row"):
        if args.fill_all:
            fields_to_fill = LABEL_FIELDS
        else:
            fields_to_fill = [field for field in LABEL_FIELDS if is_missing_label(row.get(field))]
        if fields_to_fill:
            rows_to_label.append((index, fields_to_fill))

    if args.limit:
        rows_to_label = rows_to_label[: args.limit]

    print(f"Rows requiring labels: {len(rows_to_label)}")
    if args.dry_run:
        for index, fields in rows_to_label[:10]:
            visual_urls, label_source = row_visual_inputs(
                df.loc[index],
                use_remote_image=not args.no_remote_image,
                max_visual_inputs=args.max_visual_inputs,
            )
            print(index, df.loc[index, "product_name"], fields, label_source, f"visual_inputs={len(visual_urls)}")
        return

    client = ZhipuAI(api_key=api_key)
    ok_count = 0
    error_count = 0
    for count, (index, fields_to_fill) in enumerate(
        tqdm(rows_to_label, desc="GLM labeling", unit="row"),
        start=1,
    ):
        row = df.loc[index]
        visual_urls, label_source = row_visual_inputs(
            row,
            use_remote_image=not args.no_remote_image,
            max_visual_inputs=args.max_visual_inputs,
        )
        df.at[index, "glm_model"] = args.model
        df.at[index, "glm_label_source"] = label_source
        try:
            raw_text = call_glm_with_retries(
                client=client,
                model=args.model,
                row=row,
                fields_to_fill=fields_to_fill,
                visual_urls=visual_urls,
                temperature=args.temperature,
                max_retries=args.max_retries,
                retry_delay=args.retry_delay,
            )
            prediction = parse_json_response(raw_text)
            labels = validate_labels(prediction, fields_to_fill)
            for field, value in labels.items():
                df.at[index, field] = value
            df.at[index, "glm_label_confidence"] = prediction.get("confidence", "")
            df.at[index, "glm_label_reason"] = prediction.get("reason", "")
            df.at[index, "glm_label_status"] = "ok"
            df.at[index, "glm_raw_response"] = raw_text
            ok_count += 1
            print(f"[{count}/{len(rows_to_label)}] ok row {index} via {label_source}")
        except Exception as error:
            error_count += 1
            error_message = f"error: {error}"
            df.at[index, "glm_label_status"] = error_message
            print(f"[{count}/{len(rows_to_label)}] failed row {index} via {label_source}: {error}")

            if is_fatal_api_error(error):
                output_csv.parent.mkdir(parents=True, exist_ok=True)
                df.to_csv(output_csv, index=False)
                print("Fatal API error detected. Stopping early so credits/time are not wasted.")
                print(f"Saved partial CSV to {output_csv}")
                print(f"Rows succeeded: {ok_count}")
                print(f"Rows failed: {error_count}")
                sys.exit(1)

        time.sleep(args.delay)

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_csv, index=False)
    print(f"Saved labeled CSV to {output_csv}")
    print(f"Rows succeeded: {ok_count}")
    print(f"Rows failed: {error_count}")


if __name__ == "__main__":
    main()
