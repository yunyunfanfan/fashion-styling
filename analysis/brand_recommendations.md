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

## Product Recommendations

### casual (derived_style)

Trend score: 0.837. Evidence: 212 products, 12 query categories, average rating 3.78, total rating count 81556.

Sample products:
- striped shirt: U TURN - U TURN Men's Casual Printed Striped Stylish Latest Formal Shirt for Men
  Image: https://m.media-amazon.com/images/I/61SB14qT0EL._AC_UL320_.jpg
- platform shoes: Vendoz - Vendoz Women White Casual Sneakers
  Image: https://m.media-amazon.com/images/I/71SGV-4lI9L._AC_UL320_.jpg
- linen shirt: NexaFlair - NexaFlair Men's Solid Linen Cotton Shirt | Casual | Plain | Full Sleeve | Summer-Regular Fit| Men Stylish Shirt | Everyday...
  Image: https://m.media-amazon.com/images/I/81I4F9xgijL._AC_UL320_.jpg

### solid (derived_pattern)

Trend score: 0.814. Evidence: 55 products, 11 query categories, average rating 3.72, total rating count 36120.

Sample products:
- linen shirt: NexaFlair - NexaFlair Men's Solid Linen Cotton Shirt | Casual | Plain | Full Sleeve | Summer-Regular Fit| Men Stylish Shirt | Everyday...
  Image: https://m.media-amazon.com/images/I/81I4F9xgijL._AC_UL320_.jpg
- oversized hoodie: The Modern Soul - The Modern Soul Half Zipper Solid Hoodie for Men | Sweatshirt for Men
  Image: https://m.media-amazon.com/images/I/31B+tV6-28L._AC_UL320_.jpg
- linen shirt: NexaFlair - NexaFlair Men's Solid Linen Cotton Shirt | Casual | Plain | Full Sleeve | Summer-Regular Fit| Men Stylish Shirt | Everyday...
  Image: https://m.media-amazon.com/images/I/81qh45dSlgL._AC_UL320_.jpg

### cotton (derived_material)

Trend score: 0.811. Evidence: 146 products, 10 query categories, average rating 3.87, total rating count 84957.

Sample products:
- linen shirt: NexaFlair - NexaFlair Men's Solid Linen Cotton Shirt | Casual | Plain | Full Sleeve | Summer-Regular Fit| Men Stylish Shirt | Everyday...
  Image: https://m.media-amazon.com/images/I/81I4F9xgijL._AC_UL320_.jpg
- oversized hoodie: NETCLICK - NETCLICK Los Angeles Printed Hoodies Sweatshirt Polycotton for Running, Gym Warm Travel Hoodies for Men
  Image: https://m.media-amazon.com/images/I/41DB2PzxvtL._AC_UL320_.jpg
- cargo pants: Lymio - Lymio Cargo for Men || Cotton Cargo Pant || Drawstring Waist Pant (Also Available in Plus Sizes) (145-148)
  Image: https://m.media-amazon.com/images/I/61VzbIFEk4L._AC_UL320_.jpg

### red (derived_colour)

Trend score: 0.786. Evidence: 31 products, 8 query categories, average rating 3.8, total rating count 21435.

Sample products:
- floral dress: Generic - Women's Pink Bandhani Print Tiered Maxi Dress, Short Sleeve, Square Neck, Cotton
  Image: https://m.media-amazon.com/images/I/61RR8+DmkLL._AC_UL320_.jpg
- linen shirt: NexaFlair - NexaFlair Man's Casual | Formal | Linen| Cotton | Regular Wear Collared | Fit Shirt for Men
  Image: https://m.media-amazon.com/images/I/61ykgVB3xHL._AC_UL320_.jpg
- floral dress: Modestouze Attires - Modestouze Attires Dress for Women Western Maxi Style, Indo Western Dresses, One Piece Long Gown, A Line Flared Pattern, E...
  Image: https://m.media-amazon.com/images/I/61QQbNKtCGL._AC_UL320_.jpg

### denim (derived_colour)

Trend score: 0.771. Evidence: 71 products, 4 query categories, average rating 3.86, total rating count 70605.

Sample products:
- denim jacket: GRECIILOOKS - GRECIILOOKS Men’S Denim Jacket | Classic Regular Fit Jeans Jacket For Men | Stylish Branded Jackets For Men – Timeless Cas...
  Image: https://m.media-amazon.com/images/I/51g+JumJl9L._AC_UL320_.jpg
- wide leg jeans: KCM FASHION - High-Waisted Wide-Leg Jeans Featuring a Relaxed fit Silhouette and Classic Denim for Versatile Casual wear
  Image: https://m.media-amazon.com/images/I/41aQZIqSbQL._AC_UL320_.jpg
- denim jacket: Urbano Fashion - Urbano Fashion Men's Regular Fit Washed Full Sleeve Denim Jacket
  Image: https://m.media-amazon.com/images/I/71e5Iu8ju8L._AC_UL320_.jpg

### black (derived_colour)

Trend score: 0.695. Evidence: 29 products, 7 query categories, average rating 3.75, total rating count 10042.

Sample products:
- floral dress: MASIYALA - MASIYALA Women's Floral Print Maxi Dress, Black with Pink Flowers, Short Sleeve, A-Line Style
  Image: https://m.media-amazon.com/images/I/61yVG8Qe+FL._AC_UL320_.jpg
- leather jacket: EXOTIX - EXOTIX Black Leather Jacket for Men | Collared Zip-Up Classic Style | Crop Fit Racing Sports Bomber Jacket | Premium Leath...
  Image: https://m.media-amazon.com/images/I/51aa6X0QOmL._AC_UL320_.jpg
- leather jacket: EXOTIX - EXOTIX Men's Black Leather Jacket | Collared Zip-Up, Classic Style | Black Crop Leather Jacket | Racing Sports Regular Bom...
  Image: https://m.media-amazon.com/images/I/61cW3rD6GqL._AC_UL320_.jpg

### vacation (derived_scene)

Trend score: 0.666. Evidence: 90 products, 10 query categories, average rating 3.87, total rating count 60187.

Sample products:
- linen shirt: NexaFlair - NexaFlair Men's Solid Linen Cotton Shirt | Casual | Plain | Full Sleeve | Summer-Regular Fit| Men Stylish Shirt | Everyday...
  Image: https://m.media-amazon.com/images/I/81I4F9xgijL._AC_UL320_.jpg
- oversized hoodie: NETCLICK - NETCLICK Los Angeles Printed Hoodies Sweatshirt Polycotton for Running, Gym Warm Travel Hoodies for Men
  Image: https://m.media-amazon.com/images/I/41DB2PzxvtL._AC_UL320_.jpg
- knit cardigan: Generic - Women’s Cropped Tie-Front Shrug Cardigan | Soft Ribbed Knit Long Sleeve V-Neck Top | Stylish Summer Cardigan, Casual Beach...
  Image: https://m.media-amazon.com/images/I/513c3fVae2L._AC_UL320_.jpg

### floral (derived_pattern)

Trend score: 0.617. Evidence: 57 products, 4 query categories, average rating 3.82, total rating count 26002.

Sample products:
- floral dress: MASIYALA - MASIYALA Women's Floral Print Maxi Dress, Black with Pink Flowers, Short Sleeve, A-Line Style
  Image: https://m.media-amazon.com/images/I/61yVG8Qe+FL._AC_UL320_.jpg
- floral dress: Generic - Women's Pink Bandhani Print Tiered Maxi Dress, Short Sleeve, Square Neck, Cotton
  Image: https://m.media-amazon.com/images/I/61RR8+DmkLL._AC_UL320_.jpg
- floral dress: Modestouze Attires - Modestouze Attires Dress for Women Western Maxi Style, Indo Western Dresses, One Piece Long Gown, A Line Flared Pattern, E...
  Image: https://m.media-amazon.com/images/I/61QQbNKtCGL._AC_UL320_.jpg
