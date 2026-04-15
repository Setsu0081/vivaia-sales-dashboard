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
RANKING_CACHE = DIR / "ranking_cache.html"
SALES_ANALYSIS_CACHE = DIR / "sales_analysis_cache.json"

IMAGE_CARD = 90
INVENTORY_CARD = 120
PRODUCT_CARD = 90

SALES_SOURCES = [
    (117, "VJP 全体",  4, 5, 7),
    (129, "ハラカド店", 3, 4, 6),
    (130, "新宿店",    3, 4, 6),
    (131, "大阪店",    3, 4, 6),
    (132, "二子玉川店", 3, 4, 6),
]


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
    # Store scope mapping
    scope_map = {"1": "ハラカド店", "2": "新宿店", "3": "大阪店", "13": "二子玉川店", "all": "全体"}
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


def aggregate_sales(headers, rows, name_idx, color_idx, sales_start):
    spu_map = defaultdict(lambda: {"name": "", "color": "", "l1": 0, "l3": 0, "l7": 0, "l15": 0, "l30": 0})
    for r in rows:
        spu = r[0]
        d = spu_map[spu]
        d["name"] = r[name_idx]
        d["color"] = r[color_idx] if color_idx < len(r) else ""
        d["l1"] += to_num(r[sales_start])
        d["l3"] += to_num(r[sales_start + 1])
        d["l7"] += to_num(r[sales_start + 2])
        d["l15"] += to_num(r[sales_start + 3]) if sales_start + 3 < len(r) else 0
        d["l30"] += to_num(r[sales_start + 4]) if sales_start + 4 < len(r) else 0
    return spu_map


def _pct_html(cur, prev):
    """Generate HTML for percentage change."""
    if not prev or prev == 0:
        return '<span class="pct-na">-</span>'
    p = (cur - prev) / prev * 100
    if p >= 0:
        return f'<span class="pct-up">\u2191{p:.1f}%</span>'
    else:
        return f'<span class="pct-down">\u2193{abs(p):.1f}%</span>'


def _prev_period_val(d, key):
    """Approximate previous same-length period value for a product."""
    # key -> (current, next_larger, scale_factor)
    mapping = {
        "l1": ("l1", "l3", 2),    # L3-L1 = 2 days, prev 1 day ≈ (L3-L1)/2
        "l3": ("l3", "l7", 4/3),  # L7-L3 = 4 days, prev 3 days ≈ (L7-L3)*3/4
        "l7": ("l7", "l15", 8/7), # L15-L7 = 8 days, prev 7 days ≈ (L15-L7)*7/8
        "l15": ("l15", "l30", 1), # L30-L15 = 15 days (exact)
        "l30": None,
    }
    m = mapping.get(key)
    if not m:
        return None
    cur_key, next_key, scale = m
    diff = d[next_key] - d[cur_key]
    if diff <= 0:
        return None
    return diff / scale


def build_ranking_html(all_data, img_map):
    def top10(spu_map, key):
        return sorted(spu_map.items(), key=lambda x: x[1][key], reverse=True)[:10]

    periods = [("1日", "l1"), ("3日", "l3"), ("7日", "l7"), ("15日", "l15"), ("30日", "l30")]

    store_nav = ""
    store_sections = ""
    for i, (card_id, label, spu_map) in enumerate(all_data):
        sid = f"store-{i}"
        active = "active" if i == 0 else ""
        store_nav += f'<button class="store-btn {active}" data-store="{sid}">{label}</button>\n'

        tabs_html = ""
        contents_html = ""
        for pi, (plabel, key) in enumerate(periods):
            pactive = "active" if pi == 2 else ""
            tid = f"tab-{sid}-{key}"
            tabs_html += f'<button class="tab-btn {pactive}" data-tab="{tid}" data-period="{key}">{plabel}</button>\n'

            # Total for this period
            total_cur = sum(d[key] for d in spu_map.values())
            total_prev_val = sum(_prev_period_val(d, key) or 0 for d in spu_map.values())
            total_prev_pct = _pct_html(total_cur, total_prev_val) if total_prev_val > 0 else '<span class="pct-na">-</span>'

            ranked = top10(spu_map, key)
            rows_html = ""
            for rank, (spu, d) in enumerate(ranked, 1):
                medal = {1: "\U0001f947", 2: "\U0001f948", 3: "\U0001f949"}.get(rank, str(rank))
                img_url = img_map.get(spu, "")
                img_tag = f'<img class="product-img" src="{img_url}" loading="lazy">' if img_url else '<div class="product-img no-img"></div>'
                prev = _prev_period_val(d, key)
                pct_html = _pct_html(d[key], prev)
                rows_html += f"""<tr>
                  <td class="rank">{medal}</td>
                  <td class="product-cell">{img_tag}<div class="product-info"><div class="product-name">{d['name']}</div><div class="product-color">{d['color']}</div></div></td>
                  <td class="num highlight">{int(d[key])}</td>
                  <td class="num">{pct_html}</td>
                </tr>"""

            contents_html += f"""<div class="tab-content {'active' if pi == 2 else ''}" id="{tid}">
              <div class="rk-summary">
                <div class="rk-total"><span class="rk-total-num">{int(total_cur):,}</span><span class="rk-total-label">販売数</span></div>
                <div class="rk-comp"><span class="rk-comp-label">環比</span>{total_prev_pct}</div>
              </div>
              <div class="table-wrap"><table>
                <thead><tr>
                  <th width="40">#</th><th>商品</th><th class="num">該当期間</th>
                  <th class="num">環比</th>
                </tr></thead>
                <tbody>{rows_html}</tbody>
              </table></div></div>"""

        store_sections += f"""<div class="store-section {'active' if i == 0 else ''}" id="{sid}">
          <div class="tabs">{tabs_html}</div>
          {contents_html}
        </div>"""

    return f"""<div class="store-nav">{store_nav}</div>{store_sections}"""


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

def build_page(ranking_html, inventory_json, sales_analysis_json, now):
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
<div class="sidebar">
  <div class="logo">VIVAIA Japan</div>
  <a href="#" class="active" data-page="analysis">売上分析</a>
  <a href="#" data-page="ranking">商品ランキング</a>
  <a href="#" data-page="inventory">在庫確認</a>
</div>
<div class="main">
  <!-- Ranking page -->
  <div id="page-ranking" class="page">
    <header>
      <h1>販売 Top 10</h1>
      <div class="time">更新: {now}</div>
    </header>
    {ranking_html}
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
      <button class="store-btn active" data-sa-store="全体">全体</button>
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
// ── Store tabs ──
document.querySelectorAll('.store-btn').forEach(btn => {{
  btn.addEventListener('click', () => {{
    document.querySelectorAll('.store-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.store-section').forEach(s => s.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById(btn.dataset.store).classList.add('active');
  }});
}});
// ── Period tabs ──
document.querySelectorAll('.tab-btn').forEach(btn => {{
  btn.addEventListener('click', () => {{
    const sec = btn.closest('.store-section');
    sec.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    sec.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById(btn.dataset.tab).classList.add('active');
  }});
}});

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
  const fmt = n => {{
    if (Math.abs(n) >= 100000000) return (n / 100000000).toFixed(2) + '億';
    if (Math.abs(n) >= 10000) return (n / 10000).toFixed(1) + '万';
    return n.toLocaleString();
  }};
  const pct = (cur, prev) => {{
    if (!prev) return '';
    const p = ((cur - prev) / prev * 100).toFixed(1);
    const cls = p >= 0 ? 'sa-up' : 'sa-down';
    const sign = p >= 0 ? '+' : '';
    return '<div class="sa-sub ' + cls + '">' + sign + p + '%</div>';
  }};
  const compLine = val => comparing && sumB ? '<div class="sa-sub sa-compare-val">比較: ' + fmt(val) + '</div>' : '';

  const metrics = [
    {{ label: '売上', valA: sumA.sales, valB: sumB ? sumB.sales : 0 }},
    {{ label: '取引数', valA: sumA.qty, valB: sumB ? sumB.qty : 0 }},
    {{ label: '客数', valA: sumA.customers, valB: sumB ? sumB.customers : 0 }},
    {{ label: '客単価', valA: sumA.atv, valB: sumB ? sumB.atv : 0 }},
  ];

  document.getElementById('sa-cards').innerHTML = metrics.map(m => {{
    return '<div class="sa-card">' +
      '<div class="sa-label">' + m.label + '</div>' +
      '<div class="sa-value">¥' + fmt(m.valA) + '</div>' +
      (comparing && sumB ? pct(m.valA, m.valB) + compLine(m.valB) : '') +
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
        print("Fetching images...")
        img_map = fetch_image_map()
        print(f"  {len(img_map)} images")

        all_data = []
        for card_id, label, ni, ci, ss in SALES_SOURCES:
            print(f"Fetching {label} (card {card_id})...")
            h, rows = fetch_csv(card_id)
            spu_map = aggregate_sales(h, rows, ni, ci, ss)
            print(f"  {len(rows)} rows -> {len(spu_map)} SPUs")
            all_data.append((card_id, label, spu_map))

        ranking_html = build_ranking_html(all_data, img_map)
        RANKING_CACHE.write_text(ranking_html, encoding="utf-8")
        print("Ranking cached.")

        print("Fetching daily sales data...")
        sa_json = fetch_daily_sales()
        SALES_ANALYSIS_CACHE.write_text(json.dumps(sa_json, ensure_ascii=False), encoding="utf-8")
        print(f"  {len(sa_json)} daily records cached.")
    else:
        print("=== INVENTORY ONLY ===")
        if RANKING_CACHE.exists():
            ranking_html = RANKING_CACHE.read_text(encoding="utf-8")
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
    html = build_page(ranking_html, inv_json, sa_json, now)
    OUTPUT.write_text(html, encoding="utf-8")
    print(f"Dashboard saved to {OUTPUT}")


def main_full_fallback(now):
    """Fallback: run full build if no cache exists."""
    import sys
    sys.argv = [sys.argv[0], "--mode", "full"]
    main()


if __name__ == "__main__":
    main()
