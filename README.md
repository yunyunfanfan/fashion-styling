# Amazon Fashion Data Pipeline

## 1. Project Purpose

这个文件夹是课程项目中的 Amazon 电商数据采集与清洗模块。

它的目标不是单纯保存商品列表，而是为 **Fashion Trend Intelligence** 项目提供一个公开电商数据源，用来观察当前市场中正在被展示和销售的 fashion products。

在整个大项目中，Amazon 数据主要承担三个作用：

1. 提供商品级市场信号
2. 提供商品图片和商品 metadata
3. 为后续 trend analysis 提供价格、评分、评论数量和视觉标签

## 2. Connection to Homework Requirements

Homework 要求项目关注：

- multiple data sources
- text, image, video, context 等多模态数据
- documented curation pipeline
- metadata cleaning
- AI-assisted component
- trend insights
- ethics and risk statement
- brand recommendations

Amazon 模块对应这些要求：

| Homework Requirement | Amazon Pipeline Response |
| --- | --- |
| Multiple data sources | Amazon 作为 e-commerce source |
| Text data | 商品名、品牌名、搜索关键词 |
| Image data | 商品图片 URL，可下载本地图片 |
| Context data | 价格、评分、评论数量、搜索排名 |
| Metadata | ASIN、source、query、scrape date、product URL |
| Curation pipeline | 爬取、清洗、过滤、补标签、导出报告 |
| AI-assisted component | GLM 视觉/文本模型补全 fashion labels |
| Trend signals | material、pattern、style、scene、rating、rank |
| Ethics | 小规模公开页面采集，不采集私人信息 |

## 3. Why This Can Collect Latest Data

这个 pipeline 不是读取旧的静态 CSV，也不是使用固定旧页面。

核心脚本：

```text
scrape_latest_amazon.py
```

每次运行时，它都会根据当前关键词实时构造 Amazon India 搜索 URL：

```text
https://www.amazon.in/s?k=<query>&page=<page>
```

例如：

```text
https://www.amazon.in/s?k=denim+jacket&page=1
```

因此，每次运行都会访问 Amazon 当前搜索结果页面，抓取当时页面中展示的商品信息。

它保存的 `scrape_date` 字段记录了抓取时间，所以可以证明数据是某一次运行时的新数据，而不是旧样本。

## 4. Current Kept Files

当前目录已经清理过，只保留项目需要的文件。

### Scripts

| File | Purpose |
| --- | --- |
| `scrape_latest_amazon.py` | 抓取 Amazon 当前搜索结果 |
| `clean_amazon_data.py` | 清洗数据，删除缺少评分/评论数的商品，导出补标模板 |
| `fill_labels_with_glm.py` | 调用 GLM 视觉/文本模型补全标签 |

### Documentation

| File | Purpose |
| --- | --- |
| `README.md` | 当前说明文档 |
| `PROJECT_FILES_SUMMARY.md` | 当前文件结构总结 |
| `LABEL_TAXONOMY.md` | 固定标签范围 |
| `requirements.txt` | Python 依赖 |

### Data

| File | Purpose |
| --- | --- |
| `scraped/amazon_fashion_batch_20260426_211640.csv` | 最新正式 Amazon 总表 |
| `scraped/amazon_*_20260426_211640.csv` | 每个关键词的单独结果 |
| `scraped/cleaned/amazon_fashion_batch_20260426_211640_rating_cleaned.csv` | 清洗后数据 |
| `scraped/cleaned/amazon_fashion_batch_20260426_211640_cleaning_report.md` | 清洗报告 |
| `scraped/cleaned/amazon_fashion_batch_20260426_211640_manual_label_template.csv` | 人工补标模板 |

## 5. Installation

进入项目目录：

```bash
cd /Users/yunfan/Documents/zhengfang/e-commerce-web-scraper
```

安装依赖：

```bash
python -m pip install -r requirements.txt
```

依赖包括：

```text
requests
beautifulsoup4
lxml
zhipuai
```

## 6. Quick Start Scripts

项目提供两个 bash 脚本：

```text
quick_start.sh
run_full_pipeline.sh
```

### Quick Start

快速验证整条流程，默认只抓 3 个关键词、每个 8 条商品，不下载图片，不调用 GLM：

```bash
./quick_start.sh
```

输出目录示例：

```text
scraped/quick_start_<timestamp>/
analysis/quick_start_<timestamp>/
```

它会自动运行：

```text
1. scrape_latest_amazon.py
2. clean_amazon_data.py
3. analyze_trends.py
4. brand_recommendations.py
```

### Full Pipeline

完整 Amazon 数据流：

```bash
./run_full_pipeline.sh
```

默认行为：

```text
抓取 12 个关键词
每个关键词 50 条商品
下载本地图片
清洗数据
导出人工补标模板
计算 CRITIC 趋势分数
生成 brand recommendations
不调用 GLM
```

只生成 CSV，不下载图片：

```bash
./run_full_pipeline.sh --no-images
```

使用 GLM 补全标签：

```bash
export ZHIPUAI_API_KEY="your_new_api_key_here"
./run_full_pipeline.sh --use-glm-labels
```

使用免费文本模型补标签：

```bash
export ZHIPUAI_API_KEY="your_new_api_key_here"
./run_full_pipeline.sh --use-glm-labels --text-only-glm
```

使用 GLM 生成 Markdown 品牌建议报告：

```bash
export ZHIPUAI_API_KEY="your_new_api_key_here"
./run_full_pipeline.sh --use-glm-report
```

同时使用 GLM 补标签和生成报告：

```bash
export ZHIPUAI_API_KEY="your_new_api_key_here"
./run_full_pipeline.sh --use-glm-labels --use-glm-report
```

可以通过环境变量调整抓取规模：

```bash
ITEMS_PER_QUERY=30 PAGES=1 DELAY=1.5 ./run_full_pipeline.sh
```

## 7. Step-by-step Pipeline

## Step 1: Scrape Amazon Data

运行：

```bash
python scrape_latest_amazon.py
```

默认抓取 12 个 fashion keywords：

```text
bucket hat
denim jacket
floral dress
striped shirt
oversized hoodie
cargo pants
knit cardigan
platform shoes
linen shirt
pleated skirt
leather jacket
wide leg jeans
```

默认设置：

```text
每个关键词保留 50 条商品
每个关键词单独保存 CSV
所有关键词合并为一张总表
```

输出示例：

```text
scraped/amazon_bucket_hat_<timestamp>.csv
scraped/amazon_denim_jacket_<timestamp>.csv
scraped/amazon_fashion_batch_<timestamp>.csv
```

如果只想生成 CSV，不下载图片：

```bash
python scrape_latest_amazon.py --no-images
```

如果需要后续 Markdown 使用本地图片，不要加 `--no-images`。脚本会保存到：

```text
scraped/images_<query>_<timestamp>/0001_<asin>.jpg
```

并在 CSV 的 `local_image_path` 字段中记录路径。品牌建议 Markdown 会优先使用 `local_image_path`；如果本地图片不存在，才回退到 `image_url`。

如果想自定义关键词：

```bash
python scrape_latest_amazon.py --queries "bucket hat,denim jacket,floral dress" --items-per-query 50
```

## Step 2: Raw Data Fields

爬取后总表包含：

```text
scrape_date
source
query
page
page_position
result_rank
is_sponsored
asin
brand_name
product_name
price
currency
price_numeric
rating
rating_numeric
number_of_ratings
number_of_ratings_numeric
derived_gender
derived_style
derived_scene
derived_colour
derived_material
derived_pattern
product_url
image_url
local_image_path
```

重要字段说明：

| Field | Meaning |
| --- | --- |
| `scrape_date` | 抓取时间 |
| `query` | 搜索关键词 |
| `result_rank` | 商品在本次抓取中的排序 |
| `asin` | Amazon 商品编号 |
| `price_numeric` | 可计算价格 |
| `rating_numeric` | 可计算评分 |
| `number_of_ratings_numeric` | 可计算评论/评分数量 |
| `image_url` | 商品图片 URL |
| `derived_*` | 初始 fashion 标签 |

## Step 3: Clean Amazon Data

运行：

```bash
python clean_amazon_data.py scraped/amazon_fashion_batch_20260426_211640.csv
```

当前第一步清洗规则：

```text
删除缺少 rating_numeric 或 number_of_ratings_numeric 的商品
```

原因：

- `rating_numeric` 是商品质量/市场反馈信号
- `number_of_ratings_numeric` 是商品热度/反馈强度信号
- 后续计算 trend score 需要这两个字段

当前清洗结果：

```text
Rows before cleaning: 599
Rows removed: 48
Rows after cleaning: 551
```

输出：

```text
scraped/cleaned/amazon_fashion_batch_20260426_211640_rating_cleaned.csv
scraped/cleaned/amazon_fashion_batch_20260426_211640_cleaning_report.md
```

## Step 4: Label Taxonomy

这些字段是项目自定义标签：

```text
derived_style
derived_scene
derived_colour
derived_material
derived_pattern
```

它们不是 Amazon 原始字段，而是从 `query` 和 `product_name` 中自动推断出来的。

所有标签必须来自固定范围，见：

```text
LABEL_TAXONOMY.md
```

例如：

```text
derived_style:
basic, casual, formal, sporty, party, streetwear, romantic, outdoor, minimal, retro, unknown
```

```text
derived_material:
cotton, denim, polyester, leather, linen, wool, knit, canvas, fleece, silk, synthetic, unknown
```

## Step 5: Export Manual Label Template

如果 `derived_*` 标签为 `unknown`，可以导出人工补标模板：

```bash
python clean_amazon_data.py scraped/amazon_fashion_batch_20260426_211640.csv --export-manual-template
```

输出：

```text
scraped/cleaned/amazon_fashion_batch_20260426_211640_manual_label_template.csv
```

人工填写这些字段：

```text
derived_style
derived_scene
derived_colour
derived_material
derived_pattern
manual_note
```

填完后可以合并回清洗数据：

```bash
python clean_amazon_data.py scraped/amazon_fashion_batch_20260426_211640.csv \
  --manual-labels scraped/cleaned/amazon_fashion_batch_20260426_211640_manual_label_template.csv
```

## Step 6: Fill Labels With GLM

除了人工补标，也可以调用 GLM 视觉/文本模型补全 `unknown` 标签。

脚本：

```text
fill_labels_with_glm.py
```

默认模型：

```text
glm-4.6v-flash
```

这个默认值使用免费视觉/文本 flash 模型，适合本项目“有图片时用图片，没有图片时用文本”的补标任务。

如果只想做纯文本补标，也可以手动指定免费文本模型：

```bash
python fill_labels_with_glm.py scraped/cleaned/amazon_fashion_batch_20260426_211640_rating_cleaned.csv \
  --model glm-4-flash-250414 \
  --no-remote-image
```

安全要求：

```text
不要把 API key 写进代码
不要把 API key 写进 Markdown
使用环境变量 ZHIPUAI_API_KEY
```

设置 API key：

```bash
export ZHIPUAI_API_KEY="your_new_api_key_here"
```

先 dry-run：

```bash
python fill_labels_with_glm.py scraped/cleaned/amazon_fashion_batch_20260426_211640_rating_cleaned.csv --dry-run --limit 10
```

正式运行：

```bash
python fill_labels_with_glm.py scraped/cleaned/amazon_fashion_batch_20260426_211640_rating_cleaned.csv
```

等价于：

```bash
python fill_labels_with_glm.py scraped/cleaned/amazon_fashion_batch_20260426_211640_rating_cleaned.csv \
  --model glm-4.6v-flash
```

如果没有本地图片，脚本会检查 `image_url`。如果你不想使用远程图片，只想基于文本预测：

```bash
python fill_labels_with_glm.py scraped/cleaned/amazon_fashion_batch_20260426_211640_rating_cleaned.csv --no-remote-image
```

GLM 输出仍然必须从 `LABEL_TAXONOMY.md` 的固定范围中选择。

新增审计字段：

```text
glm_model
glm_label_source
glm_label_confidence
glm_label_reason
glm_label_status
glm_raw_response
```

如果 API 返回余额不足、无可用资源包、无权限或限额错误，脚本会停止并保存当前 partial CSV，避免继续消耗时间。

如果免费模型返回：

```text
1305 该模型当前访问量过大，请您稍后再试
```

这表示模型拥堵，不是 key 错误。脚本会自动重试。可以调整：

```bash
python fill_labels_with_glm.py scraped/cleaned/amazon_fashion_batch_20260426_211640_rating_cleaned.csv \
  --model glm-4.6v-flash \
  --max-retries 6 \
  --retry-delay 20
```

如果视觉模型持续拥堵，可以先用免费文本模型完成文本补标：

```bash
python fill_labels_with_glm.py scraped/cleaned/amazon_fashion_batch_20260426_211640_rating_cleaned.csv \
  --model glm-4-flash-250414 \
  --no-remote-image \
  --max-retries 6 \
  --retry-delay 20
```

## Step 7: How Product Data Becomes Trend Signals

单个商品不是趋势。商品只是趋势信号的载体。

转化逻辑：

```text
product
-> extract attributes
-> aggregate labels
-> compare frequency and popularity
-> identify repeated signals
-> generate trend insight
```

例如：

```text
denim jacket + wide leg jeans
-> material = denim
-> style = casual / streetwear
-> repeated across categories
-> denim-based casual dressing trend
```

可聚合字段：

```text
query
derived_style
derived_scene
derived_colour
derived_material
derived_pattern
rating_numeric
number_of_ratings_numeric
result_rank
```

## Step 8: Trend Score via CRITIC Method

趋势分数的权重通过 **CRITIC 方法**（Criteria Importance Through Intercriteria Correlation）从数据中统计学习得出，而非人工指定。

### 为什么不用固定权重

固定权重（如 `0.4 + 0.3 + 0.2 + 0.1`）是主观的，没有统计依据。不同批次数据中各指标的分布和相关性不同，固定权重无法反映数据本身的信息结构。

### CRITIC 方法原理

CRITIC 方法从两个维度衡量每个指标的重要性：

1. **对比强度（Contrast Intensity）**：用标准差衡量。标准差越大，说明该指标在各标签间的区分度越高，信息量越大。
2. **冲突性（Conflict）**：用指标间相关系数衡量。若两个指标高度相关，说明它们携带的信息重叠，应降低其中一个的权重，避免重复计数。

每个指标的信息量定义为：

```text
C_j = σ_j × Σ(1 - r_ij)
```

其中：
- `σ_j`：指标 j 在所有标签上的标准差（对比强度）
- `r_ij`：指标 i 与指标 j 之间的 Pearson 相关系数
- `Σ(1 - r_ij)`：对所有其他指标求和，相关性越低，冲突性越高

最终权重归一化：

```text
w_j = C_j / Σ C_j
```

### 指标定义

对每个标签值（如 `derived_style = "casual"`），计算以下四个指标：

| 指标 | 计算方式 | 含义 |
|------|----------|------|
| `frequency_score` | 该标签出现次数 / 总商品数 | 市场曝光频率 |
| `rating_count_score` | 含该标签商品的评论数均值（log 归一化） | 市场热度强度 |
| `rank_score` | 1 - (含该标签商品的平均排名 / 最大排名) | 搜索结果靠前程度 |
| `cross_category_score` | 含该标签商品覆盖的 query 种类数 / 总 query 数 | 跨品类渗透度 |

### 计算流程

```text
1. 对每个 derived_* 维度（style / scene / colour / material / pattern）分别聚合
2. 每个标签值计算上述四个指标，得到指标矩阵 X (n_labels × 4)
3. 对 X 做 min-max 归一化到 [0, 1]
4. 计算各列标准差 σ_j
5. 计算列间 Pearson 相关矩阵 R
6. 计算每列信息量 C_j = σ_j × Σ(1 - r_ij)
7. 归一化得到权重向量 w
8. trend_score = X × w（加权求和）
```

### 输出示例

```text
Dimension: derived_material
CRITIC weights: frequency=0.31, rating_count=0.28, rank=0.22, cross_category=0.19

Label         trend_score
denim         0.847
cotton        0.763
polyester     0.621
...
```

权重由当前批次数据决定，每次重新运行 `analyze_trends.py` 时自动重新计算。

### 运行趋势分析脚本

脚本：

```text
analyze_trends.py
```

运行：

```bash
python analyze_trends.py scraped/cleaned/amazon_fashion_batch_20260426_211640_rating_cleaned.csv
```

默认不把 `unknown` 标签纳入趋势计算。如果希望保留 `unknown`，可以运行：

```bash
python analyze_trends.py scraped/cleaned/amazon_fashion_batch_20260426_211640_rating_cleaned.csv --include-unknown
```

输出：

```text
analysis/trend_scores_all_dimensions.csv
analysis/critic_weights.csv
analysis/trend_analysis_report.md
analysis/trend_derived_style.csv
analysis/trend_derived_scene.csv
analysis/trend_derived_colour.csv
analysis/trend_derived_material.csv
analysis/trend_derived_pattern.csv
```

### 当前数据是否支持 CRITIC

当前清洗后的 Amazon 数据支持 CRITIC 计算。

输入文件：

```text
scraped/cleaned/amazon_fashion_batch_20260426_211640_rating_cleaned.csv
```

验证结果：

```text
Rows analyzed: 551
Dimensions analyzed: 5
```

核心数值字段没有缺失：

```text
rating_numeric
number_of_ratings_numeric
result_rank
```

当前 CRITIC 输出示例：

```text
derived_material:
cotton   trend_score = 0.811
denim    trend_score = 0.551
knit     trend_score = 0.395
leather  trend_score = 0.391

derived_pattern:
solid    trend_score = 0.814
floral   trend_score = 0.617
striped  trend_score = 0.541

derived_style:
casual   trend_score = 0.837
basic    trend_score = 0.544
sporty   trend_score = 0.512
```

这些结果说明，当前 Amazon 数据已经可以从商品级数据转化为趋势级信号。

## Step 9: Brand Recommendations

趋势分数本身不是结论，需要转化为品牌可执行的建议。这一步的逻辑是：把 `analyze_trends.py` 输出的 `trend_score` 按阈值分级，再映射到具体的产品方向。

### 分级规则

对每个维度（style / colour / material / pattern / scene），按 `trend_score` 将标签分为三级：

| 级别 | 阈值 | 含义 | 建议动作 |
|------|------|------|----------|
| Strong Trend | `trend_score >= 0.6` | 高频、高热度、跨品类 | 主推，优先备货 |
| Weak Signal | `0.3 <= trend_score < 0.6` | 有一定市场存在但不稳定 | 小批量试水，持续观察 |
| Noise | `trend_score < 0.3` | 低频或低热度 | 暂不建议投入 |

阈值基于 min-max 归一化后的 `trend_score`（0 到 1 之间），可根据实际数据分布调整。

### 建议生成逻辑

```text
1. 读取 analysis/trend_scores_all_dimensions.csv
2. 对每个维度，筛选 Strong Trend 标签
3. 组合多个维度的 Strong Trend 标签，生成组合建议
4. 输出品牌建议表
```

组合示例：

```text
Strong Trend 标签：
  derived_material = cotton (0.811)
  derived_style    = casual (0.837)
  derived_colour   = white  (0.72)
  derived_scene    = daily wear (0.79)

→ 建议：推出白色棉质休闲日常系列，优先覆盖 T-shirt、衬衫、宽腿裤品类
```

### 多维度 Strong Trend 组合

强趋势不是孤立标签，而是要组合成产品方向。

例如当前 Amazon 数据中的 Strong Trend 标签包括：

```text
derived_style    = casual
derived_scene    = vacation
derived_colour   = red, denim, black
derived_material = cotton
derived_pattern  = solid, floral
```

这些可以组合成更具体的产品方向：

```text
cotton + casual + vacation
-> lightweight casual vacation products

denim + casual
-> denim-based casual dressing

floral + vacation
-> romantic vacation dressing

solid + cotton
-> minimalist cotton basics
```

### 输出格式

`brand_recommendations.py` 输出两个文件：

```text
analysis/brand_recommendations.csv   — 每行一条建议，含维度、标签、分级、建议动作
analysis/brand_recommendations.md    — 可读报告，按维度分组展示；可选用 GLM 生成
```

`brand_recommendations.csv` 字段：

```text
dimension        — 趋势维度（style / colour / material / pattern / scene）
label            — 标签值（如 casual / cotton / white）
trend_score      — CRITIC 趋势分数
tier             — Strong Trend / Weak Signal / Noise
item_count       — 含该标签的商品数
avg_rating       — 含该标签商品的平均评分
total_rating_count — 含该标签商品的总评论数
query_count      — 覆盖的搜索关键词数
recommendation   — 建议动作文字
```

### 运行

默认本地生成，不调用 GLM：

```bash
python brand_recommendations.py analysis/trend_scores_all_dimensions.csv
```

可选参数：

```bash
# 调整 Strong Trend 阈值（默认 0.6）
python brand_recommendations.py analysis/trend_scores_all_dimensions.csv --strong-threshold 0.65

# 调整 Weak Signal 阈值（默认 0.3）
python brand_recommendations.py analysis/trend_scores_all_dimensions.csv --weak-threshold 0.35
```

输出：

```text
analysis/brand_recommendations.csv
analysis/brand_recommendations.md
```

### 使用 GLM 生成 Markdown 报告

CSV 建议表由规则稳定生成；Markdown 可读报告可以选择调用 GLM 生成。

GLM 会收到以下上下文：

```text
1. Strong / Weak / Noise 分级规则
2. 每个维度的 Strong Trend 标签
3. 每个标签的 trend_score、item_count、avg_rating、total_rating_count、query_count
4. 相关 sample products
5. sample product image_url 作为视觉证据
6. 要求：不能创造标签，只能基于已有上下文写品牌建议
```

生成的 Markdown 需要按每个趋势分成以下结构：

```text
Trend Insight
Evidence
Product Direction
Brand Recommendation
Risk / Validation Note
```

报告会使用爬取到的 `image_url` 生成 Markdown 图片：

```markdown
![product name](image_url)
```

安全要求：

```text
API key 只能通过环境变量 ZHIPUAI_API_KEY 传入
不要写进代码
不要写进 README
```

运行：

```bash
export ZHIPUAI_API_KEY="your_new_api_key_here"

python brand_recommendations.py analysis/trend_scores_all_dimensions.csv \
  --use-glm \
  --products-csv scraped/cleaned/amazon_fashion_batch_20260426_211640_rating_cleaned.csv
```

如果不加 `--use-glm`，则不会调用 API，而是使用本地模板生成 `brand_recommendations.md`。

### 当前验证结果

当前数据已成功生成：

```text
analysis/brand_recommendations.csv
analysis/brand_recommendations.md
```

分级结果：

```text
Strong Trend: 8
Weak Signal: 20
Noise: 12
```

当前 Strong Trend 标签：

```text
derived_style: casual
derived_scene: vacation
derived_colour: red, denim, black
derived_material: cotton
derived_pattern: solid, floral
```

## 10. Ethics and Risk

本模块只采集公开 Amazon 搜索结果页面中可见的信息。

注意事项：

- 小规模、低频率采集
- 只用于课程研究
- 不采集私人信息
- 不绕过登录、付费墙或隐私限制
- 标记 sponsored products
- 不把平台排序直接等同于真实趋势

潜在偏差：

- Amazon 搜索结果受广告影响
- 平台排序算法不可见
- 搜索关键词由研究者设定，存在主观性
- 商品名称可能不完整，自动标签可能误判

应对方法：

- 保留 `is_sponsored`
- 保留 `query`
- 保留 `scrape_date`
- 使用固定 taxonomy
- 允许人工或 GLM 辅助补标
- 后续结合 TikTok 和 Telegram 等其他来源交叉验证

## 11. Expected Outputs for Assignment

这个 Amazon 模块最终可以提供：

```text
raw Amazon product dataset
cleaned Amazon product dataset
manual label template
cleaning report
label taxonomy
AI-assisted label completion script
trend-ready product metadata
```

这些文件可以在报告中支持：

- 数据来源说明
- 数据预处理流程
- 多模态数据说明
- AI-assisted data curation
- 初步趋势分析
- 伦理和风险说明

## 12. Short Summary

Amazon pipeline 用当前搜索结果页面采集最新商品数据，保存商品文本、价格、评分、评论数量、图片链接和初始 fashion 标签。随后通过清洗脚本删除缺少市场反馈信号的商品，再使用固定 taxonomy、人工补标或 GLM 视觉/文本模型补全标签。处理后的数据可以用于统计颜色、材质、图案、风格和场景等趋势信号。

## 13. Sample Output Preview

下面是 `brand_recommendations.py` 生成的最终 Markdown 报告样例。报告会把 CRITIC 趋势分数、商品证据和爬取到的商品图片组合在一起，形成面向品牌的趋势建议。

完整样例文件：

```text
analysis/demo_recommendations_structured/brand_recommendations.md
analysis/brand_recommendations.md
```

### Example Trend Insight

当前样例中，Amazon 商品数据得到的主要强趋势包括：

```text
style: casual
pattern: solid, floral
material: cotton
colour: red, denim, black
scene: vacation
```

这些标签会进一步组合成产品方向，例如：

```text
Develop products around cotton with casual positioning, for vacation.
Use red, denim, black as colour direction and solid, floral as visual surface direction.
```

### Example Visual Evidence

| Trend Signal | Product Evidence | Image |
| --- | --- | --- |
| `casual` style | Striped shirt, rating 3.7, 1803 ratings | ![casual striped shirt](https://m.media-amazon.com/images/I/61SB14qT0EL._AC_UL320_.jpg) |
| `solid` pattern | Linen cotton shirt, rating 3.2, 746 ratings | ![solid linen shirt](https://m.media-amazon.com/images/I/81I4F9xgijL._AC_UL320_.jpg) |
| `denim` colour/material direction | Denim jacket, strong cross-query signal | ![denim jacket](https://m.media-amazon.com/images/I/51g+JumJl9L._AC_UL320_.jpg) |

### Example Recommendation Format

每个强趋势在最终报告中都会按照下面结构输出：

```text
Trend Insight
Evidence
Product Direction
Brand Recommendation
Risk / Validation Note
```

这样最终结果不是停留在“某个商品很热门”，而是把单品证据转化为可解释、可验证、可执行的品牌趋势方向。
