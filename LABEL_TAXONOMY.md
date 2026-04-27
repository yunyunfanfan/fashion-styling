# Fashion Label Taxonomy

## Purpose

`derived_style`、`derived_scene`、`derived_colour`、`derived_material` 和 `derived_pattern` 是项目自定义的策展标签，不是 Amazon 原始字段。

这些字段由两种方式产生：

1. 规则自动推断：从 `query` 和 `product_name` 中识别关键词。
2. 人工补标：对自动识别为 `unknown` 或明显错误的样本进行人工修正。

为了保证后续统计一致，人工补标时应尽量从下面的固定词表中选择。

## derived_style

用于描述商品整体风格。

Allowed values:

```text
basic
casual
formal
sporty
party
streetwear
romantic
outdoor
minimal
retro
unknown
```

Examples:

| Signal | Label |
| --- | --- |
| classic, regular, basic | `basic` |
| casual, daily, hoodie, loose | `casual` |
| office, business, formal | `formal` |
| sport, gym, running, training | `sporty` |
| party, glitter, sequin | `party` |
| cargo, oversized, street, urban | `streetwear` |
| floral, lace, feminine | `romantic` |
| hiking, travel, sun protection | `outdoor` |

## derived_scene

用于描述商品适合的使用场景。

Allowed values:

```text
daily wear
work
party
vacation
outdoor
sport
home
school
unknown
```

Examples:

| Signal | Label |
| --- | --- |
| casual, daily, everyday | `daily wear` |
| office, work, business | `work` |
| party, evening, club | `party` |
| beach, summer, travel, vacation | `vacation` |
| hiking, outdoor, sun protection | `outdoor` |
| gym, running, training | `sport` |

## derived_colour

用于描述主要颜色。若商品名出现多个颜色，优先选最明确或最靠前的主色；如果是多色设计，用 `multi`。

Allowed values:

```text
black
white
blue
denim
grey
green
red
pink
brown
beige
khaki
yellow
purple
orange
navy
cream
multi
unknown
```

Notes:

- `denim` 可以作为颜色，也可以作为材质。
- 如果商品名只写 “multicolour” 或 “multi colour”，用 `multi`。

## derived_material

用于描述主要材质。

Allowed values:

```text
cotton
denim
polyester
leather
linen
wool
knit
canvas
fleece
silk
synthetic
unknown
```

Examples:

| Signal | Label |
| --- | --- |
| jeans, denim jacket | `denim` |
| knit cardigan, knitted | `knit` |
| leather jacket | `leather` |
| linen shirt | `linen` |
| cotton bucket hat | `cotton` |

## derived_pattern

用于描述视觉图案或表面设计。

Allowed values:

```text
solid
striped
floral
printed
embroidered
check
plaid
graphic
reversible
unknown
```

Examples:

| Signal | Label |
| --- | --- |
| plain, solid | `solid` |
| stripe, striped | `striped` |
| floral, flower | `floral` |
| print, printed | `printed` |
| embroidery, embroidered | `embroidered` |
| check, checked | `check` |
| plaid | `plaid` |
| graphic | `graphic` |
| reversible | `reversible` |

## Manual Labeling Rules

人工补标时遵循以下原则：

1. 不确定就填 `unknown`，不要猜。
2. 优先根据 `product_name` 判断。
3. 如果有图片，可以结合 `image_url` 或本地图片判断。
4. 每个字段只填一个主标签，方便统计。
5. 如果商品有多个特征，选择最能代表趋势的一个。
6. 修改过的行可以在 `manual_note` 里写原因。

## Manual Labeling Workflow

先生成需要人工补标的模板：

```bash
python clean_amazon_data.py scraped/amazon_fashion_batch_20260426_211640.csv --export-manual-template
```

输出：

```text
scraped/cleaned/amazon_fashion_batch_20260426_211640_manual_label_template.csv
```

人工填写模板里的这些字段：

```text
derived_style
derived_scene
derived_colour
derived_material
derived_pattern
manual_note
```

然后将人工标签合并回清洗数据：

```bash
python clean_amazon_data.py scraped/amazon_fashion_batch_20260426_211640.csv \
  --manual-labels scraped/cleaned/amazon_fashion_batch_20260426_211640_manual_label_template.csv
```

这样可以保证人工补标过程可追踪、可复现。

## GLM-assisted Label Completion

除了人工补标，也可以使用 GLM 视觉/文本模型补全 `unknown` 标签。

原则：

1. 每个字段必须从本文件的 allowed values 中选择。
2. 不允许模型创造新标签。
3. 如果证据不足，必须返回 `unknown`。
4. 如果存在本地图片，优先使用本地图片。
5. 如果没有本地图片，但有 `image_url`，可以使用远程图片 URL。
6. 如果没有图片，则只使用文本字段进行预测。
7. API key 只能通过环境变量读取，不能写进代码或文档。

设置 API key：

```bash
export ZHIPUAI_API_KEY="your_new_api_key_here"
```

先 dry-run 查看哪些行会被补标：

```bash
python fill_labels_with_glm.py scraped/cleaned/amazon_fashion_batch_20260426_211640_rating_cleaned.csv --dry-run --limit 10
```

正式补标：

```bash
python fill_labels_with_glm.py scraped/cleaned/amazon_fashion_batch_20260426_211640_rating_cleaned.csv
```

如果只想用文本，不使用远程图片 URL：

```bash
python fill_labels_with_glm.py scraped/cleaned/amazon_fashion_batch_20260426_211640_rating_cleaned.csv --no-remote-image
```

输出文件：

```text
scraped/cleaned/amazon_fashion_batch_20260426_211640_rating_cleaned_glm_labeled.csv
```

新增记录字段：

```text
glm_label_source
glm_label_confidence
glm_label_reason
glm_label_status
```
