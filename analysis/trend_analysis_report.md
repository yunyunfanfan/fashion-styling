# Amazon Trend Analysis Report

## Input Summary

- Rows: 551
- Queries: 12
- Include unknown labels: False

## CRITIC Criteria

- `frequency_score`: label frequency in all products
- `rating_count_score`: log-normalized average rating count
- `rank_score`: higher when products rank closer to the top
- `cross_category_score`: label coverage across search queries

## CRITIC Weights

### derived_style

- `frequency_score`: 0.2275
- `rating_count_score`: 0.2446
- `rank_score`: 0.2884
- `cross_category_score`: 0.2395

### derived_scene

- `frequency_score`: 0.2265
- `rating_count_score`: 0.1577
- `rank_score`: 0.3948
- `cross_category_score`: 0.2210

### derived_colour

- `frequency_score`: 0.2190
- `rating_count_score`: 0.2619
- `rank_score`: 0.2536
- `cross_category_score`: 0.2655

### derived_material

- `frequency_score`: 0.2130
- `rating_count_score`: 0.2208
- `rank_score`: 0.3363
- `cross_category_score`: 0.2298

### derived_pattern

- `frequency_score`: 0.2717
- `rating_count_score`: 0.2120
- `rank_score`: 0.3097
- `cross_category_score`: 0.2066

## Top Trend Labels

### derived_style

```text
 label  trend_score  item_count  avg_rating  total_rating_count  query_count
casual     0.836696         212    3.783019             81556.0           12
 basic     0.543558          47    3.763830             18521.0            9
sporty     0.512286           3    3.933333              1165.0            2
formal     0.299881          10    3.920000              5899.0            3
 party     0.000000           2    3.650000                 9.0            2
```

### derived_scene

```text
     label  trend_score  item_count  avg_rating  total_rating_count  query_count
  vacation     0.665793          90    3.871111             60187.0           10
daily wear     0.567944         109    3.857798             46625.0           10
   outdoor     0.480121           3    4.033333               842.0            2
      work     0.475244          27    3.681481             14416.0            6
     party     0.113079          11    3.545455              1105.0            3
```

### derived_colour

```text
label  trend_score  item_count  avg_rating  total_rating_count  query_count
  red     0.786291          31    3.803226             21435.0            8
denim     0.771470          71    3.856338             70605.0            4
black     0.694945          29    3.751724             10042.0            7
white     0.565762           9    3.444444              5158.0            5
 navy     0.542476           2    4.100000              2094.0            2
 blue     0.532451          13    3.969231              2424.0            7
 pink     0.460849           6    4.033333               677.0            4
multi     0.406396           9    3.955556              1834.0            3
brown     0.397170           5    3.980000              6825.0            2
 grey     0.299272           4    3.575000                87.0            2
```

### derived_material

```text
    label  trend_score  item_count  avg_rating  total_rating_count  query_count
   cotton     0.811043         146    3.869178             84957.0           10
    denim     0.551303          68    3.882353             69124.0            3
polyester     0.458947           2    3.900000               211.0            2
     knit     0.394882          28    3.667857              5585.0            2
  leather     0.391339          43    3.790698              8524.0            2
    linen     0.327283          22    3.581818              5121.0            1
   fleece     0.241713           2    4.100000                74.0            1
     wool     0.213831          10    3.840000               570.0            2
synthetic     0.000000           1    4.000000                18.0            1
```

### derived_pattern

```text
      label  trend_score  item_count  avg_rating  total_rating_count  query_count
      solid     0.813533          55    3.723636             36120.0           11
     floral     0.617266          57    3.822807             26002.0            4
    striped     0.541258          48    3.916667             20991.0            2
embroidered     0.452900           1    4.100000               134.0            1
    printed     0.363964          16    3.943750              2596.0            3
 reversible     0.335861          11    4.081818              1459.0            1
     stripe     0.250767           1    4.100000               126.0            1
      check     0.182995           2    2.050000                 8.0            2
    graphic     0.169546           2    4.100000               441.0            1
```
