import argparse
import base64
import json
import os
import sys
import time
from pathlib import Path

import pandas as pd
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


def is_missing_label(value):
    return pd.isna(value) or str(value).strip() in {"", "unknown", "not_available"}


def image_to_data_uri(path):
    image_path = Path(path)
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


def row_image_url(row, use_remote_image):
    local_path = str(row.get("local_image_path", "") or "")
    if local_path and local_path not in {"not_downloaded", "download_failed", "not_available"}:
        data_uri = image_to_data_uri(local_path)
        if data_uri:
            return data_uri, "local_image"

    remote_url = str(row.get("image_url", "") or "")
    if use_remote_image and remote_url.startswith(("http://", "https://")):
        return remote_url, "remote_image"

    return "", "text_only"


def build_prompt(row, fields_to_fill):
    compact_taxonomy = {field: TAXONOMY[field] for field in fields_to_fill}
    product_context = {
        "query": row.get("query", ""),
        "brand_name": row.get("brand_name", ""),
        "product_name": row.get("product_name", ""),
        "price": row.get("price", ""),
        "rating": row.get("rating", ""),
        "number_of_ratings": row.get("number_of_ratings", ""),
    }

    return (
        "You are assisting a fashion data curation project.\n"
        "Predict missing fashion labels for one product.\n\n"
        "Rules:\n"
        "1. Return only valid JSON.\n"
        "2. For each requested field, choose exactly one value from its allowed list.\n"
        "3. Do not invent new labels.\n"
        "4. If there is not enough evidence, choose \"unknown\".\n"
        "5. Use the image if provided. If no image is provided, use text only.\n\n"
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


def call_glm(client, model, row, fields_to_fill, image_url, temperature):
    prompt = build_prompt(row, fields_to_fill)
    content = [{"type": "text", "text": prompt}]
    if image_url:
        content.append({"type": "image_url", "image_url": {"url": image_url}})

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


def call_glm_with_retries(client, model, row, fields_to_fill, image_url, temperature, max_retries, retry_delay):
    for attempt in range(max_retries + 1):
        try:
            return call_glm(
                client=client,
                model=model,
                row=row,
                fields_to_fill=fields_to_fill,
                image_url=image_url,
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
    for index, row in df.iterrows():
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
            print(index, df.loc[index, "product_name"], fields)
        return

    client = ZhipuAI(api_key=api_key)
    ok_count = 0
    error_count = 0
    for count, (index, fields_to_fill) in enumerate(rows_to_label, start=1):
        row = df.loc[index]
        image_url, label_source = row_image_url(row, use_remote_image=not args.no_remote_image)
        df.at[index, "glm_model"] = args.model
        df.at[index, "glm_label_source"] = label_source
        try:
            raw_text = call_glm_with_retries(
                client=client,
                model=args.model,
                row=row,
                fields_to_fill=fields_to_fill,
                image_url=image_url,
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
