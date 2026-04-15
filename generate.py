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

        # Stats
        t1 = sum(d["l1"] for d in spu_map.values())
        t3 = sum(d["l3"] for d in spu_map.values())
        t7 = sum(d["l7"] for d in spu_map.values())
        t30 = sum(d["l30"] for d in spu_map.values())

        # Period tabs + tables
        tabs_html = ""
        contents_html = ""
        for pi, (plabel, key) in enumerate(periods):
            pactive = "active" if pi == 2 else ""
            tid = f"tab-{sid}-{key}"
            tabs_html += f'<button class="tab-btn {pactive}" data-tab="{tid}">{plabel}</button>\n'

            ranked = top10(spu_map, key)
            rows_html = ""
            for rank, (spu, d) in enumerate(ranked, 1):
                medal = {1: "\U0001f947", 2: "\U0001f948", 3: "\U0001f949"}.get(rank, str(rank))
                img_url = img_map.get(spu, "")
                img_tag = f'<img class="product-img" src="{img_url}" loading="lazy">' if img_url else '<div class="product-img no-img"></div>'
                rows_html += f"""<tr>
                  <td class="rank">{medal}</td>
                  <td class="product-cell">{img_tag}<div class="product-info"><div class="product-name">{d['name']}</div><div class="product-color">{d['color']}</div></div></td>
                  <td class="num highlight">{int(d[key])}</td>
                  <td class="num hide-mobile">{int(d['l1'])}</td>
                  <td class="num hide-mobile">{int(d['l3'])}</td>
                  <td class="num hide-mobile">{int(d['l7'])}</td>
                  <td class="num hide-mobile">{int(d['l15'])}</td>
                  <td class="num hide-mobile">{int(d['l30'])}</td>
                </tr>"""

            contents_html += f"""<div class="tab-content {'active' if pi == 2 else ''}" id="{tid}">
              <div class="table-wrap"><table>
                <thead><tr>
                  <th width="40">#</th><th>商品</th><th class="num">該当期間</th>
                  <th class="num hide-mobile">1日</th><th class="num hide-mobile">3日</th>
                  <th class="num hide-mobile">7日</th><th class="num hide-mobile">15日</th>
                  <th class="num hide-mobile">30日</th>
                </tr></thead>
                <tbody>{rows_html}</tbody>
              </table></div></div>"""

        store_sections += f"""<div class="store-section {'active' if i == 0 else ''}" id="{sid}">
          <div class="stats">
            <div class="stat-card"><div class="label">昨日</div><div class="value">{int(t1)}</div></div>
            <div class="stat-card"><div class="label">3日間</div><div class="value">{int(t3)}</div></div>
            <div class="stat-card"><div class="label">7日間</div><div class="value">{int(t7)}</div></div>
            <div class="stat-card"><div class="label">30日間</div><div class="value">{int(t30)}</div></div>
          </div>
          <div class="tabs">{tabs_html}</div>
          {contents_html}
        </div>"""

    return f"""<div class="store-nav">{store_nav}</div>{store_sections}"""


# ── Inventory logic ──────────────────────────────────────────

def build_inventory_json():
    """Fetch inventory + product info, return JSON data for client-side rendering."""
    print("  Fetching inventory (card 120)...")
    _, inv_rows = fetch_csv(INVENTORY_CARD)

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
            "warehouse": int(to_num(r[5])),
            "total": int(to_num(r[6])),
        })

    print(f"  {len(items)} SKUs loaded")
    return items


# ── Page assembly ────────────────────────────────────────────

def build_page(ranking_html, inventory_json, now):
    inv_data = json.dumps(inventory_json, ensure_ascii=False, separators=(",", ":"))

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
.main {{ margin-left:180px; flex:1; padding:20px 16px; max-width:1060px; }}
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
footer {{ text-align:center; margin-top:20px; font-size:10px; color:#b2bec3; }}
/* Inventory filters */
.filters {{ display:flex; gap:8px; margin-bottom:14px; flex-wrap:wrap; }}
.filter-group {{ flex:1; min-width:140px; }}
.filter-group label {{ display:block; font-size:10px; color:#636e72; margin-bottom:3px; font-weight:600; }}
.filter-group select {{ width:100%; padding:7px 8px; border:1px solid #dfe6e9; border-radius:7px; font-size:12px; background:#fff; appearance:auto; }}
.inv-count {{ font-size:11px; color:#636e72; margin-bottom:10px; }}
.inv-table td.stock {{ text-align:center; font-variant-numeric:tabular-nums; }}
.inv-table td.stock.has-stock {{ font-weight:600; color:#00b894; }}
.inv-table th.stock {{ text-align:center; }}
.inv-img {{ width:32px; height:32px; border-radius:4px; object-fit:cover; background:#f1f2f6; }}
/* Mobile */
@media (max-width:768px) {{
  .sidebar {{ position:fixed; bottom:0; top:auto; left:0; width:100%; height:auto; display:flex; padding:0; z-index:100; }}
  .sidebar .logo {{ display:none; }}
  .sidebar a {{ flex:1; text-align:center; padding:10px 4px; font-size:11px; border-top:1px solid #636e72; }}
  .main {{ margin-left:0; margin-bottom:50px; padding:14px 10px; }}
  .hide-mobile {{ display:none; }}
  .stats {{ grid-template-columns:repeat(2,1fr); }}
  .store-btn {{ font-size:11px; padding:8px 4px; }}
  .filters {{ flex-direction:column; }}
  .filter-group {{ min-width:100%; }}
}}
</style>
</head>
<body>
<div class="sidebar">
  <div class="logo">VIVAIA Japan</div>
  <a href="#" class="active" data-page="ranking">商品ランキング</a>
  <a href="#" data-page="inventory">在庫確認</a>
</div>
<div class="main">
  <!-- Ranking page -->
  <div id="page-ranking" class="page active">
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
    <div class="filters">
      <div class="filter-group"><label>UPC</label><select id="f-upc"><option value="">すべて</option></select></div>
      <div class="filter-group"><label>カテゴリ</label><select id="f-cat"><option value="">すべて</option></select></div>
      <div class="filter-group"><label>商品名</label><select id="f-name"><option value="">すべて</option></select></div>
      <div class="filter-group"><label>カラー</label><select id="f-color"><option value="">すべて</option></select></div>
      <div class="filter-group"><label>サイズ</label><select id="f-size"><option value="">すべて</option></select></div>
    </div>
    <div class="inv-count" id="inv-count"></div>
    <div class="table-wrap">
      <table class="inv-table">
        <thead><tr>
          <th>商品</th>
          <th class="stock">ハラカド</th>
          <th class="stock">新宿</th>
          <th class="stock">大阪</th>
          <th class="stock">二子玉川</th>
          <th class="stock">門店計</th>
          <th class="stock hide-mobile">東莞倉</th>
        </tr></thead>
        <tbody id="inv-body"></tbody>
      </table>
    </div>
  </div>
</div>
<footer>Auto-generated from Metabase</footer>
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

function initInventory() {{
  const filters = {{upc: new Set(), cat: new Set(), name: new Set(), color: new Set(), size: new Set()}};
  INV_DATA.forEach(d => {{
    if (d.upc) filters.upc.add(d.upc);
    if (d.cat) filters.cat.add(d.cat);
    if (d.name) filters.name.add(d.name);
    if (d.color) filters.color.add(d.color);
    if (d.size) filters.size.add(d.size);
  }});
  const populate = (id, vals) => {{
    const sel = document.getElementById(id);
    [...vals].sort().forEach(v => {{
      const o = document.createElement('option');
      o.value = v; o.textContent = v;
      sel.appendChild(o);
    }});
  }};
  populate('f-upc', filters.upc);
  populate('f-cat', filters.cat);
  populate('f-name', filters.name);
  populate('f-color', filters.color);
  populate('f-size', filters.size);

  ['f-upc','f-cat','f-name','f-color','f-size'].forEach(id => {{
    document.getElementById(id).addEventListener('change', renderInventory);
  }});
  renderInventory();
}}

function renderInventory() {{
  const fUpc = document.getElementById('f-upc').value;
  const fCat = document.getElementById('f-cat').value;
  const fName = document.getElementById('f-name').value;
  const fColor = document.getElementById('f-color').value;
  const fSize = document.getElementById('f-size').value;

  let filtered = INV_DATA;
  if (fUpc) filtered = filtered.filter(d => d.upc === fUpc);
  if (fCat) filtered = filtered.filter(d => d.cat === fCat);
  if (fName) filtered = filtered.filter(d => d.name === fName);
  if (fColor) filtered = filtered.filter(d => d.color === fColor);
  if (fSize) filtered = filtered.filter(d => d.size === fSize);

  // Default: show only items with store inventory > 0, unless filtering
  const hasFilter = fUpc || fCat || fName || fColor || fSize;
  if (!hasFilter) {{
    filtered = filtered.filter(d => d.total > 0 || d.warehouse > 0);
  }}

  document.getElementById('inv-count').textContent = filtered.length + ' 件表示';

  const body = document.getElementById('inv-body');
  const html = filtered.map(d => {{
    const img = d.img ? '<img class="inv-img" src="' + d.img + '" loading="lazy">' : '';
    const sc = v => v > 0 ? '<td class="stock has-stock">' + v + '</td>' : '<td class="stock">0</td>';
    return '<tr>' +
      '<td class="product-cell">' + img + '<div class="product-info"><div class="product-name">' + d.name + '</div><div class="product-color">' + d.color + (d.size ? ' / ' + d.size : '') + '</div></div></td>' +
      sc(d.hara) + sc(d.shinjuku) + sc(d.osaka) + sc(d.futako) + sc(d.total) +
      '<td class="stock hide-mobile">' + d.warehouse + '</td>' +
      '</tr>';
  }}).join('');
  body.innerHTML = html;
}}

initInventory();
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
    else:
        print("=== INVENTORY ONLY ===")
        if RANKING_CACHE.exists():
            ranking_html = RANKING_CACHE.read_text(encoding="utf-8")
            print("Ranking loaded from cache.")
        else:
            print("WARNING: No ranking cache, running full build instead.")
            return main_full_fallback(now)

    print("Building inventory...")
    inv_json = build_inventory_json()

    print("Assembling page...")
    html = build_page(ranking_html, inv_json, now)
    OUTPUT.write_text(html, encoding="utf-8")
    print(f"Dashboard saved to {OUTPUT}")


def main_full_fallback(now):
    """Fallback: run full build if no cache exists."""
    import sys
    sys.argv = [sys.argv[0], "--mode", "full"]
    main()


if __name__ == "__main__":
    main()
