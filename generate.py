#!/usr/bin/env python3
"""
VIVAIA Japan Dashboard Generator
- 商品ランキング: VJP全体 + 4店铺 Top 10 (built 3x/day)
- 在庫確認: 全SKU库存 + 筛选 (built every 15 min)

Usage:
  python3 generate.py --mode full        # rebuild everything
  python3 generate.py --mode inventory   # only refresh inventory data
"""

import argparse
import csv
import io
import json
import os
import urllib.request
import ssl
from collections import defaultdict
from datetime import datetime
from pathlib import Path

API_CSV = "https://bi.vivaia.jp/api/card/{}/query/csv"
API_JSON = "https://bi.vivaia.jp/api/card/{}/query"
API_KEY = os.environ["METABASE_API_KEY"]
DIR = Path(__file__).parent
OUTPUT = DIR / "index.html"
RANKING_CACHE = DIR / "ranking_cache.json"
SALES_ANALYSIS_CACHE = DIR / "sales_analysis_cache.json"

IMAGE_CARD = 90
INVENTORY_CARD = 120
PRODUCT_CARD = 90

STORE_MAP = {"1": "ハラカド店", "2": "新宿店", "3": "大阪店", "13": "二子玉川店", "all": "全体"}


# ── API helpers ──────────────────────────────────────────────

def _fetch(url, method="POST"):
    ctx = ssl.create_default_context()
    req = urllib.request.Request(
        url, method=method,
        headers={"X-Api-Key": API_KEY, "Content-Type": "application/json"},
        data=b"{}",
    )
    with urllib.request.urlopen(req, context=ctx) as resp:
        return resp.read()


def fetch_csv(card_id):
    raw = _fetch(API_CSV.format(card_id)).decode("utf-8")
    reader = csv.reader(io.StringIO(raw))
    headers = next(reader)
    return headers, list(reader)


def fetch_json(card_id):
    return json.loads(_fetch(API_JSON.format(card_id)))


def fetch_ec_inventory():
    """Fetch EC inventory from postgres-db product_variants via paginated SQL."""
    ctx = ssl.create_default_context()
    ec = {}
    offset = 0
    while True:
        body = json.dumps({
            "database": 2,
            "type": "native",
            "native": {"query": f"SELECT sku, inventory_quantity FROM product_variants ORDER BY sku LIMIT 2000 OFFSET {offset}"}
        }).encode()
        req = urllib.request.Request(
            "https://bi.vivaia.jp/api/dataset",
            method="POST",
            headers={"X-Api-Key": API_KEY, "Content-Type": "application/json"},
            data=body,
        )
        with urllib.request.urlopen(req, context=ctx) as resp:
            data = json.loads(resp.read())
        rows = data["data"]["rows"]
        for r in rows:
            ec[r[0]] = r[1] or 0
        if len(rows) < 2000:
            break
        offset += len(rows)
    return ec


def fetch_daily_sales():
    """Fetch daily_sales_reports from postgres-db."""
    ctx = ssl.create_default_context()
    body = json.dumps({
        "database": 2, "type": "native",
        "native": {"query": "SELECT report_date, store_scope, sales_amount, sales_qty, customers_count, avg_transaction_value FROM daily_sales_reports ORDER BY report_date, store_scope"}
    }).encode()
    req = urllib.request.Request(
        "https://bi.vivaia.jp/api/dataset", method="POST",
        headers={"X-Api-Key": API_KEY, "Content-Type": "application/json"}, data=body,
    )
    with urllib.request.urlopen(req, context=ctx) as resp:
        data = json.loads(resp.read())
    # Store scope mapping (daily_sales_reports = offline stores only)
    scope_map = {"1": "ハラカド店", "2": "新宿店", "3": "大阪店", "13": "二子玉川店", "all": "店舗合計"}
    result = []
    for r in data["data"]["rows"]:
        date_str = r[0][:10] if r[0] else ""
        scope = scope_map.get(str(r[1]), str(r[1]))
        result.append({
            "date": date_str,
            "store": scope,
            "sales": round(r[2] or 0),
            "qty": r[3] or 0,
            "customers": r[4] or 0,
            "atv": round(r[5] or 0),
        })

    # Fetch EC daily sales from online_orders
    print("  Fetching EC daily sales...")
    ec_sql = """SELECT DATE(created_at) as d,
        SUM(total_price::numeric) as sales,
        COUNT(*) as orders,
        COUNT(DISTINCT customer_id) as customers
    FROM online_orders
    WHERE financial_status = 'PAID' AND created_at >= '2025-09-01'
    GROUP BY 1 ORDER BY d
    LIMIT 2000 OFFSET {}"""
    ec_rows = _paginated_query(ec_sql)
    print(f"  {len(ec_rows)} EC daily records")

    # Build date -> offline totals for computing VJP全体
    from collections import defaultdict as dd
    offline_by_date = dd(lambda: {"sales": 0, "qty": 0, "customers": 0})
    for item in result:
        if item["store"] == "店舗合計":
            d = offline_by_date[item["date"]]
            d["sales"] = item["sales"]
            d["qty"] = item["qty"]
            d["customers"] = item["customers"]

    for r in ec_rows:
        date_str = r[0][:10] if r[0] else ""
        ec_sales = round(r[1] or 0)
        ec_qty = r[2] or 0
        ec_cust = r[3] or 0
        ec_atv = round(ec_sales / ec_cust) if ec_cust > 0 else 0
        result.append({
            "date": date_str,
            "store": "EC",
            "sales": ec_sales,
            "qty": ec_qty,
            "customers": ec_cust,
            "atv": ec_atv,
        })
        # VJP全体 = offline + EC
        off = offline_by_date.get(date_str, {"sales": 0, "qty": 0, "customers": 0})
        total_sales = off["sales"] + ec_sales
        total_qty = off["qty"] + ec_qty
        total_cust = off["customers"] + ec_cust
        total_atv = round(total_sales / total_cust) if total_cust > 0 else 0
        result.append({
            "date": date_str,
            "store": "全体",
            "sales": total_sales,
            "qty": total_qty,
            "customers": total_cust,
            "atv": total_atv,
        })

    return result


def to_num(v):
    try:
        return float(v)
    except (ValueError, TypeError):
        return 0


# ── Ranking logic ────────────────────────────────────────────

def fetch_image_map():
    raw = fetch_json(IMAGE_CARD)
    m = {}
    for r in raw["data"]["rows"]:
        spu, img = r[1], r[0]
        if spu not in m and img:
            m[spu] = img
    return m


def fetch_spu_info():
    """Fetch SPU -> {name, color, img} from MD_商品信息汇総 CSV."""
    _, rows = fetch_csv(PRODUCT_CARD)
    info = {}
    for r in rows:
        spu = r[1]
        if spu not in info:
            info[spu] = {"name": r[5] or "", "color": r[6] or "", "img": r[0] or ""}
    return info


def _paginated_query(query_template):
    """Run a paginated SQL query against Metabase, returning all rows."""
    ctx = ssl.create_default_context()
    all_rows = []
    offset = 0
    while True:
        body = json.dumps({"database": 2, "type": "native", "native": {"query": query_template.format(offset)}}).encode()
        req = urllib.request.Request("https://bi.vivaia.jp/api/dataset", method="POST",
            headers={"X-Api-Key": API_KEY, "Content-Type": "application/json"}, data=body)
        with urllib.request.urlopen(req, context=ctx) as resp:
            data = json.loads(resp.read())
        rows = data["data"]["rows"]
        all_rows.extend(rows)
        if len(rows) < 2000:
            break
        offset += len(rows)
    return all_rows


def fetch_ranking_data():
    """Fetch daily SPU-level sales per store (offline + EC) from DB."""
    # Offline: transactions table
    print("    Fetching offline transactions...")
    offline_sql = """SELECT t.store_id, DATE(t.transaction_date_time) as d,
        SUBSTRING(pv.sku FROM 1 FOR LENGTH(pv.sku)-3) as spu,
        SUM(ti.quantity::int) as qty
    FROM transactions t
    JOIN transaction_items ti ON t.transaction_head_id = ti.transaction_head_id
    JOIN product_variants pv ON pv.barcode = ti.product_code
    GROUP BY 1, 2, 3
    ORDER BY d, t.store_id, spu
    LIMIT 2000 OFFSET {}"""
    offline_rows = _paginated_query(offline_sql)
    print(f"    {len(offline_rows)} offline rows")

    # EC: online_orders table
    print("    Fetching EC orders...")
    ec_sql = """SELECT 'ec' as store_id, DATE(o.created_at) as d,
        SUBSTRING(oi.product_variant_sku FROM 1 FOR LENGTH(oi.product_variant_sku)-3) as spu,
        SUM(oi.product_quantity) as qty
    FROM online_orders o
    JOIN online_order_items oi ON o.id = oi.order_id
    WHERE o.financial_status = 'PAID' AND o.created_at >= '2024-04-01'
    GROUP BY 1, 2, 3
    ORDER BY d, spu
    LIMIT 2000 OFFSET {}"""
    ec_rows = _paginated_query(ec_sql)
    print(f"    {len(ec_rows)} EC rows")

    # Merge offline + EC, compute "all" (全体 = offline + EC)
    from collections import defaultdict as dd
    spu_daily = dd(int)
    for r in offline_rows:
        spu_daily[(r[0], r[1][:10], r[2])] += r[3]
    for r in ec_rows:
        if r[2]:  # skip rows with NULL spu
            spu_daily[(r[0], r[1][:10], r[2])] += r[3]

    # Compute "all" = sum of all stores + EC
    all_total = dd(int)
    for (store, date, spu), qty in spu_daily.items():
        all_total[("all", date, spu)] += qty
    spu_daily.update(all_total)

    # Compact format with string table
    spus = sorted(set(k[2] for k in spu_daily))
    spu_idx = {s: i for i, s in enumerate(spus)}
    compact = sorted([[s, d, spu_idx[p], q] for (s, d, p), q in spu_daily.items()])
    return {"spus": spus, "data": compact}


# ── Inventory logic ──────────────────────────────────────────

def build_inventory_json():
    """Fetch inventory + product info + EC inventory, return JSON data for client-side rendering."""
    print("  Fetching inventory (card 120)...")
    _, inv_rows = fetch_csv(INVENTORY_CARD)

    print("  Fetching EC inventory (postgres-db)...")
    ec_map = fetch_ec_inventory()
    print(f"  {len(ec_map)} EC SKUs loaded")

    print("  Fetching product info (card 90)...")
    _, prod_rows = fetch_csv(PRODUCT_CARD)

    # Build SKU -> product info map
    sku_info = {}
    for r in prod_rows:
        # 画像, SPU, SKU, UPC, カテゴリ, 商品名, カラー, サイズ
        sku = r[2]
        sku_info[sku] = {
            "img": r[0] or "",
            "upc": r[3] or "",
            "cat": r[4] or "",
            "name": r[5] or "",
            "color": r[6] or "",
            "size": r[7] if len(r) > 7 else "",
        }

    # Merge inventory with product info
    items = []
    for r in inv_rows:
        sku = r[0]
        info = sku_info.get(sku, {})
        items.append({
            "sku": sku,
            "img": info.get("img", ""),
            "upc": info.get("upc", ""),
            "cat": info.get("cat", ""),
            "name": info.get("name", sku),
            "color": info.get("color", ""),
            "size": info.get("size", ""),
            "hara": int(to_num(r[1])),
            "shinjuku": int(to_num(r[2])),
            "osaka": int(to_num(r[3])),
            "futako": int(to_num(r[4])),
            "total": int(to_num(r[6])),
            "ec": ec_map.get(sku, 0),
        })

    print(f"  {len(items)} SKUs loaded")
    return items


# ── Page assembly ────────────────────────────────────────────

def build_page(ranking_json, spu_info_json, inventory_json, sales_analysis_json, now):
    rk_data = json.dumps(ranking_json, ensure_ascii=False, separators=(",", ":"))
    rk_info = json.dumps(spu_info_json, ensure_ascii=False, separators=(",", ":"))
    inv_data = json.dumps(inventory_json, ensure_ascii=False, separators=(",", ":"))
    sa_data = json.dumps(sales_analysis_json, ensure_ascii=False, separators=(",", ":"))

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>VIVAIA Japan Dashboard</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:-apple-system,'Helvetica Neue','Segoe UI',sans-serif; background:#f5f6fa; color:#2d3436; -webkit-text-size-adjust:100%; display:flex; min-height:100vh; }}
.sidebar {{ width:180px; background:#2d3436; color:#fff; padding:16px 0; flex-shrink:0; position:fixed; top:0; left:0; height:100vh; z-index:100; }}
.sidebar .logo {{ padding:0 16px 16px; font-size:14px; font-weight:700; border-bottom:1px solid #636e72; margin-bottom:8px; }}
.sidebar a {{ display:block; padding:10px 16px; color:#b2bec3; text-decoration:none; font-size:13px; font-weight:500; transition:all .2s; }}
.sidebar a:hover {{ color:#fff; background:#636e72; }}
.sidebar a.active {{ color:#fff; background:#0984e3; }}
.main {{ margin-left:180px; flex:1; padding:20px 16px; max-width:calc(100vw - 180px); overflow-x:hidden; }}
.page {{ display:none; }}
.page.active {{ display:block; }}
header {{ margin-bottom:16px; }}
header h1 {{ font-size:18px; font-weight:700; }}
header .time {{ color:#636e72; font-size:11px; margin-top:3px; }}
.store-nav {{ display:flex; gap:0; margin-bottom:16px; border-radius:10px; overflow:hidden; box-shadow:0 1px 3px rgba(0,0,0,.08); }}
.store-btn {{ flex:1; padding:9px 6px; border:none; background:#fff; cursor:pointer; font-size:12px; font-weight:600; color:#636e72; transition:all .2s; border-right:1px solid #f1f2f6; }}
.store-btn:last-child {{ border-right:none; }}
.store-btn.active {{ background:#0984e3; color:#fff; }}
.store-btn:hover:not(.active) {{ background:#dfe6e9; }}
.store-section {{ display:none; }}
.store-section.active {{ display:block; }}
.stats {{ display:grid; grid-template-columns:repeat(4,1fr); gap:8px; margin-bottom:16px; }}
.stat-card {{ background:#fff; border-radius:10px; padding:10px 12px; box-shadow:0 1px 3px rgba(0,0,0,.06); }}
.stat-card .label {{ font-size:10px; color:#636e72; }}
.stat-card .value {{ font-size:20px; font-weight:700; color:#0984e3; }}
.tabs {{ display:flex; gap:5px; margin-bottom:12px; }}
.tab-btn {{ padding:6px 12px; border:none; border-radius:7px; background:#dfe6e9; cursor:pointer; font-size:12px; font-weight:500; transition:all .2s; white-space:nowrap; }}
.tab-btn.active {{ background:#0984e3; color:#fff; }}
.tab-content {{ display:none; }}
.tab-content.active {{ display:block; }}
.rk-summary {{ display:flex; align-items:center; gap:20px; background:#fff; border-radius:10px; padding:14px 18px; margin-bottom:14px; box-shadow:0 1px 3px rgba(0,0,0,.06); }}
.rk-total-num {{ font-size:28px; font-weight:700; color:#0984e3; }}
.rk-total-label {{ font-size:11px; color:#636e72; margin-left:6px; }}
.rk-comp {{ display:flex; align-items:center; gap:6px; }}
.rk-comp-label {{ font-size:10px; color:#636e72; font-weight:600; }}
.pct-up {{ color:#00b894; font-weight:600; font-size:13px; }}
.pct-down {{ color:#e74c3c; font-weight:600; font-size:13px; }}
.pct-na {{ color:#b2bec3; font-size:12px; }}
.table-wrap {{ overflow-x:auto; border-radius:10px; box-shadow:0 1px 3px rgba(0,0,0,.06); }}
table {{ width:100%; background:#fff; border-collapse:collapse; }}
thead {{ background:#f8f9fa; }}
th {{ padding:8px; text-align:left; font-size:10px; color:#636e72; font-weight:600; text-transform:uppercase; white-space:nowrap; }}
td {{ padding:8px; border-top:1px solid #f1f2f6; font-size:12px; }}
tr:hover {{ background:#f8f9fa; }}
.rank {{ font-size:15px; text-align:center; }}
.product-cell {{ display:flex; align-items:center; gap:8px; }}
.product-img {{ width:40px; height:40px; border-radius:6px; object-fit:cover; flex-shrink:0; background:#f1f2f6; }}
.no-img {{ width:40px; height:40px; border-radius:6px; background:#f1f2f6; flex-shrink:0; }}
.product-info {{ min-width:0; }}
.product-name {{ font-weight:600; font-size:12px; }}
.product-color {{ font-size:10px; color:#636e72; }}
.num {{ text-align:right; font-variant-numeric:tabular-nums; }}
.highlight {{ font-weight:700; color:#0984e3; font-size:14px; }}
th.num {{ text-align:right; }}
/* Inventory */
.search-bar {{ margin-bottom:10px; }}
.search-bar input {{ width:100%; padding:10px 12px; border:1px solid #dfe6e9; border-radius:8px; font-size:14px; background:#fff; }}
.search-bar input:focus {{ outline:none; border-color:#0984e3; box-shadow:0 0 0 2px rgba(9,132,227,.15); }}
.filters {{ display:flex; gap:8px; margin-bottom:14px; flex-wrap:wrap; }}
.filter-group {{ flex:1; min-width:130px; }}
.filter-group label {{ display:block; font-size:10px; color:#636e72; margin-bottom:3px; font-weight:600; }}
.filter-group select, .filter-group input {{ width:100%; padding:7px 8px; border:1px solid #dfe6e9; border-radius:7px; font-size:12px; background:#fff; }}
.inv-count {{ font-size:11px; color:#636e72; margin-bottom:10px; }}
.inv-table td.stock {{ text-align:center; font-variant-numeric:tabular-nums; white-space:nowrap; }}
.inv-table td.stock.has-stock {{ font-weight:600; color:#2d3436; }}
.inv-table th.stock {{ text-align:center; font-size:10px; padding:8px 4px; white-space:nowrap; }}
.inv-table td.stock:nth-last-child(2) {{ background:#f8f9fa; font-weight:700; }}
.inv-table th:nth-last-child(2) {{ background:#edf0f2; }}
.inv-table td.stock.zero {{ color:#ccc; }}
.inv-img {{ width:32px; height:32px; border-radius:4px; object-fit:cover; background:#f1f2f6; flex-shrink:0; }}
.inv-table td.color-col {{ font-size:11px; white-space:nowrap; }}
.inv-table td.size-col {{ font-size:11px; text-align:center; white-space:nowrap; }}
.inv-table td.name-col {{ font-size:12px; font-weight:600; white-space:nowrap; }}
.inv-table td.img-col {{ width:32px; padding:6px; }}
/* Sales Analysis */
.sa-controls {{ margin-bottom:16px; }}
.sa-date-row {{ display:flex; gap:12px; align-items:center; flex-wrap:wrap; }}
.sa-date-group {{ display:flex; align-items:center; gap:6px; background:#fff; padding:8px 12px; border-radius:8px; box-shadow:0 1px 3px rgba(0,0,0,.06); font-size:12px; }}
.sa-date-group label {{ font-size:10px; font-weight:600; color:#636e72; margin-right:4px; }}
.sa-date-group input[type="date"] {{ border:1px solid #dfe6e9; border-radius:5px; padding:5px 8px; font-size:12px; }}
.sa-compare-toggle {{ display:flex; align-items:center; gap:4px; font-size:12px; cursor:pointer; white-space:nowrap; }}
.sa-cards {{ display:grid; grid-template-columns:repeat(4,1fr); gap:10px; margin-bottom:16px; }}
.sa-card {{ background:#fff; border-radius:10px; padding:14px; box-shadow:0 1px 3px rgba(0,0,0,.06); }}
.sa-card .sa-label {{ font-size:10px; color:#636e72; margin-bottom:4px; }}
.sa-card .sa-value {{ font-size:22px; font-weight:700; color:#2d3436; }}
.sa-card .sa-sub {{ font-size:11px; margin-top:4px; }}
.sa-card .sa-up {{ color:#00b894; }}
.sa-card .sa-down {{ color:#e74c3c; }}
.sa-card .sa-compare-val {{ font-size:13px; color:#636e72; }}
.sa-quick {{ display:flex; gap:5px; margin-bottom:10px; flex-wrap:wrap; }}
.sa-quick-btn {{ padding:5px 12px; border:1px solid #dfe6e9; border-radius:6px; background:#fff; font-size:11px; cursor:pointer; transition:all .2s; }}
.sa-quick-btn.active {{ background:#0984e3; color:#fff; border-color:#0984e3; }}
.sa-quick-btn:hover {{ border-color:#0984e3; }}
.sa-to2-auto {{ font-size:11px; color:#636e72; }}
.sa-chart-wrap {{ background:#fff; border-radius:10px; padding:16px; box-shadow:0 1px 3px rgba(0,0,0,.06); }}
/* Mobile: merged product cell */
.mobile-product {{ display:none; }}
.desktop-only {{ }}
.filter-bar {{ display:flex; gap:8px; margin-bottom:14px; flex-wrap:wrap; align-items:flex-end; }}
.clear-btn {{ padding:7px 14px; border:1px solid #dfe6e9; border-radius:7px; background:#fff; font-size:12px; cursor:pointer; color:#636e72; white-space:nowrap; transition:all .2s; }}
.clear-btn:hover {{ background:#e74c3c; color:#fff; border-color:#e74c3c; }}
/* Mobile */
@media (max-width:768px) {{
  .sidebar {{ position:fixed; bottom:0; top:auto; left:0; width:100%; height:auto; display:flex; padding:0; z-index:100; }}
  .sidebar .logo {{ display:none; }}
  .sidebar a {{ flex:1; text-align:center; padding:10px 4px; font-size:11px; border-top:1px solid #636e72; }}
  .main {{ margin-left:0; margin-bottom:50px; padding:14px 10px; max-width:100vw; }}
  .hide-mobile {{ display:none; }}
  .stats {{ grid-template-columns:repeat(2,1fr); }}
  .store-btn {{ font-size:11px; padding:8px 4px; }}
  .filters {{ flex-direction:column; }}
  .filter-group {{ min-width:100%; }}
  /* Inventory mobile: merge product info into one cell */
  .inv-table .desktop-only {{ display:none; }}
  .inv-table .mobile-product {{ display:table-cell; }}
  .inv-table {{ table-layout:auto; }}
  .inv-table th.stock {{ width:auto; padding:6px 3px; font-size:9px; }}
  .inv-table td.stock {{ padding:6px 3px; font-size:11px; }}
  .m-product {{ display:flex; align-items:center; gap:6px; }}
  .m-product .inv-img {{ width:28px; height:28px; }}
  .m-info {{ min-width:0; }}
  .m-info .m-name {{ font-weight:600; font-size:11px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:120px; }}
  .m-info .m-detail {{ font-size:9px; color:#636e72; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:120px; }}
  .sa-cards {{ grid-template-columns:repeat(2,1fr); }}
  .sa-date-row {{ flex-direction:column; align-items:stretch; }}
  .sa-card .sa-value {{ font-size:18px; }}
}}
</style>
</head>
<body>
<div id="login-overlay" style="display:flex;position:fixed;inset:0;z-index:9999;background:#2d3436;align-items:center;justify-content:center;">
  <div style="background:#fff;border-radius:12px;padding:32px 28px;width:300px;text-align:center;box-shadow:0 4px 20px rgba(0,0,0,.3);">
    <div style="font-size:18px;font-weight:700;margin-bottom:4px;">VIVAIA Japan</div>
    <div style="font-size:12px;color:#636e72;margin-bottom:20px;">Dashboard Login</div>
    <input id="login-pw" type="password" placeholder="パスワードを入力" style="width:100%;padding:10px 12px;border:1px solid #dfe6e9;border-radius:8px;font-size:14px;margin-bottom:12px;">
    <div id="login-err" style="color:#e74c3c;font-size:11px;margin-bottom:8px;display:none;">パスワードが違います</div>
    <button id="login-btn" style="width:100%;padding:10px;border:none;border-radius:8px;background:#0984e3;color:#fff;font-size:14px;font-weight:600;cursor:pointer;">ログイン</button>
  </div>
</div>
<div class="sidebar" style="display:none;">
  <div class="logo">VIVAIA Japan</div>
  <a href="#" class="active" data-page="analysis">売上分析</a>
  <a href="#" data-page="ranking">商品ランキング</a>
  <a href="#" data-page="inventory">在庫確認</a>
</div>
<div class="main" style="display:none;">
  <!-- Ranking page -->
  <div id="page-ranking" class="page">
    <header>
      <h1>商品ランキング</h1>
      <div class="time">更新: {now}</div>
    </header>
    <div class="store-nav rk-store-nav">
      <button class="store-btn active" data-rk-store="all">VJP 全体</button>
      <button class="store-btn" data-rk-store="ec">EC</button>
      <button class="store-btn" data-rk-store="1">ハラカド店</button>
      <button class="store-btn" data-rk-store="2">新宿店</button>
      <button class="store-btn" data-rk-store="3">大阪店</button>
      <button class="store-btn" data-rk-store="13">二子玉川店</button>
    </div>
    <div class="sa-quick rk-quick">
      <button class="sa-quick-btn" data-rk-range="today">今日</button>
      <button class="sa-quick-btn" data-rk-range="yesterday">昨日</button>
      <button class="sa-quick-btn active" data-rk-range="thisweek">今週</button>
      <button class="sa-quick-btn" data-rk-range="lastweek">先週</button>
      <button class="sa-quick-btn" data-rk-range="thismonth">今月</button>
      <button class="sa-quick-btn" data-rk-range="lastmonth">先月</button>
      <button class="sa-quick-btn" data-rk-range="thisyear">今年</button>
      <button class="sa-quick-btn" data-rk-range="lastyear">去年</button>
    </div>
    <div class="sa-date-row" style="margin-bottom:14px">
      <div class="sa-date-group">
        <label>期間</label>
        <input type="date" id="rk-from"> ～ <input type="date" id="rk-to">
      </div>
    </div>
    <div class="rk-summary" id="rk-summary"></div>
    <div class="table-wrap">
      <table>
        <thead><tr>
          <th width="36">#</th><th>商品</th><th class="num">該当期間</th>
          <th class="num">環比</th><th class="num">前年比</th>
        </tr></thead>
        <tbody id="rk-body"></tbody>
      </table>
    </div>
  </div>
  <!-- Inventory page -->
  <div id="page-inventory" class="page">
    <header>
      <h1>在庫確認</h1>
      <div class="time">更新: {now}　<span id="inv-refresh-note">（15分ごと自動更新）</span></div>
    </header>
    <div class="search-bar">
      <input id="f-search" type="text" placeholder="商品名・カラー・UPCで検索...">
    </div>
    <div class="filter-bar">
      <div class="filter-group"><label>UPC</label><input id="f-upc" type="text" list="upc-list" placeholder="UPCを入力..."><datalist id="upc-list"></datalist></div>
      <div class="filter-group"><label>カテゴリ</label><select id="f-cat"><option value="">すべて</option></select></div>
      <div class="filter-group"><label>商品名</label><select id="f-name"><option value="">すべて</option></select></div>
      <div class="filter-group"><label>カラー</label><select id="f-color"><option value="">すべて</option></select></div>
      <div class="filter-group"><label>サイズ</label><select id="f-size"><option value="">すべて</option></select></div>
      <button class="clear-btn" id="clear-filters">クリア</button>
    </div>
    <div class="inv-count" id="inv-count"></div>
    <div class="table-wrap">
      <table class="inv-table">
        <thead><tr>
          <th class="desktop-only">画像</th>
          <th class="desktop-only">商品名</th>
          <th class="desktop-only">カラー</th>
          <th class="desktop-only" style="text-align:center">サイズ</th>
          <th class="mobile-product">商品</th>
          <th class="stock">ハラカド</th>
          <th class="stock">新宿</th>
          <th class="stock">大阪</th>
          <th class="stock">二子玉川</th>
          <th class="stock">合計</th>
          <th class="stock">EC在庫</th>
        </tr></thead>
        <tbody id="inv-body"></tbody>
      </table>
    </div>
  </div>
  <!-- Sales Analysis page -->
  <div id="page-analysis" class="page active">
    <header>
      <h1>店舗売上分析</h1>
      <div class="time">更新: {now}</div>
    </header>
    <div class="store-nav sa-store-nav">
      <button class="store-btn active" data-sa-store="全体">VJP 全体</button>
      <button class="store-btn" data-sa-store="EC">EC</button>
      <button class="store-btn" data-sa-store="店舗合計">店舗合計</button>
      <button class="store-btn" data-sa-store="ハラカド店">ハラカド</button>
      <button class="store-btn" data-sa-store="新宿店">新宿</button>
      <button class="store-btn" data-sa-store="大阪店">大阪</button>
      <button class="store-btn" data-sa-store="二子玉川店">二子玉川</button>
    </div>
    <div class="sa-controls">
      <div class="sa-quick">
        <button class="sa-quick-btn" data-range="today">今日</button>
        <button class="sa-quick-btn" data-range="yesterday">昨日</button>
        <button class="sa-quick-btn active" data-range="thisweek">今週</button>
        <button class="sa-quick-btn" data-range="lastweek">先週</button>
        <button class="sa-quick-btn" data-range="thismonth">今月</button>
        <button class="sa-quick-btn" data-range="lastmonth">先月</button>
        <button class="sa-quick-btn" data-range="thisyear">今年</button>
        <button class="sa-quick-btn" data-range="lastyear">去年</button>
      </div>
      <div class="sa-date-row">
        <div class="sa-date-group">
          <label>期間</label>
          <input type="date" id="sa-from"> ～ <input type="date" id="sa-to">
        </div>
        <label class="sa-compare-toggle"><input type="checkbox" id="sa-compare-check"> 比較</label>
        <div class="sa-date-group" id="sa-compare-group" style="display:none">
          <label>比較開始日</label>
          <input type="date" id="sa-from2"> <span id="sa-to2-label" class="sa-to2-auto"></span>
        </div>
      </div>
    </div>
    <div class="sa-cards" id="sa-cards"></div>
    <div class="sa-chart-wrap">
      <canvas id="sa-chart" height="280"></canvas>
    </div>
  </div>
</div>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>
<script>
// ── Login ──
const PW_HASH = 'a49aff1951a384d5fa0f4860ab58c383052caf6e3ce7b6caa998e38ec3afc5db';
async function sha256(msg) {{
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(msg));
  return [...new Uint8Array(buf)].map(b => b.toString(16).padStart(2,'0')).join('');
}}
function unlockApp() {{
  document.getElementById('login-overlay').style.display = 'none';
  document.querySelector('.sidebar').style.display = '';
  document.querySelector('.main').style.display = '';
}}
if (localStorage.getItem('vj_auth') === PW_HASH) {{
  unlockApp();
}}
document.getElementById('login-btn').addEventListener('click', async () => {{
  const h = await sha256(document.getElementById('login-pw').value);
  if (h === PW_HASH) {{
    localStorage.setItem('vj_auth', PW_HASH);
    unlockApp();
  }} else {{
    document.getElementById('login-err').style.display = 'block';
  }}
}});
document.getElementById('login-pw').addEventListener('keydown', e => {{
  if (e.key === 'Enter') document.getElementById('login-btn').click();
}});

// ── Page navigation ──
document.querySelectorAll('.sidebar a').forEach(a => {{
  a.addEventListener('click', e => {{
    e.preventDefault();
    document.querySelectorAll('.sidebar a').forEach(x => x.classList.remove('active'));
    document.querySelectorAll('.page').forEach(x => x.classList.remove('active'));
    a.classList.add('active');
    document.getElementById('page-' + a.dataset.page).classList.add('active');
  }});
}});
// ── Ranking page ──
const RK_RAW = {rk_data};
const RK_INFO = {rk_info};
let rkStore = 'all';

function rkAddDays(ds, n) {{ const d = new Date(ds); d.setDate(d.getDate()+n); return d.toISOString().slice(0,10); }}
function rkDiffDays(a, b) {{ return Math.round((new Date(b)-new Date(a))/86400000); }}
function rkQuickRange(key) {{
  const t = new Date(); const fmt = d => d.toISOString().slice(0,10);
  const mon = d => {{ const r=new Date(d); r.setDate(r.getDate()-(r.getDay()||7)+1); return r; }};
  switch(key) {{
    case 'today': return [fmt(t),fmt(t)];
    case 'yesterday': {{ const y=new Date(t); y.setDate(y.getDate()-1); return [fmt(y),fmt(y)]; }}
    case 'thisweek': return [fmt(mon(t)),fmt(t)];
    case 'lastweek': {{ const m=mon(t); m.setDate(m.getDate()-7); const e=new Date(m); e.setDate(e.getDate()+6); return [fmt(m),fmt(e)]; }}
    case 'thismonth': return [fmt(t).slice(0,8)+'01',fmt(t)];
    case 'lastmonth': {{ const f=new Date(t.getFullYear(),t.getMonth()-1,1); const l=new Date(t.getFullYear(),t.getMonth(),0); return [fmt(f),fmt(l)]; }}
    case 'thisyear': return [t.getFullYear()+'-01-01',fmt(t)];
    case 'lastyear': return [(t.getFullYear()-1)+'-01-01',(t.getFullYear()-1)+'-12-31'];
  }}
}}

function rkAggregate(store, from, to) {{
  // Aggregate RK_RAW.data by SPU for given store+date range
  const map = {{}};
  for (const [s, d, si, q] of RK_RAW.data) {{
    if (s === store && d >= from && d <= to) {{
      map[si] = (map[si] || 0) + q;
    }}
  }}
  return map;
}}

function rkPctHtml(cur, prev) {{
  if (!prev || prev === 0) return '<span class="pct-na">-</span>';
  const p = ((cur - prev) / prev * 100).toFixed(1);
  return p >= 0
    ? '<span class="pct-up">\u2191' + p + '%</span>'
    : '<span class="pct-down">\u2193' + Math.abs(p).toFixed(1) + '%</span>';
}}

function renderRanking() {{
  const from1 = document.getElementById('rk-from').value;
  const to1 = document.getElementById('rk-to').value;
  if (!from1 || !to1) return;
  const days = rkDiffDays(from1, to1);

  // Current period
  const cur = rkAggregate(rkStore, from1, to1);
  // 環比: previous same-length period
  const prevTo = rkAddDays(from1, -1);
  const prevFrom = rkAddDays(prevTo, -days);
  const prev = rkAggregate(rkStore, prevFrom, prevTo);
  // 前年比: last year same dates
  const yoyFrom = rkAddDays(from1, -365);
  const yoyTo = rkAddDays(to1, -365);
  const yoy = rkAggregate(rkStore, yoyFrom, yoyTo);

  // Top 10 by current period
  const ranked = Object.entries(cur).sort((a,b) => b[1]-a[1]).slice(0, 10);
  const totalCur = Object.values(cur).reduce((s,v) => s+v, 0);
  const totalPrev = Object.values(prev).reduce((s,v) => s+v, 0);
  const totalYoy = Object.values(yoy).reduce((s,v) => s+v, 0);

  // Summary
  document.getElementById('rk-summary').innerHTML =
    '<div class="rk-total"><span class="rk-total-num">' + totalCur.toLocaleString() + '</span><span class="rk-total-label">販売数</span></div>' +
    '<div class="rk-comp"><span class="rk-comp-label">環比</span>' + rkPctHtml(totalCur, totalPrev) + '</div>' +
    '<div class="rk-comp"><span class="rk-comp-label">前年比</span>' + rkPctHtml(totalCur, totalYoy) + '</div>';

  // Table
  const medals = {{0:'\U0001f947',1:'\U0001f948',2:'\U0001f949'}};
  document.getElementById('rk-body').innerHTML = ranked.map(([si, qty], i) => {{
    const spu = RK_RAW.spus[si];
    const info = RK_INFO[spu] || {{}};
    const img = info.img ? '<img class="product-img" src="'+info.img+'" loading="lazy">' : '<div class="product-img no-img"></div>';
    const medal = medals[i] || (i+1);
    const prevQty = prev[si] || 0;
    const yoyQty = yoy[si] || 0;
    return '<tr>' +
      '<td class="rank">'+medal+'</td>' +
      '<td class="product-cell">'+img+'<div class="product-info"><div class="product-name">'+(info.name||spu)+'</div><div class="product-color">'+(info.color||'')+'</div></div></td>' +
      '<td class="num highlight">'+qty+'</td>' +
      '<td class="num">'+rkPctHtml(qty, prevQty)+'</td>' +
      '<td class="num">'+rkPctHtml(qty, yoyQty)+'</td>' +
      '</tr>';
  }}).join('');
}}

(function initRanking() {{
  const [f,t] = rkQuickRange('thisweek');
  document.getElementById('rk-from').value = f;
  document.getElementById('rk-to').value = t;

  document.querySelectorAll('.rk-store-nav .store-btn').forEach(btn => {{
    btn.addEventListener('click', () => {{
      document.querySelectorAll('.rk-store-nav .store-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      rkStore = btn.dataset.rkStore;
      renderRanking();
    }});
  }});

  document.querySelectorAll('.rk-quick .sa-quick-btn').forEach(btn => {{
    btn.addEventListener('click', () => {{
      document.querySelectorAll('.rk-quick .sa-quick-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const [f,t] = rkQuickRange(btn.dataset.rkRange);
      document.getElementById('rk-from').value = f;
      document.getElementById('rk-to').value = t;
      renderRanking();
    }});
  }});

  ['rk-from','rk-to'].forEach(id => {{
    document.getElementById(id).addEventListener('change', () => {{
      document.querySelectorAll('.rk-quick .sa-quick-btn').forEach(b => b.classList.remove('active'));
      renderRanking();
    }});
  }});

  renderRanking();
}})();

// ── Inventory ──
const INV_DATA = {inv_data};

function populateSelect(id, values) {{
  const sel = document.getElementById(id);
  const cur = sel.value;
  while (sel.options.length > 1) sel.remove(1);
  [...values].sort().forEach(v => {{
    const o = document.createElement('option');
    o.value = v; o.textContent = v;
    sel.appendChild(o);
  }});
  if ([...values].includes(cur)) sel.value = cur;
}}

function getFilteredBase() {{
  // Apply filters in cascade order: UPC -> cat -> name -> color -> size
  const fUpc = document.getElementById('f-upc').value.trim();
  const fCat = document.getElementById('f-cat').value;
  const fName = document.getElementById('f-name').value;
  const fColor = document.getElementById('f-color').value;
  const fSize = document.getElementById('f-size').value;

  let data = INV_DATA;
  if (fUpc) data = data.filter(d => d.upc === fUpc);
  if (fCat) data = data.filter(d => d.cat === fCat);
  if (fName) data = data.filter(d => d.name === fName);
  if (fColor) data = data.filter(d => d.color === fColor);
  if (fSize) data = data.filter(d => d.size === fSize);
  return {{ data, fUpc, fCat, fName, fColor, fSize }};
}}

function updateCascade() {{
  const fSearch = document.getElementById('f-search').value.trim().toLowerCase();
  const fUpc = document.getElementById('f-upc').value.trim();
  const fCat = document.getElementById('f-cat').value;
  const fName = document.getElementById('f-name').value;
  const fColor = document.getElementById('f-color').value;

  // Start from search-filtered data
  let pool = INV_DATA;
  if (fSearch) {{
    pool = pool.filter(d =>
      d.name.toLowerCase().includes(fSearch) ||
      d.color.toLowerCase().includes(fSearch) ||
      d.upc.includes(fSearch) ||
      d.sku.toLowerCase().includes(fSearch)
    );
  }}

  // After UPC filter
  if (fUpc) pool = pool.filter(d => d.upc === fUpc);

  // Populate cat from pool
  populateSelect('f-cat', new Set(pool.filter(d => d.cat).map(d => d.cat)));

  // After cat filter
  if (fCat) pool = pool.filter(d => d.cat === fCat);
  populateSelect('f-name', new Set(pool.filter(d => d.name).map(d => d.name)));

  // After name filter
  if (fName) pool = pool.filter(d => d.name === fName);
  populateSelect('f-color', new Set(pool.filter(d => d.color).map(d => d.color)));

  // After color filter
  if (fColor) pool = pool.filter(d => d.color === fColor);
  populateSelect('f-size', new Set(pool.filter(d => d.size).map(d => d.size)));
}}

function onFilterChange(resetDownstream) {{
  // Reset downstream filters
  const order = ['f-cat', 'f-name', 'f-color', 'f-size'];
  const idx = order.indexOf(resetDownstream);
  if (idx >= 0) {{
    for (let i = idx; i < order.length; i++) {{
      document.getElementById(order[i]).value = '';
    }}
  }}
  updateCascade();
  renderInventory();
}}

function initInventory() {{
  // UPC: input with datalist autocomplete
  const upcInput = document.getElementById('f-upc');
  const upcList = document.getElementById('upc-list');
  const allUpcs = [...new Set(INV_DATA.filter(d => d.upc).map(d => d.upc))].sort();

  upcInput.addEventListener('input', () => {{
    const val = upcInput.value.trim();
    upcList.innerHTML = '';
    if (val.length >= 2) {{
      const matches = allUpcs.filter(u => u.startsWith(val)).slice(0, 20);
      matches.forEach(u => {{
        const o = document.createElement('option');
        o.value = u;
        upcList.appendChild(o);
      }});
    }}
    // Trigger filter when exact match or cleared
    if (allUpcs.includes(val) || val === '') {{
      updateCascade();
      renderInventory();
    }}
  }});
  upcInput.addEventListener('change', () => {{ updateCascade(); renderInventory(); }});

  document.getElementById('f-cat').addEventListener('change', () => onFilterChange('f-name'));
  document.getElementById('f-name').addEventListener('change', () => onFilterChange('f-color'));
  document.getElementById('f-color').addEventListener('change', () => onFilterChange('f-size'));
  document.getElementById('f-size').addEventListener('change', () => renderInventory());

  // Fuzzy search — cascade dropdowns + render
  let searchTimer;
  document.getElementById('f-search').addEventListener('input', () => {{
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => {{
      // Reset dropdown filters when search changes
      document.getElementById('f-cat').value = '';
      document.getElementById('f-name').value = '';
      document.getElementById('f-color').value = '';
      document.getElementById('f-size').value = '';
      updateCascade();
      renderInventory();
    }}, 200);
  }});

  updateCascade();
  renderInventory();
}}

function renderInventory() {{
  const {{ data, fUpc, fCat, fName, fColor, fSize }} = getFilteredBase();
  const fSearch = document.getElementById('f-search').value.trim().toLowerCase();

  let filtered = data;

  // Fuzzy search
  if (fSearch) {{
    filtered = filtered.filter(d =>
      d.name.toLowerCase().includes(fSearch) ||
      d.color.toLowerCase().includes(fSearch) ||
      d.upc.includes(fSearch) ||
      d.sku.toLowerCase().includes(fSearch)
    );
  }}

  const hasFilter = fUpc || fCat || fName || fColor || fSize || fSearch;
  if (!hasFilter) {{
    filtered = filtered.filter(d => d.total > 0);
  }}

  // Sort by name → color → size
  filtered.sort((a, b) =>
    a.name.localeCompare(b.name, 'ja') ||
    a.color.localeCompare(b.color, 'ja') ||
    a.size.localeCompare(b.size)
  );

  document.getElementById('inv-count').textContent = filtered.length + ' 件表示';

  const sc = v => v > 0
    ? '<td class="stock has-stock">' + v + '</td>'
    : '<td class="stock zero">0</td>';

  const body = document.getElementById('inv-body');
  body.innerHTML = filtered.map(d => {{
    const img = d.img ? '<img class="inv-img" src="' + d.img + '" loading="lazy">' : '';
    const detail = d.color + (d.size ? ' / ' + d.size : '');
    return '<tr>' +
      '<td class="desktop-only img-col">' + img + '</td>' +
      '<td class="name-col desktop-only">' + d.name + '</td>' +
      '<td class="color-col desktop-only">' + d.color + '</td>' +
      '<td class="size-col desktop-only">' + d.size + '</td>' +
      '<td class="mobile-product"><div class="m-product">' + img + '<div class="m-info"><div class="m-name">' + d.name + '</div><div class="m-detail">' + detail + '</div></div></div></td>' +
      sc(d.hara) + sc(d.shinjuku) + sc(d.osaka) + sc(d.futako) + sc(d.total) + sc(d.ec) +
      '</tr>';
  }}).join('');
}}

initInventory();

// Clear all filters
document.getElementById('clear-filters').addEventListener('click', () => {{
  document.getElementById('f-upc').value = '';
  document.getElementById('f-cat').value = '';
  document.getElementById('f-name').value = '';
  document.getElementById('f-color').value = '';
  document.getElementById('f-size').value = '';
  document.getElementById('f-search').value = '';
  updateCascade();
  renderInventory();
}});

// ── Sales Analysis ──
const SA_DATA = {sa_data};
let saChart = null;
let saStore = '全体';

function addDays(dateStr, n) {{
  const d = new Date(dateStr);
  d.setDate(d.getDate() + n);
  return d.toISOString().slice(0, 10);
}}

function diffDays(from, to) {{
  return Math.round((new Date(to) - new Date(from)) / 86400000);
}}

function setDateRange(from, to) {{
  document.getElementById('sa-from').value = from;
  document.getElementById('sa-to').value = to;
  // Auto-set compare to previous period of same length
  const days = diffDays(from, to);
  const compFrom = addDays(from, -(days + 1));
  document.getElementById('sa-from2').value = compFrom;
  updateCompareTo();
  renderSA();
}}

function updateCompareTo() {{
  const from1 = document.getElementById('sa-from').value;
  const to1 = document.getElementById('sa-to').value;
  const from2 = document.getElementById('sa-from2').value;
  if (from1 && to1 && from2) {{
    const days = diffDays(from1, to1);
    const to2 = addDays(from2, days);
    document.getElementById('sa-to2-label').textContent = '～ ' + to2;
  }}
}}

// Quick date presets
function getQuickRange(key) {{
  const today = new Date();
  const fmt = d => d.toISOString().slice(0, 10);
  const mon = d => {{ const r = new Date(d); r.setDate(r.getDate() - (r.getDay() || 7) + 1); return r; }};
  switch (key) {{
    case 'today': return [fmt(today), fmt(today)];
    case 'yesterday': {{ const y = new Date(today); y.setDate(y.getDate()-1); return [fmt(y), fmt(y)]; }}
    case 'thisweek': return [fmt(mon(today)), fmt(today)];
    case 'lastweek': {{ const m = mon(today); m.setDate(m.getDate()-7); const e = new Date(m); e.setDate(e.getDate()+6); return [fmt(m), fmt(e)]; }}
    case 'thismonth': return [fmt(today).slice(0,8)+'01', fmt(today)];
    case 'lastmonth': {{ const f = new Date(today.getFullYear(), today.getMonth()-1, 1); const l = new Date(today.getFullYear(), today.getMonth(), 0); return [fmt(f), fmt(l)]; }}
    case 'thisyear': return [today.getFullYear()+'-01-01', fmt(today)];
    case 'lastyear': return [(today.getFullYear()-1)+'-01-01', (today.getFullYear()-1)+'-12-31'];
  }}
}}

(function initSA() {{
  // Default: this week
  const [df, dt] = getQuickRange('thisweek');
  setDateRange(df, dt);

  // Store buttons
  document.querySelectorAll('.sa-store-nav .store-btn').forEach(btn => {{
    btn.addEventListener('click', () => {{
      document.querySelectorAll('.sa-store-nav .store-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      saStore = btn.dataset.saStore;
      renderSA();
    }});
  }});

  // Quick buttons
  document.querySelectorAll('.sa-quick-btn').forEach(btn => {{
    btn.addEventListener('click', () => {{
      document.querySelectorAll('.sa-quick-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const [f, t] = getQuickRange(btn.dataset.range);
      setDateRange(f, t);
    }});
  }});

  // Date inputs
  ['sa-from','sa-to'].forEach(id => {{
    document.getElementById(id).addEventListener('change', () => {{
      document.querySelectorAll('.sa-quick-btn').forEach(b => b.classList.remove('active'));
      updateCompareTo();
      renderSA();
    }});
  }});
  document.getElementById('sa-from2').addEventListener('change', () => {{
    updateCompareTo();
    renderSA();
  }});

  // Compare toggle
  document.getElementById('sa-compare-check').addEventListener('change', e => {{
    document.getElementById('sa-compare-group').style.display = e.target.checked ? 'flex' : 'none';
    updateCompareTo();
    renderSA();
  }});
}})();

function renderSA() {{
  const from1 = document.getElementById('sa-from').value;
  const to1 = document.getElementById('sa-to').value;
  const comparing = document.getElementById('sa-compare-check').checked;
  const from2 = document.getElementById('sa-from2').value;
  const days = diffDays(from1, to1);
  const to2 = addDays(from2, days);

  // Filter period A
  const a = SA_DATA.filter(d => d.store === saStore && d.date >= from1 && d.date <= to1).sort((a,b) => a.date.localeCompare(b.date));

  // Aggregate
  const sum = arr => ({{
    sales: arr.reduce((s,d) => s + d.sales, 0),
    qty: arr.reduce((s,d) => s + d.qty, 0),
    customers: arr.reduce((s,d) => s + d.customers, 0),
    atv: arr.length ? Math.round(arr.reduce((s,d) => s + d.sales, 0) / Math.max(arr.reduce((s,d) => s + d.customers, 0), 1)) : 0,
    days: arr.length
  }});

  const sumA = sum(a);

  let sumB = null;
  let b = [];
  if (comparing && from2) {{
    b = SA_DATA.filter(d => d.store === saStore && d.date >= from2 && d.date <= to2).sort((a,b) => a.date.localeCompare(b.date));
    sumB = sum(b);
  }}

  // Render cards
  const fmtYen = n => '¥' + Math.round(n).toLocaleString();
  const fmtNum = n => Math.round(n).toLocaleString();
  const pct = (cur, prev) => {{
    if (!prev) return '';
    const p = ((cur - prev) / prev * 100).toFixed(1);
    const cls = p >= 0 ? 'sa-up' : 'sa-down';
    const sign = p >= 0 ? '+' : '';
    return '<div class="sa-sub ' + cls + '">' + sign + p + '%</div>';
  }};

  const metrics = [
    {{ label: '売上', valA: sumA.sales, valB: sumB ? sumB.sales : 0, fmt: fmtYen }},
    {{ label: '取引数', valA: sumA.qty, valB: sumB ? sumB.qty : 0, fmt: fmtNum }},
    {{ label: '客数', valA: sumA.customers, valB: sumB ? sumB.customers : 0, fmt: fmtNum }},
    {{ label: '客単価', valA: sumA.atv, valB: sumB ? sumB.atv : 0, fmt: fmtYen }},
  ];

  document.getElementById('sa-cards').innerHTML = metrics.map(m => {{
    const compLine = comparing && sumB ? '<div class="sa-sub sa-compare-val">比較: ' + m.fmt(m.valB) + '</div>' : '';
    return '<div class="sa-card">' +
      '<div class="sa-label">' + m.label + '</div>' +
      '<div class="sa-value">' + m.fmt(m.valA) + '</div>' +
      (comparing && sumB ? pct(m.valA, m.valB) + compLine : '') +
      '</div>';
  }}).join('');

  // Render chart — labels are day index (Day1, Day2...) when comparing, otherwise dates
  const ctx = document.getElementById('sa-chart').getContext('2d');
  if (saChart) saChart.destroy();

  const chartLabels = a.map(d => d.date.slice(5));
  const datasets = [{{
    label: from1 + ' ～ ' + to1,
    data: a.map(d => d.sales),
    borderColor: '#0984e3',
    backgroundColor: 'rgba(9,132,227,.08)',
    fill: true,
    tension: 0.3,
    pointRadius: a.length > 31 ? 0 : 3,
    borderWidth: 2,
  }}];

  if (comparing && b.length) {{
    // Pad or trim b to match a's length for overlay
    const bData = b.map(d => d.sales);
    datasets.push({{
      label: from2 + ' ～ ' + to2,
      data: bData,
      borderColor: '#636e72',
      backgroundColor: 'rgba(99,110,114,.05)',
      fill: true,
      tension: 0.3,
      borderDash: [6, 3],
      pointRadius: b.length > 31 ? 0 : 3,
      borderWidth: 2,
    }});
  }}

  saChart = new Chart(ctx, {{
    type: 'line',
    data: {{ labels: chartLabels, datasets }},
    options: {{
      responsive: true,
      maintainAspectRatio: false,
      interaction: {{ mode: 'index', intersect: false }},
      plugins: {{
        legend: {{ display: comparing, position: 'top' }},
        tooltip: {{
          callbacks: {{
            label: item => item.dataset.label + ': ¥' + item.raw.toLocaleString()
          }}
        }}
      }},
      scales: {{
        y: {{
          beginAtZero: true,
          ticks: {{ callback: v => v >= 10000 ? (v/10000).toFixed(0) + '万' : v }}
        }}
      }}
    }}
  }});
}}
</script>
</body>
</html>"""


# ── Main ─────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", default="full", choices=["full", "inventory"])
    args = parser.parse_args()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    if args.mode == "full":
        print("=== FULL BUILD ===")

        print("Fetching SPU info...")
        spu_info = fetch_spu_info()
        print(f"  {len(spu_info)} SPUs")

        print("Fetching ranking data from transactions...")
        rk_json = fetch_ranking_data()
        print(f"  {len(rk_json['spus'])} SPUs, {len(rk_json['data'])} records")
        RANKING_CACHE.write_text(json.dumps({"rk": rk_json, "info": spu_info}, ensure_ascii=False), encoding="utf-8")
        print("Ranking cached.")

        print("Fetching daily sales data...")
        sa_json = fetch_daily_sales()
        SALES_ANALYSIS_CACHE.write_text(json.dumps(sa_json, ensure_ascii=False), encoding="utf-8")
        print(f"  {len(sa_json)} daily records cached.")
    else:
        print("=== INVENTORY ONLY ===")
        if RANKING_CACHE.exists():
            cached = json.loads(RANKING_CACHE.read_text(encoding="utf-8"))
            rk_json = cached["rk"]
            spu_info = cached["info"]
            print("Ranking loaded from cache.")
        else:
            print("WARNING: No ranking cache, running full build instead.")
            return main_full_fallback(now)

    # Load sales analysis from cache
    if SALES_ANALYSIS_CACHE.exists():
        sa_json = json.loads(SALES_ANALYSIS_CACHE.read_text(encoding="utf-8"))
        print(f"Sales analysis loaded ({len(sa_json)} records).")
    else:
        sa_json = []
        print("WARNING: No sales analysis cache.")

    print("Building inventory...")
    inv_json = build_inventory_json()

    print("Assembling page...")
    html = build_page(rk_json, spu_info, inv_json, sa_json, now)
    OUTPUT.write_text(html, encoding="utf-8")
    print(f"Dashboard saved to {OUTPUT}")


def main_full_fallback(now):
    """Fallback: run full build if no cache exists."""
    import sys
    sys.argv = [sys.argv[0], "--mode", "full"]
    main()


if __name__ == "__main__":
    main()
