# Amazon Data Cleaning Report

Generated at: 2026-04-27T08:54:25

## Files

- Input: `scraped/amazon_fashion_batch_20260426_211640.csv`
- Output: `scraped/cleaned/amazon_fashion_batch_20260426_211640_rating_cleaned.csv`

## Step 1: Remove Products Without Rating Signals

Rows are removed if either field is missing:

- `rating_numeric`
- `number_of_ratings_numeric`

## Row Counts

- Rows before cleaning: 599
- Rows removed: 48
- Rows after cleaning: 551

## Manual Labeling

- Manual label file: not used
- Manual label cells updated: 0
- Manual label template: `scraped/cleaned/amazon_fashion_batch_20260426_211640_manual_label_template.csv`
- Manual label template rows: 541

## Missing Values After Cleaning

```text
scrape_date                    0
source                         0
query                          0
page                           0
page_position                  0
result_rank                    0
is_sponsored                   0
asin                           0
brand_name                     0
product_name                   0
price                          0
currency                       0
price_numeric                  0
rating                         0
rating_numeric                 0
number_of_ratings              0
number_of_ratings_numeric      0
derived_gender                33
derived_style                  0
derived_scene                  0
derived_colour                 0
derived_material               0
derived_pattern                0
product_url                    0
image_url                      0
local_image_path             551
```

## Rows Per Query After Cleaning

```text
query
floral dress        49
oversized hoodie    49
striped shirt       48
cargo pants         48
bucket hat          47
wide leg jeans      47
denim jacket        46
pleated skirt       46
platform shoes      45
linen shirt         45
leather jacket      42
knit cardigan       39
```