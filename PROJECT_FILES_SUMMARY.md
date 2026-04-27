# E-commerce Web Scraper: Current Files Summary

## Current Status

这个文件夹现在只保留当前项目需要的 Amazon fashion trend pipeline 文件。旧仓库自带的 CSV、旧爬虫脚本、旧图片样本、旧 README 示例图片和早期测试 CSV 已经删除。

## Remaining Files

### Core Scripts

| File | Purpose |
| --- | --- |
| `scrape_latest_amazon.py` | 批量抓取 Amazon fashion 商品数据 |
| `clean_amazon_data.py` | 清洗 Amazon 数据，删除缺少评分/评论数量的商品，并导出人工补标模板 |
| `fill_labels_with_glm.py` | 使用 GLM 视觉/文本模型补全 `derived_*` 标签 |
| `analyze_trends.py` | 使用 CRITIC 方法计算趋势分数 |
| `brand_recommendations.py` | 将趋势分数转化为品牌建议，可选 GLM 生成 Markdown |
| `quick_start.sh` | 小样本快速跑通 pipeline |
| `run_full_pipeline.sh` | 完整 Amazon 数据流脚本 |

### Documentation

| File | Purpose |
| --- | --- |
| `PROJECT_FILES_SUMMARY.md` | 当前文件夹说明 |
| `LABEL_TAXONOMY.md` | 固定标签范围和人工/GLM 补标规则 |
| `requirements.txt` | Python 依赖 |

## Current Data

### Raw Batch Output

保留最新正式批次 `20260426_211640`。

| File | Content |
| --- | --- |
| `scraped/amazon_fashion_batch_20260426_211640.csv` | Amazon 12 个关键词合并总表 |

### Per-query Outputs

这些文件是同一批次中每个关键词的单独结果：

```text
scraped/amazon_bucket_hat_20260426_211640.csv
scraped/amazon_cargo_pants_20260426_211640.csv
scraped/amazon_denim_jacket_20260426_211640.csv
scraped/amazon_floral_dress_20260426_211640.csv
scraped/amazon_knit_cardigan_20260426_211640.csv
scraped/amazon_leather_jacket_20260426_211640.csv
scraped/amazon_linen_shirt_20260426_211640.csv
scraped/amazon_oversized_hoodie_20260426_211640.csv
scraped/amazon_platform_shoes_20260426_211640.csv
scraped/amazon_pleated_skirt_20260426_211640.csv
scraped/amazon_striped_shirt_20260426_211640.csv
scraped/amazon_wide_leg_jeans_20260426_211640.csv
```

### Cleaned Outputs

| File | Content |
| --- | --- |
| `scraped/cleaned/amazon_fashion_batch_20260426_211640_rating_cleaned.csv` | 删除缺少 `rating_numeric` 或 `number_of_ratings_numeric` 后的数据 |
| `scraped/cleaned/amazon_fashion_batch_20260426_211640_cleaning_report.md` | 清洗报告 |
| `scraped/cleaned/amazon_fashion_batch_20260426_211640_manual_label_template.csv` | 人工补标模板 |

## Main Workflow

### 0. Quick Start

```bash
./quick_start.sh
```

小样本验证：3 个关键词，每个 8 条商品，不下载图片，不调用 GLM。

完整流程：

```bash
./run_full_pipeline.sh
```

默认抓 12 个关键词，每个 50 条商品，并下载本地图片。

### 1. Scrape New Amazon Data

```bash
python scrape_latest_amazon.py
```

默认抓取 12 个 fashion 关键词，每个关键词保留 50 条商品，并生成一张总表。

只生成 CSV，不下载图片：

```bash
python scrape_latest_amazon.py --no-images
```

### 2. Clean Data

```bash
python clean_amazon_data.py scraped/amazon_fashion_batch_20260426_211640.csv
```

当前第一步清洗规则：

```text
删除缺少 rating_numeric 或 number_of_ratings_numeric 的商品
```

当前清洗结果：

```text
Rows before cleaning: 599
Rows removed: 48
Rows after cleaning: 551
```

### 3. Export Manual Label Template

```bash
python clean_amazon_data.py scraped/amazon_fashion_batch_20260426_211640.csv --export-manual-template
```

用于补充这些字段：

```text
derived_style
derived_scene
derived_colour
derived_material
derived_pattern
```

标签范围见：

```text
LABEL_TAXONOMY.md
```

### 4. Fill Labels With GLM

API key 必须使用环境变量，不要写进代码：

```bash
export ZHIPUAI_API_KEY="your_new_api_key_here"
```

默认使用免费视觉/文本模型：

```text
glm-4.6v-flash
```

先 dry-run：

```bash
python fill_labels_with_glm.py scraped/cleaned/amazon_fashion_batch_20260426_211640_rating_cleaned.csv --dry-run --limit 10
```

正式运行：

```bash
python fill_labels_with_glm.py scraped/cleaned/amazon_fashion_batch_20260426_211640_rating_cleaned.csv
```

只用文本，不使用远程图片：

```bash
python fill_labels_with_glm.py scraped/cleaned/amazon_fashion_batch_20260426_211640_rating_cleaned.csv --no-remote-image
```

如果只做纯文本补标，可以指定免费文本模型：

```bash
python fill_labels_with_glm.py scraped/cleaned/amazon_fashion_batch_20260426_211640_rating_cleaned.csv \
  --model glm-4-flash-250414 \
  --no-remote-image
```

### 5. Analyze Trends With CRITIC

```bash
python analyze_trends.py scraped/cleaned/amazon_fashion_batch_20260426_211640_rating_cleaned.csv
```

输出：

```text
analysis/trend_scores_all_dimensions.csv
analysis/critic_weights.csv
analysis/trend_analysis_report.md
```

当前数据已验证可以计算：

```text
Rows analyzed: 551
Dimensions analyzed: 5
```

### 6. Generate Brand Recommendations

默认不调用 GLM：

```bash
python brand_recommendations.py analysis/trend_scores_all_dimensions.csv
```

输出：

```text
analysis/brand_recommendations.csv
analysis/brand_recommendations.md
```

如果需要用 GLM 生成 Markdown 报告：

```bash
export ZHIPUAI_API_KEY="your_new_api_key_here"

python brand_recommendations.py analysis/trend_scores_all_dimensions.csv \
  --use-glm \
  --products-csv scraped/cleaned/amazon_fashion_batch_20260426_211640_rating_cleaned.csv
```

当前验证结果：

```text
Strong Trend: 8
Weak Signal: 20
Noise: 12
```

## Removed Old Files

已删除的旧文件包括：

- 旧 Amazon 示例 CSV：`ASINs.csv`、`ASIN_product_details.csv`、`amazon_main_page_scraping.csv`、`data.csv`
- 旧爬虫脚本：`amazon_search_image_scraper.py`、`asin_scraper.py`、`scrape_amazon.py`、`scrape_flipkart.py`、`scrape_images_from_alibaba.py`、`scrape_product_details_using_asins.py`
- 旧图片目录：`images/`
- 旧 README 示例资源：`README.md`、`ReadmeImages/`
- 旧 Scrapy 示例目录：`scrapy_tut/`
- 早期测试 CSV：`205624`、`205705`、`210525`、`211042`、`211116`、`211211` 等批次

## Summary

当前目录已经清理为一个更干净的 Amazon fashion trend data pipeline：保留最新正式数据、清洗结果、标签 taxonomy、GLM 补标脚本和核心说明文档。
