# Amazon Brand Recommendations

## Tier Rules

- Strong Trend: `trend_score >= 0.6`
- Weak Signal: `0.3 <= trend_score < 0.6`
- Noise: `trend_score < 0.3`

## Combined Product Direction

Develop products around cotton with casual positioning, for vacation. Use red, denim, black as colour direction and solid, floral as visual surface direction.

## Strong Trend Labels

### derived_style

```text
 label  trend_score  item_count  avg_rating  total_rating_count  query_count
casual     0.836696         212    3.783019             81556.0           12
```

### derived_pattern

```text
 label  trend_score  item_count  avg_rating  total_rating_count  query_count
 solid     0.813533          55    3.723636             36120.0           11
floral     0.617266          57    3.822807             26002.0            4
```

### derived_material

```text
 label  trend_score  item_count  avg_rating  total_rating_count  query_count
cotton     0.811043         146    3.869178             84957.0           10
```

### derived_colour

```text
label  trend_score  item_count  avg_rating  total_rating_count  query_count
  red     0.786291          31    3.803226             21435.0            8
denim     0.771470          71    3.856338             70605.0            4
black     0.694945          29    3.751724             10042.0            7
```

### derived_scene

```text
   label  trend_score  item_count  avg_rating  total_rating_count  query_count
vacation     0.665793          90    3.871111             60187.0           10
```

## Trend Recommendations

### casual (style)

#### Trend Insight

`casual` is the strongest styling signal, suggesting demand for broadly wearable fashion directions.

#### Evidence

- Trend score: `0.837`
- Product count: `212`
- Query coverage: `12` categories
- Average rating: `3.78`
- Total rating count: `81556`

Visual evidence:

![striped shirt: U TURN - U TURN Men's Casual Printed Striped Stylish Latest Formal Shirt for Men](https://m.media-amazon.com/images/I/61SB14qT0EL._AC_UL320_.jpg)
- striped shirt: U TURN - U TURN Men's Casual Printed Striped Stylish Latest Formal Shirt for Men
  Rating: 3.7; rating count: 1803
  Image: https://m.media-amazon.com/images/I/61SB14qT0EL._AC_UL320_.jpg
  Source image URL: https://m.media-amazon.com/images/I/61SB14qT0EL._AC_UL320_.jpg

![platform shoes: Vendoz - Vendoz Women White Casual Sneakers](https://m.media-amazon.com/images/I/71SGV-4lI9L._AC_UL320_.jpg)
- platform shoes: Vendoz - Vendoz Women White Casual Sneakers
  Rating: 3.8; rating count: 1698
  Image: https://m.media-amazon.com/images/I/71SGV-4lI9L._AC_UL320_.jpg
  Source image URL: https://m.media-amazon.com/images/I/71SGV-4lI9L._AC_UL320_.jpg

![linen shirt: NexaFlair - NexaFlair Men's Solid Linen Cotton Shirt | Casual | Plain | Full Sleeve | Summer-Regular Fit| Men Stylish Shirt | Everyday...](https://m.media-amazon.com/images/I/81I4F9xgijL._AC_UL320_.jpg)
- linen shirt: NexaFlair - NexaFlair Men's Solid Linen Cotton Shirt | Casual | Plain | Full Sleeve | Summer-Regular Fit| Men Stylish Shirt | Everyday...
  Rating: 3.2; rating count: 746
  Image: https://m.media-amazon.com/images/I/81I4F9xgijL._AC_UL320_.jpg
  Source image URL: https://m.media-amazon.com/images/I/81I4F9xgijL._AC_UL320_.jpg

#### Product Direction

Build a capsule around casual styling, using the strongest material, colour, and pattern signals as supporting design choices.

#### Brand Recommendation

Prioritize this signal in assortment planning, product naming, and campaign visuals. Validate with TikTok and Telegram before treating it as a cross-platform trend.

#### Risk / Validation Note

This signal is based on Amazon search results, which may be affected by sponsored placement, platform ranking, keyword choice, and incomplete automatic labels. Treat it as an e-commerce signal, not a final market truth.

### solid (pattern)

#### Trend Insight

`solid` is a strong visual-surface signal and can guide print, graphic, and pattern direction.

#### Evidence

- Trend score: `0.814`
- Product count: `55`
- Query coverage: `11` categories
- Average rating: `3.72`
- Total rating count: `36120`

Visual evidence:

![linen shirt: NexaFlair - NexaFlair Men's Solid Linen Cotton Shirt | Casual | Plain | Full Sleeve | Summer-Regular Fit| Men Stylish Shirt | Everyday...](https://m.media-amazon.com/images/I/81I4F9xgijL._AC_UL320_.jpg)
- linen shirt: NexaFlair - NexaFlair Men's Solid Linen Cotton Shirt | Casual | Plain | Full Sleeve | Summer-Regular Fit| Men Stylish Shirt | Everyday...
  Rating: 3.2; rating count: 746
  Image: https://m.media-amazon.com/images/I/81I4F9xgijL._AC_UL320_.jpg
  Source image URL: https://m.media-amazon.com/images/I/81I4F9xgijL._AC_UL320_.jpg

![oversized hoodie: The Modern Soul - The Modern Soul Half Zipper Solid Hoodie for Men | Sweatshirt for Men](https://m.media-amazon.com/images/I/31B+tV6-28L._AC_UL320_.jpg)
- oversized hoodie: The Modern Soul - The Modern Soul Half Zipper Solid Hoodie for Men | Sweatshirt for Men
  Rating: 3.7; rating count: 435
  Image: https://m.media-amazon.com/images/I/31B+tV6-28L._AC_UL320_.jpg
  Source image URL: https://m.media-amazon.com/images/I/31B+tV6-28L._AC_UL320_.jpg

![linen shirt: NexaFlair - NexaFlair Men's Solid Linen Cotton Shirt | Casual | Plain | Full Sleeve | Summer-Regular Fit| Men Stylish Shirt | Everyday...](https://m.media-amazon.com/images/I/81qh45dSlgL._AC_UL320_.jpg)
- linen shirt: NexaFlair - NexaFlair Men's Solid Linen Cotton Shirt | Casual | Plain | Full Sleeve | Summer-Regular Fit| Men Stylish Shirt | Everyday...
  Rating: 3.2; rating count: 746
  Image: https://m.media-amazon.com/images/I/81qh45dSlgL._AC_UL320_.jpg
  Source image URL: https://m.media-amazon.com/images/I/81qh45dSlgL._AC_UL320_.jpg

#### Product Direction

Develop solid surface treatments across relevant products, then validate with social and community sources.

#### Brand Recommendation

Prioritize this signal in assortment planning, product naming, and campaign visuals. Validate with TikTok and Telegram before treating it as a cross-platform trend.

#### Risk / Validation Note

This signal is based on Amazon search results, which may be affected by sponsored placement, platform ranking, keyword choice, and incomplete automatic labels. Treat it as an e-commerce signal, not a final market truth.

### cotton (material)

#### Trend Insight

`cotton` is a strong material signal and can guide fabric, texture, and sourcing decisions.

#### Evidence

- Trend score: `0.811`
- Product count: `146`
- Query coverage: `10` categories
- Average rating: `3.87`
- Total rating count: `84957`

Visual evidence:

![linen shirt: NexaFlair - NexaFlair Men's Solid Linen Cotton Shirt | Casual | Plain | Full Sleeve | Summer-Regular Fit| Men Stylish Shirt | Everyday...](https://m.media-amazon.com/images/I/81I4F9xgijL._AC_UL320_.jpg)
- linen shirt: NexaFlair - NexaFlair Men's Solid Linen Cotton Shirt | Casual | Plain | Full Sleeve | Summer-Regular Fit| Men Stylish Shirt | Everyday...
  Rating: 3.2; rating count: 746
  Image: https://m.media-amazon.com/images/I/81I4F9xgijL._AC_UL320_.jpg
  Source image URL: https://m.media-amazon.com/images/I/81I4F9xgijL._AC_UL320_.jpg

![oversized hoodie: NETCLICK - NETCLICK Los Angeles Printed Hoodies Sweatshirt Polycotton for Running, Gym Warm Travel Hoodies for Men](https://m.media-amazon.com/images/I/41DB2PzxvtL._AC_UL320_.jpg)
- oversized hoodie: NETCLICK - NETCLICK Los Angeles Printed Hoodies Sweatshirt Polycotton for Running, Gym Warm Travel Hoodies for Men
  Rating: 4.0; rating count: 227
  Image: https://m.media-amazon.com/images/I/41DB2PzxvtL._AC_UL320_.jpg
  Source image URL: https://m.media-amazon.com/images/I/41DB2PzxvtL._AC_UL320_.jpg

![cargo pants: Lymio - Lymio Cargo for Men || Cotton Cargo Pant || Drawstring Waist Pant (Also Available in Plus Sizes) (145-148)](https://m.media-amazon.com/images/I/61VzbIFEk4L._AC_UL320_.jpg)
- cargo pants: Lymio - Lymio Cargo for Men || Cotton Cargo Pant || Drawstring Waist Pant (Also Available in Plus Sizes) (145-148)
  Rating: 4.2; rating count: 147
  Image: https://m.media-amazon.com/images/I/61VzbIFEk4L._AC_UL320_.jpg
  Source image URL: https://m.media-amazon.com/images/I/61VzbIFEk4L._AC_UL320_.jpg

#### Product Direction

Prioritize cotton in core products and test adjacent categories where the material supports comfort, durability, or seasonal relevance.

#### Brand Recommendation

Prioritize this signal in assortment planning, product naming, and campaign visuals. Validate with TikTok and Telegram before treating it as a cross-platform trend.

#### Risk / Validation Note

This signal is based on Amazon search results, which may be affected by sponsored placement, platform ranking, keyword choice, and incomplete automatic labels. Treat it as an e-commerce signal, not a final market truth.

### red (colour)

#### Trend Insight

`red` is a strong colour signal and can guide palette selection for product and visual merchandising.

#### Evidence

- Trend score: `0.786`
- Product count: `31`
- Query coverage: `8` categories
- Average rating: `3.8`
- Total rating count: `21435`

Visual evidence:

![floral dress: Generic - Women's Pink Bandhani Print Tiered Maxi Dress, Short Sleeve, Square Neck, Cotton](https://m.media-amazon.com/images/I/61RR8+DmkLL._AC_UL320_.jpg)
- floral dress: Generic - Women's Pink Bandhani Print Tiered Maxi Dress, Short Sleeve, Square Neck, Cotton
  Rating: 3.3; rating count: 64
  Image: https://m.media-amazon.com/images/I/61RR8+DmkLL._AC_UL320_.jpg
  Source image URL: https://m.media-amazon.com/images/I/61RR8+DmkLL._AC_UL320_.jpg

![linen shirt: NexaFlair - NexaFlair Man's Casual | Formal | Linen| Cotton | Regular Wear Collared | Fit Shirt for Men](https://m.media-amazon.com/images/I/61ykgVB3xHL._AC_UL320_.jpg)
- linen shirt: NexaFlair - NexaFlair Man's Casual | Formal | Linen| Cotton | Regular Wear Collared | Fit Shirt for Men
  Rating: 2.8; rating count: 17
  Image: https://m.media-amazon.com/images/I/61ykgVB3xHL._AC_UL320_.jpg
  Source image URL: https://m.media-amazon.com/images/I/61ykgVB3xHL._AC_UL320_.jpg

![floral dress: Modestouze Attires - Modestouze Attires Dress for Women Western Maxi Style, Indo Western Dresses, One Piece Long Gown, A Line Flared Pattern, E...](https://m.media-amazon.com/images/I/61QQbNKtCGL._AC_UL320_.jpg)
- floral dress: Modestouze Attires - Modestouze Attires Dress for Women Western Maxi Style, Indo Western Dresses, One Piece Long Gown, A Line Flared Pattern, E...
  Rating: 4.3; rating count: 104
  Image: https://m.media-amazon.com/images/I/61QQbNKtCGL._AC_UL320_.jpg
  Source image URL: https://m.media-amazon.com/images/I/61QQbNKtCGL._AC_UL320_.jpg

#### Product Direction

Use red as a hero colour or recurring accent across selected categories.

#### Brand Recommendation

Prioritize this signal in assortment planning, product naming, and campaign visuals. Validate with TikTok and Telegram before treating it as a cross-platform trend.

#### Risk / Validation Note

This signal is based on Amazon search results, which may be affected by sponsored placement, platform ranking, keyword choice, and incomplete automatic labels. Treat it as an e-commerce signal, not a final market truth.

### denim (colour)

#### Trend Insight

`denim` is a strong colour signal and can guide palette selection for product and visual merchandising.

#### Evidence

- Trend score: `0.771`
- Product count: `71`
- Query coverage: `4` categories
- Average rating: `3.86`
- Total rating count: `70605`

Visual evidence:

![denim jacket: GRECIILOOKS - GRECIILOOKS Men’S Denim Jacket | Classic Regular Fit Jeans Jacket For Men | Stylish Branded Jackets For Men – Timeless Cas...](https://m.media-amazon.com/images/I/51g+JumJl9L._AC_UL320_.jpg)
- denim jacket: GRECIILOOKS - GRECIILOOKS Men’S Denim Jacket | Classic Regular Fit Jeans Jacket For Men | Stylish Branded Jackets For Men – Timeless Cas...
  Rating: 3.8; rating count: 239
  Image: https://m.media-amazon.com/images/I/51g+JumJl9L._AC_UL320_.jpg
  Source image URL: https://m.media-amazon.com/images/I/51g+JumJl9L._AC_UL320_.jpg

![wide leg jeans: KCM FASHION - High-Waisted Wide-Leg Jeans Featuring a Relaxed fit Silhouette and Classic Denim for Versatile Casual wear](https://m.media-amazon.com/images/I/41aQZIqSbQL._AC_UL320_.jpg)
- wide leg jeans: KCM FASHION - High-Waisted Wide-Leg Jeans Featuring a Relaxed fit Silhouette and Classic Denim for Versatile Casual wear
  Rating: 3.6; rating count: 14
  Image: https://m.media-amazon.com/images/I/41aQZIqSbQL._AC_UL320_.jpg
  Source image URL: https://m.media-amazon.com/images/I/41aQZIqSbQL._AC_UL320_.jpg

![denim jacket: Urbano Fashion - Urbano Fashion Men's Regular Fit Washed Full Sleeve Denim Jacket](https://m.media-amazon.com/images/I/71e5Iu8ju8L._AC_UL320_.jpg)
- denim jacket: Urbano Fashion - Urbano Fashion Men's Regular Fit Washed Full Sleeve Denim Jacket
  Rating: 3.8; rating count: 2957
  Image: https://m.media-amazon.com/images/I/71e5Iu8ju8L._AC_UL320_.jpg
  Source image URL: https://m.media-amazon.com/images/I/71e5Iu8ju8L._AC_UL320_.jpg

#### Product Direction

Use denim as a hero colour or recurring accent across selected categories.

#### Brand Recommendation

Prioritize this signal in assortment planning, product naming, and campaign visuals. Validate with TikTok and Telegram before treating it as a cross-platform trend.

#### Risk / Validation Note

This signal is based on Amazon search results, which may be affected by sponsored placement, platform ranking, keyword choice, and incomplete automatic labels. Treat it as an e-commerce signal, not a final market truth.

### black (colour)

#### Trend Insight

`black` is a strong colour signal and can guide palette selection for product and visual merchandising.

#### Evidence

- Trend score: `0.695`
- Product count: `29`
- Query coverage: `7` categories
- Average rating: `3.75`
- Total rating count: `10042`

Visual evidence:

![floral dress: MASIYALA - MASIYALA Women's Floral Print Maxi Dress, Black with Pink Flowers, Short Sleeve, A-Line Style](https://m.media-amazon.com/images/I/61yVG8Qe+FL._AC_UL320_.jpg)
- floral dress: MASIYALA - MASIYALA Women's Floral Print Maxi Dress, Black with Pink Flowers, Short Sleeve, A-Line Style
  Rating: 3.6; rating count: 18
  Image: https://m.media-amazon.com/images/I/61yVG8Qe+FL._AC_UL320_.jpg
  Source image URL: https://m.media-amazon.com/images/I/61yVG8Qe+FL._AC_UL320_.jpg

![leather jacket: EXOTIX - EXOTIX Black Leather Jacket for Men | Collared Zip-Up Classic Style | Crop Fit Racing Sports Bomber Jacket | Premium Leath...](https://m.media-amazon.com/images/I/51aa6X0QOmL._AC_UL320_.jpg)
- leather jacket: EXOTIX - EXOTIX Black Leather Jacket for Men | Collared Zip-Up Classic Style | Crop Fit Racing Sports Bomber Jacket | Premium Leath...
  Rating: 3.0; rating count: 4
  Image: https://m.media-amazon.com/images/I/51aa6X0QOmL._AC_UL320_.jpg
  Source image URL: https://m.media-amazon.com/images/I/51aa6X0QOmL._AC_UL320_.jpg

![leather jacket: EXOTIX - EXOTIX Men's Black Leather Jacket | Collared Zip-Up, Classic Style | Black Crop Leather Jacket | Racing Sports Regular Bom...](https://m.media-amazon.com/images/I/61cW3rD6GqL._AC_UL320_.jpg)
- leather jacket: EXOTIX - EXOTIX Men's Black Leather Jacket | Collared Zip-Up, Classic Style | Black Crop Leather Jacket | Racing Sports Regular Bom...
  Rating: 5.0; rating count: 1
  Image: https://m.media-amazon.com/images/I/61cW3rD6GqL._AC_UL320_.jpg
  Source image URL: https://m.media-amazon.com/images/I/61cW3rD6GqL._AC_UL320_.jpg

#### Product Direction

Use black as a hero colour or recurring accent across selected categories.

#### Brand Recommendation

Prioritize this signal in assortment planning, product naming, and campaign visuals. Validate with TikTok and Telegram before treating it as a cross-platform trend.

#### Risk / Validation Note

This signal is based on Amazon search results, which may be affected by sponsored placement, platform ranking, keyword choice, and incomplete automatic labels. Treat it as an e-commerce signal, not a final market truth.

### vacation (scene)

#### Trend Insight

`vacation` appears as a strong wearing-context signal, indicating where customers may imagine using these products.

#### Evidence

- Trend score: `0.666`
- Product count: `90`
- Query coverage: `10` categories
- Average rating: `3.87`
- Total rating count: `60187`

Visual evidence:

![linen shirt: NexaFlair - NexaFlair Men's Solid Linen Cotton Shirt | Casual | Plain | Full Sleeve | Summer-Regular Fit| Men Stylish Shirt | Everyday...](https://m.media-amazon.com/images/I/81I4F9xgijL._AC_UL320_.jpg)
- linen shirt: NexaFlair - NexaFlair Men's Solid Linen Cotton Shirt | Casual | Plain | Full Sleeve | Summer-Regular Fit| Men Stylish Shirt | Everyday...
  Rating: 3.2; rating count: 746
  Image: https://m.media-amazon.com/images/I/81I4F9xgijL._AC_UL320_.jpg
  Source image URL: https://m.media-amazon.com/images/I/81I4F9xgijL._AC_UL320_.jpg

![oversized hoodie: NETCLICK - NETCLICK Los Angeles Printed Hoodies Sweatshirt Polycotton for Running, Gym Warm Travel Hoodies for Men](https://m.media-amazon.com/images/I/41DB2PzxvtL._AC_UL320_.jpg)
- oversized hoodie: NETCLICK - NETCLICK Los Angeles Printed Hoodies Sweatshirt Polycotton for Running, Gym Warm Travel Hoodies for Men
  Rating: 4.0; rating count: 227
  Image: https://m.media-amazon.com/images/I/41DB2PzxvtL._AC_UL320_.jpg
  Source image URL: https://m.media-amazon.com/images/I/41DB2PzxvtL._AC_UL320_.jpg

![knit cardigan: Generic - Women’s Cropped Tie-Front Shrug Cardigan | Soft Ribbed Knit Long Sleeve V-Neck Top | Stylish Summer Cardigan, Casual Beach...](https://m.media-amazon.com/images/I/513c3fVae2L._AC_UL320_.jpg)
- knit cardigan: Generic - Women’s Cropped Tie-Front Shrug Cardigan | Soft Ribbed Knit Long Sleeve V-Neck Top | Stylish Summer Cardigan, Casual Beach...
  Rating: 3.8; rating count: 73
  Image: https://m.media-amazon.com/images/I/513c3fVae2L._AC_UL320_.jpg
  Source image URL: https://m.media-amazon.com/images/I/513c3fVae2L._AC_UL320_.jpg

#### Product Direction

Design products and campaign styling around vacation occasions, with product names and visuals that make the usage context explicit.

#### Brand Recommendation

Prioritize this signal in assortment planning, product naming, and campaign visuals. Validate with TikTok and Telegram before treating it as a cross-platform trend.

#### Risk / Validation Note

This signal is based on Amazon search results, which may be affected by sponsored placement, platform ranking, keyword choice, and incomplete automatic labels. Treat it as an e-commerce signal, not a final market truth.

### floral (pattern)

#### Trend Insight

`floral` is a strong visual-surface signal and can guide print, graphic, and pattern direction.

#### Evidence

- Trend score: `0.617`
- Product count: `57`
- Query coverage: `4` categories
- Average rating: `3.82`
- Total rating count: `26002`

Visual evidence:

![floral dress: MASIYALA - MASIYALA Women's Floral Print Maxi Dress, Black with Pink Flowers, Short Sleeve, A-Line Style](https://m.media-amazon.com/images/I/61yVG8Qe+FL._AC_UL320_.jpg)
- floral dress: MASIYALA - MASIYALA Women's Floral Print Maxi Dress, Black with Pink Flowers, Short Sleeve, A-Line Style
  Rating: 3.6; rating count: 18
  Image: https://m.media-amazon.com/images/I/61yVG8Qe+FL._AC_UL320_.jpg
  Source image URL: https://m.media-amazon.com/images/I/61yVG8Qe+FL._AC_UL320_.jpg

![floral dress: Generic - Women's Pink Bandhani Print Tiered Maxi Dress, Short Sleeve, Square Neck, Cotton](https://m.media-amazon.com/images/I/61RR8+DmkLL._AC_UL320_.jpg)
- floral dress: Generic - Women's Pink Bandhani Print Tiered Maxi Dress, Short Sleeve, Square Neck, Cotton
  Rating: 3.3; rating count: 64
  Image: https://m.media-amazon.com/images/I/61RR8+DmkLL._AC_UL320_.jpg
  Source image URL: https://m.media-amazon.com/images/I/61RR8+DmkLL._AC_UL320_.jpg

![floral dress: Modestouze Attires - Modestouze Attires Dress for Women Western Maxi Style, Indo Western Dresses, One Piece Long Gown, A Line Flared Pattern, E...](https://m.media-amazon.com/images/I/61QQbNKtCGL._AC_UL320_.jpg)
- floral dress: Modestouze Attires - Modestouze Attires Dress for Women Western Maxi Style, Indo Western Dresses, One Piece Long Gown, A Line Flared Pattern, E...
  Rating: 4.3; rating count: 104
  Image: https://m.media-amazon.com/images/I/61QQbNKtCGL._AC_UL320_.jpg
  Source image URL: https://m.media-amazon.com/images/I/61QQbNKtCGL._AC_UL320_.jpg

#### Product Direction

Develop floral surface treatments across relevant products, then validate with social and community sources.

#### Brand Recommendation

Prioritize this signal in assortment planning, product naming, and campaign visuals. Validate with TikTok and Telegram before treating it as a cross-platform trend.

#### Risk / Validation Note

This signal is based on Amazon search results, which may be affected by sponsored placement, platform ranking, keyword choice, and incomplete automatic labels. Treat it as an e-commerce signal, not a final market truth.
