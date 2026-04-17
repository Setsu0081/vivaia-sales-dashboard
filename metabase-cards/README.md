# Metabase Cards SQL 集

> Dashboard で使う全 card の SQL 本体。card 消失時の再現、SQL 修正時のリファレンスに使う。
> Collection: ID=24 (VIVAIA Dashboard)
> Database: id=2 (postgres-db)
> 再生成: PROJECT.md §12 参照

## card 90 — MD_商品信息汇总

- collection_id: 12

```sql
SELECT
  p.image AS "画像", -- 1
  LEFT(pv.sku, LENGTH(pv.sku) - 3) AS "SPU", -- 2
  pv.sku AS "SKU", -- 3
  pv.barcode AS "UPC", -- 4
  p.product_type AS "カテゴリ", -- 5
  substring(p.title from '\[(.*?)\]') AS "商品名", -- 6
  CASE -- 7
    WHEN position('_' IN pv.option1) > 0 THEN
      substring(pv.option1 from position('_' IN pv.option1) + 1)
    ELSE
      pv.option1
  END AS "カラー",
  CASE -- 8
    WHEN position('/' IN pv.option2) > 0 THEN
      replace(substring(pv.option2 from position('/' IN pv.option2) + 1), '-', '')
    ELSE
      replace(pv.option2, '-', '')
  END AS "サイズ",
  CASE -- 9
    WHEN position('/' IN pv.option2) > 0 THEN
      left(pv.option2, position('/' IN pv.option2) - 1)
    ELSE
      pv.option2
  END AS "日本サイズ",
  pv.price AS "価格", -- 10
  p.heel_hight_for_filter AS "ヒール高", -- ✅ 正确字段名
  p.toes_type AS "つま先形", -- 12
  p.shaft_height AS "筒丈", -- 13
  p.upper_material AS "アッパー素材", -- 14
  p.insole_material AS "インソール素材", -- 15
  p.functional AS "インソール機能", -- 16
  p.outsole_material AS "アウトソール素材", -- 17
  p.technology AS "テクノロジー" -- 18
FROM
  products p
LEFT JOIN product_variants pv
  ON p.id = pv.product_id;
```

## card 120 — MD_门店库存

- collection_id: 12

```sql
SELECT 
    pv.sku AS "SKU",
    -- 4 个日本门店 (来自 POS 数据)
    SUM(CASE WHEN pvi.store_id = '1'  THEN CAST(NULLIF(pvi.quantity, '') AS INTEGER) ELSE 0 END) AS "hara",
    SUM(CASE WHEN pvi.store_id = '2'  THEN CAST(NULLIF(pvi.quantity, '') AS INTEGER) ELSE 0 END) AS "新宿",
    SUM(CASE WHEN pvi.store_id = '3'  THEN CAST(NULLIF(pvi.quantity, '') AS INTEGER) ELSE 0 END) AS "大阪",
    SUM(CASE WHEN pvi.store_id = '13' THEN CAST(NULLIF(pvi.quantity, '') AS INTEGER) ELSE 0 END) AS "二子玉川",
    
    -- 你要的东莞仓 (从 pv 表取最大值，避免重复)
    MAX(pv.inventory_quantity) AS "东莞仓 (总可售)",
    
    -- 汇总：全日本门店库存合计
    SUM(CASE WHEN pvi.store_id IN ('1', '2', '3', '13') THEN CAST(NULLIF(pvi.quantity, '') AS INTEGER) ELSE 0 END) AS "日本门店总计"
FROM product_variants pv
LEFT JOIN product_variants_inventory pvi ON pv.sku = pvi.sku
GROUP BY pv.sku, pv.inventory_quantity
HAVING pv.inventory_quantity > 0 OR SUM(CASE WHEN pvi.store_id IN ('1', '2', '3', '13') THEN CAST(NULLIF(pvi.quantity, '') AS INTEGER) ELSE 0 END) > 0
ORDER BY "东莞仓 (总可售)" DESC;
```

## card 133 — 店铺销售数据

- collection_id: 12

```sql
SELECT                                                                                                               
    s.store_name AS "店舗",                                                                                            
                
    -- 今日                                                                                                                      
    COALESCE(SUM(CASE WHEN ts.transaction_date_time AT TIME ZONE 'Asia/Tokyo' >= (CURRENT_DATE AT TIME ZONE 'Asia/Tokyo')        
                      AND ts.transaction_date_time AT TIME ZONE 'Asia/Tokyo' < (CURRENT_DATE AT TIME ZONE 'Asia/Tokyo' + INTERVAL
   '1 day')                                                                                                                      
                      THEN ts.total::numeric END), 0) AS "今日_売上",                                                            
    COUNT(CASE WHEN ts.transaction_date_time AT TIME ZONE 'Asia/Tokyo' >= (CURRENT_DATE AT TIME ZONE 'Asia/Tokyo')               
                    AND ts.transaction_date_time AT TIME ZONE 'Asia/Tokyo' < (CURRENT_DATE AT TIME ZONE 'Asia/Tokyo' + INTERVAL  
  '1 day')                                                                                                                       
                    THEN 1 END) AS "今日_取引数",                                                                                
    ROUND(COALESCE(SUM(CASE WHEN ts.transaction_date_time AT TIME ZONE 'Asia/Tokyo' >= (CURRENT_DATE AT TIME ZONE 'Asia/Tokyo')  
                      AND ts.transaction_date_time AT TIME ZONE 'Asia/Tokyo' < (CURRENT_DATE AT TIME ZONE 'Asia/Tokyo' + INTERVAL
   '1 day')                                                                                                                      
                      THEN ts.total::numeric END), 0)                                                                            
      / NULLIF(COUNT(CASE WHEN ts.transaction_date_time AT TIME ZONE 'Asia/Tokyo' >= (CURRENT_DATE AT TIME ZONE 'Asia/Tokyo')    
                               AND ts.transaction_date_time AT TIME ZONE 'Asia/Tokyo' < (CURRENT_DATE AT TIME ZONE 'Asia/Tokyo' +
   INTERVAL '1 day')                                                                                                             
                               THEN 1 END), 0), 0) AS "今日_客単価",                                                             
                                                                                                                                 
    -- 昨日       
    COALESCE(SUM(CASE WHEN ts.transaction_date_time AT TIME ZONE 'Asia/Tokyo' >= (CURRENT_DATE AT TIME ZONE 'Asia/Tokyo' -
  INTERVAL '1 day')                                                                                                              
                      AND ts.transaction_date_time AT TIME ZONE 'Asia/Tokyo' < (CURRENT_DATE AT TIME ZONE 'Asia/Tokyo')
                      THEN ts.total::numeric END), 0) AS "昨日_売上",                                                            
    COUNT(CASE WHEN ts.transaction_date_time AT TIME ZONE 'Asia/Tokyo' >= (CURRENT_DATE AT TIME ZONE 'Asia/Tokyo' - INTERVAL '1 
  day')                                                                                                                          
                    AND ts.transaction_date_time AT TIME ZONE 'Asia/Tokyo' < (CURRENT_DATE AT TIME ZONE 'Asia/Tokyo')
                    THEN 1 END) AS "昨日_取引数",                                                                                
    ROUND(COALESCE(SUM(CASE WHEN ts.transaction_date_time AT TIME ZONE 'Asia/Tokyo' >= (CURRENT_DATE AT TIME ZONE 'Asia/Tokyo' - 
  INTERVAL '1 day')                                                                                                              
                      AND ts.transaction_date_time AT TIME ZONE 'Asia/Tokyo' < (CURRENT_DATE AT TIME ZONE 'Asia/Tokyo')          
                      THEN ts.total::numeric END), 0)                                                                            
      / NULLIF(COUNT(CASE WHEN ts.transaction_date_time AT TIME ZONE 'Asia/Tokyo' >= (CURRENT_DATE AT TIME ZONE 'Asia/Tokyo' -   
  INTERVAL '1 day')
                               AND ts.transaction_date_time AT TIME ZONE 'Asia/Tokyo' < (CURRENT_DATE AT TIME ZONE 'Asia/Tokyo') 
                               THEN 1 END), 0), 0) AS "昨日_客単価",                                                             
  
    -- 上一週間 (過去7日)                                                                                                        
    COALESCE(SUM(CASE WHEN ts.transaction_date_time AT TIME ZONE 'Asia/Tokyo' >= (CURRENT_DATE AT TIME ZONE 'Asia/Tokyo' -
  INTERVAL '7 day')                                                                                                              
                      AND ts.transaction_date_time AT TIME ZONE 'Asia/Tokyo' < (CURRENT_DATE AT TIME ZONE 'Asia/Tokyo')
                      THEN ts.total::numeric END), 0) AS "7日間_売上",                                                           
    COUNT(CASE WHEN ts.transaction_date_time AT TIME ZONE 'Asia/Tokyo' >= (CURRENT_DATE AT TIME ZONE 'Asia/Tokyo' - INTERVAL '7  
  day')                                                                                                                          
                    AND ts.transaction_date_time AT TIME ZONE 'Asia/Tokyo' < (CURRENT_DATE AT TIME ZONE 'Asia/Tokyo')            
                    THEN 1 END) AS "7日間_取引数",                                                                               
    ROUND(COALESCE(SUM(CASE WHEN ts.transaction_date_time AT TIME ZONE 'Asia/Tokyo' >= (CURRENT_DATE AT TIME ZONE 'Asia/Tokyo' - 
  INTERVAL '7 day')                                                                                                              
                      AND ts.transaction_date_time AT TIME ZONE 'Asia/Tokyo' < (CURRENT_DATE AT TIME ZONE 'Asia/Tokyo')          
                      THEN ts.total::numeric END), 0)                                                                            
      / NULLIF(COUNT(CASE WHEN ts.transaction_date_time AT TIME ZONE 'Asia/Tokyo' >= (CURRENT_DATE AT TIME ZONE 'Asia/Tokyo' -
  INTERVAL '7 day')                                                                                                              
                               AND ts.transaction_date_time AT TIME ZONE 'Asia/Tokyo' < (CURRENT_DATE AT TIME ZONE 'Asia/Tokyo')
                               THEN 1 END), 0), 0) AS "7日間_客単価",                                                            
                  
    -- 30日間                                                                                                                    
    COALESCE(SUM(CASE WHEN ts.transaction_date_time AT TIME ZONE 'Asia/Tokyo' >= (CURRENT_DATE AT TIME ZONE 'Asia/Tokyo' -
  INTERVAL '30 day')                                                                                                             
                      AND ts.transaction_date_time AT TIME ZONE 'Asia/Tokyo' < (CURRENT_DATE AT TIME ZONE 'Asia/Tokyo')
                      THEN ts.total::numeric END), 0) AS "30日間_売上",                                                          
    COUNT(CASE WHEN ts.transaction_date_time AT TIME ZONE 'Asia/Tokyo' >= (CURRENT_DATE AT TIME ZONE 'Asia/Tokyo' - INTERVAL '30 
  day')                                                                                                                          
                    AND ts.transaction_date_time AT TIME ZONE 'Asia/Tokyo' < (CURRENT_DATE AT TIME ZONE 'Asia/Tokyo')
                    THEN 1 END) AS "30日間_取引数",                                                                              
    ROUND(COALESCE(SUM(CASE WHEN ts.transaction_date_time AT TIME ZONE 'Asia/Tokyo' >= (CURRENT_DATE AT TIME ZONE 'Asia/Tokyo' -
  INTERVAL '30 day')                                                                                                             
                      AND ts.transaction_date_time AT TIME ZONE 'Asia/Tokyo' < (CURRENT_DATE AT TIME ZONE 'Asia/Tokyo')
                      THEN ts.total::numeric END), 0)                                                                            
      / NULLIF(COUNT(CASE WHEN ts.transaction_date_time AT TIME ZONE 'Asia/Tokyo' >= (CURRENT_DATE AT TIME ZONE 'Asia/Tokyo' -   
  INTERVAL '30 day')                                                                                                             
                               AND ts.transaction_date_time AT TIME ZONE 'Asia/Tokyo' < (CURRENT_DATE AT TIME ZONE 'Asia/Tokyo') 
                               THEN 1 END), 0), 0) AS "30日間_客単価"                                                            
                                                                                                                                 
  FROM transactions ts
  LEFT JOIN stores s ON ts.store_id = s.store_id                                                                                 
  WHERE s.store_name IN ('ハラカド店', '新宿マルイ本館店', 'グラングリーン大阪店', '二子玉川店')
    AND ts.transaction_date_time AT TIME ZONE 'Asia/Tokyo' >= (CURRENT_DATE AT TIME ZONE 'Asia/Tokyo' - INTERVAL '30 day')       
  GROUP BY s.store_name                                                                                                          
  ORDER BY s.store_name;
```

## card 134 — SYS_offline_ranking_daily

- collection_id: 24

```sql
SELECT t.store_id, DATE(t.transaction_date_time) as d, SUBSTRING(pv.sku FROM 1 FOR LENGTH(pv.sku)-3) as spu, SUM(ti.quantity::int) as qty FROM transactions t JOIN transaction_items ti ON t.transaction_head_id = ti.transaction_head_id JOIN product_variants pv ON pv.barcode = ti.product_code WHERE t.transaction_date_time >= NOW() - INTERVAL '400 days' GROUP BY 1, 2, 3 ORDER BY d, t.store_id, spu
```

## card 135 — SYS_ec_ranking_daily

- collection_id: 24

```sql
SELECT 'ec' as store_id, DATE(o.created_at) as d, SUBSTRING(oi.product_variant_sku FROM 1 FOR LENGTH(oi.product_variant_sku)-3) as spu, SUM(oi.product_quantity) as qty FROM online_orders o JOIN online_order_items oi ON o.id = oi.order_id WHERE o.financial_status = 'PAID' AND o.created_at >= NOW() - INTERVAL '400 days' GROUP BY 1, 2, 3 ORDER BY d, spu
```

## card 136 — SYS_ec_daily_sales

- collection_id: 24

```sql
SELECT DATE(created_at) as d, SUM(total_price::numeric) as sales, COUNT(*) as orders, COUNT(DISTINCT customer_id) as customers FROM online_orders WHERE financial_status = 'PAID' AND created_at >= '2025-09-01' GROUP BY 1 ORDER BY d
```

## card 137 — SYS_ec_inventory

- collection_id: 24

```sql
SELECT sku, inventory_quantity FROM product_variants ORDER BY sku
```

## card 138 — SYS_offline_ranking_full

- collection_id: 24

```sql
SELECT t.store_id, DATE(t.transaction_date_time) as d, SUBSTRING(pv.sku FROM 1 FOR LENGTH(pv.sku)-3) as spu, SUM(ti.quantity::int) as qty FROM transactions t JOIN transaction_items ti ON t.transaction_head_id = ti.transaction_head_id JOIN product_variants pv ON pv.barcode = ti.product_code WHERE t.transaction_date_time >= '2024-04-01' GROUP BY 1, 2, 3 ORDER BY d, t.store_id, spu
```

## card 139 — SYS_ec_ranking_full

- collection_id: 24

```sql
SELECT 'ec' as store_id, DATE(o.created_at) as d, SUBSTRING(oi.product_variant_sku FROM 1 FOR LENGTH(oi.product_variant_sku)-3) as spu, SUM(oi.product_quantity) as qty FROM online_orders o JOIN online_order_items oi ON o.id = oi.order_id WHERE o.financial_status = 'PAID' AND o.created_at >= '2024-04-01' GROUP BY 1, 2, 3 ORDER BY d, spu
```

## card 140 — SYS_offline_daily_sales_full

- collection_id: 24

```sql
SELECT store_id, DATE(transaction_date_time) as d, COUNT(*) as txn, SUM(total::numeric) as sales, COUNT(DISTINCT customer_id) as customers FROM transactions WHERE transaction_date_time >= '2024-04-01' GROUP BY 1,2 ORDER BY d, store_id
```

## card 141 — SYS_ec_daily_sales_full

- collection_id: 24

```sql
SELECT DATE(created_at) as d, SUM(total_price::numeric) as sales, COUNT(*) as orders, COUNT(DISTINCT customer_id) as customers FROM online_orders WHERE financial_status = 'PAID' AND created_at >= '2024-04-01' GROUP BY 1 ORDER BY d
```

