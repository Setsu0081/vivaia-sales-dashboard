#!/usr/bin/env python3
"""
从 Metabase (bi.vivaia.jp) 拉取 VJP 全体 + 4 店铺销量数据，
按 SPU 汇总后生成 Top 10 商品销量 HTML 报表（含店铺切换）。
"""

import json
import os
import urllib.request
import ssl
from collections import defaultdict
from datetime import datetime
from pathlib import Path

API_BASE = "https://bi.vivaia.jp/api/card/{}/query"
API_KEY = os.environ["METABASE_API_KEY"]
OUTPUT = Path(__file__).parent / "index.html"

# card_id, label, col_name_idx, col_color_idx, col_sales_start
IMAGE_CARD_ID = 90  # MD_商品信息汇总 — first column is image URL, second is SPU

SOURCES = [
    (117, "VJP 全体",  4, 5, 7),   # SPU,SKU,UPC,カテゴリ,商品名,カラー,サイズ,L1..L30
    (129, "ハラカド店", 3, 4, 6),   # SPU,SKU,カテゴリ,商品名,カラー,サイズ,L1..L30
    (130, "新宿店",    3, 4, 6),
    (131, "大阪店",    3, 4, 6),
    (132, "二子玉川店", 3, 4, 6),
]


def fetch_card(card_id):
    ctx = ssl.create_default_context()
    req = urllib.request.Request(
        API_BASE.format(card_id),
        method="POST",
        headers={"X-Api-Key": API_KEY, "Content-Type": "application/json"},
        data=b"{}",
    )
    with urllib.request.urlopen(req, context=ctx) as resp:
        return json.loads(resp.read())


def fetch_image_map():
    """Fetch SPU -> image URL mapping from MD_商品信息汇总."""
    raw = fetch_card(IMAGE_CARD_ID)
    img_map = {}
    for r in raw["data"]["rows"]:
        spu, img = r[1], r[0]
        if spu not in img_map and img:
            img_map[spu] = img
    return img_map


def aggregate(raw, name_idx, color_idx, sales_start):
    rows = raw["data"]["rows"]
    spu_map = defaultdict(lambda: {"name": "", "color": "", "l1": 0, "l3": 0, "l7": 0, "l15": 0, "l30": 0})
    for r in rows:
        spu = r[0]
        d = spu_map[spu]
        d["name"] = r[name_idx]
        d["color"] = r[color_idx] or ""
        d["l1"] += r[sales_start] or 0
        d["l3"] += r[sales_start + 1] or 0
        d["l7"] += r[sales_start + 2] or 0
        d["l15"] += r[sales_start + 3] or 0
        d["l30"] += r[sales_start + 4] or 0
    return spu_map


def build_store_section(store_id, spu_map, img_map):
    def top10(key):
        return sorted(spu_map.items(), key=lambda x: x[1][key], reverse=True)[:10]

    periods = [
        ("1\u65e5", "l1"),
        ("3\u65e5", "l3"),
        ("7\u65e5", "l7"),
        ("15\u65e5", "l15"),
        ("30\u65e5", "l30"),
    ]

    tab_buttons = ""
    tab_contents = ""
    for i, (label, key) in enumerate(periods):
        active = "active" if i == 2 else ""
        tid = f"tab-{store_id}-{key}"
        tab_buttons += f'<button class="tab-btn {active}" data-tab="{tid}">{label}</button>\n'

        ranked = top10(key)
        rows_html = ""
        for rank, (spu, d) in enumerate(ranked, 1):
            medal = {1: "\U0001f947", 2: "\U0001f948", 3: "\U0001f949"}.get(rank, str(rank))
            img_url = img_map.get(spu, "")
            img_tag = f'<img class="product-img" src="{img_url}" alt="" loading="lazy">' if img_url else '<div class="product-img no-img"></div>'
            rows_html += f"""
            <tr>
                <td class="rank">{medal}</td>
                <td class="product-cell">
                    {img_tag}
                    <div class="product-info">
                        <div class="product-name">{d['name']}</div>
                        <div class="product-color">{d['color']}</div>
                    </div>
                </td>
                <td class="num highlight">{int(d[key])}</td>
                <td class="num hide-mobile">{int(d['l1'])}</td>
                <td class="num hide-mobile">{int(d['l3'])}</td>
                <td class="num hide-mobile">{int(d['l7'])}</td>
                <td class="num hide-mobile">{int(d['l15'])}</td>
                <td class="num hide-mobile">{int(d['l30'])}</td>
            </tr>"""

        tab_contents += f"""
        <div class="tab-content {'active' if i == 2 else ''}" id="{tid}">
          <div class="table-wrap">
            <table>
                <thead>
                    <tr>
                        <th width="40">#</th>
                        <th>\u5546\u54c1</th>
                        <th class="num">\u8a72\u5f53\u671f\u9593</th>
                        <th class="num hide-mobile">1\u65e5</th>
                        <th class="num hide-mobile">3\u65e5</th>
                        <th class="num hide-mobile">7\u65e5</th>
                        <th class="num hide-mobile">15\u65e5</th>
                        <th class="num hide-mobile">30\u65e5</th>
                    </tr>
                </thead>
                <tbody>{rows_html}
                </tbody>
            </table>
          </div>
        </div>"""

    total_l1 = sum(d["l1"] for d in spu_map.values())
    total_l3 = sum(d["l3"] for d in spu_map.values())
    total_l7 = sum(d["l7"] for d in spu_map.values())
    total_l30 = sum(d["l30"] for d in spu_map.values())

    stats = f"""
    <div class="stats">
      <div class="stat-card"><div class="label">\u6628\u65e5</div><div class="value">{int(total_l1)}</div></div>
      <div class="stat-card"><div class="label">3\u65e5\u9593</div><div class="value">{int(total_l3)}</div></div>
      <div class="stat-card"><div class="label">7\u65e5\u9593</div><div class="value">{int(total_l7)}</div></div>
      <div class="stat-card"><div class="label">30\u65e5\u9593</div><div class="value">{int(total_l30)}</div></div>
    </div>"""

    return stats, tab_buttons, tab_contents


def build_html(all_data, img_map):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Build store nav + sections
    store_nav = ""
    store_sections = ""
    for i, (card_id, label, spu_map) in enumerate(all_data):
        sid = f"store-{i}"
        active = "active" if i == 0 else ""
        store_nav += f'<button class="store-btn {active}" data-store="{sid}">{label}</button>\n'

        stats, tab_buttons, tab_contents = build_store_section(sid, spu_map, img_map)
        store_sections += f"""
    <div class="store-section {'active' if i == 0 else ''}" id="{sid}">
      {stats}
      <div class="tabs">{tab_buttons}</div>
      {tab_contents}
    </div>"""

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>VIVAIA Japan \u2014 \u8ca9\u58f2 Top 10</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, 'Helvetica Neue', 'Segoe UI', sans-serif; background: #f5f6fa; color: #2d3436; -webkit-text-size-adjust: 100%; }}
  .container {{ max-width: 960px; margin: 0 auto; padding: 20px 12px; }}
  header {{ margin-bottom: 20px; }}
  header h1 {{ font-size: 20px; font-weight: 700; }}
  header .time {{ color: #636e72; font-size: 12px; margin-top: 4px; }}
  .store-nav {{ display: flex; gap: 0; margin-bottom: 20px; border-radius: 10px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }}
  .store-btn {{ flex: 1; padding: 10px 8px; border: none; background: #fff; cursor: pointer; font-size: 13px; font-weight: 600; color: #636e72; transition: all .2s; border-right: 1px solid #f1f2f6; }}
  .store-btn:last-child {{ border-right: none; }}
  .store-btn.active {{ background: #0984e3; color: #fff; }}
  .store-btn:hover:not(.active) {{ background: #dfe6e9; }}
  .store-section {{ display: none; }}
  .store-section.active {{ display: block; }}
  .stats {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 20px; }}
  .stat-card {{ background: #fff; border-radius: 10px; padding: 12px 14px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }}
  .stat-card .label {{ font-size: 11px; color: #636e72; margin-bottom: 2px; }}
  .stat-card .value {{ font-size: 22px; font-weight: 700; color: #0984e3; }}
  .tabs {{ display: flex; gap: 6px; margin-bottom: 14px; overflow-x: auto; -webkit-overflow-scrolling: touch; }}
  .tab-btn {{ padding: 7px 14px; border: none; border-radius: 8px; background: #dfe6e9; cursor: pointer; font-size: 13px; font-weight: 500; transition: all .2s; white-space: nowrap; }}
  .tab-btn.active {{ background: #0984e3; color: #fff; }}
  .tab-btn:hover {{ background: #74b9ff; color: #fff; }}
  .tab-content {{ display: none; }}
  .tab-content.active {{ display: block; }}
  .table-wrap {{ overflow-x: auto; -webkit-overflow-scrolling: touch; border-radius: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }}
  table {{ width: 100%; background: #fff; border-collapse: collapse; min-width: 320px; }}
  thead {{ background: #f8f9fa; }}
  th {{ padding: 10px 10px; text-align: left; font-size: 11px; color: #636e72; font-weight: 600; text-transform: uppercase; letter-spacing: 0.3px; white-space: nowrap; }}
  td {{ padding: 10px; border-top: 1px solid #f1f2f6; font-size: 13px; }}
  tr:hover {{ background: #f8f9fa; }}
  .rank {{ font-size: 16px; text-align: center; }}
  .product-cell {{ display: flex; align-items: center; gap: 10px; }}
  .product-img {{ width: 44px; height: 44px; border-radius: 6px; object-fit: cover; flex-shrink: 0; background: #f1f2f6; }}
  .no-img {{ width: 44px; height: 44px; border-radius: 6px; background: #f1f2f6; flex-shrink: 0; }}
  .product-info {{ min-width: 0; }}
  .product-name {{ font-weight: 600; font-size: 13px; }}
  .product-color {{ font-size: 11px; color: #636e72; margin-top: 1px; }}
  .num {{ text-align: right; font-variant-numeric: tabular-nums; }}
  .highlight {{ font-weight: 700; color: #0984e3; font-size: 15px; }}
  th.num {{ text-align: right; }}
  footer {{ text-align: center; margin-top: 24px; font-size: 11px; color: #b2bec3; }}
  @media (max-width: 600px) {{
    .stats {{ grid-template-columns: repeat(2, 1fr); }}
    .stat-card .value {{ font-size: 20px; }}
    .hide-mobile {{ display: none; }}
    header h1 {{ font-size: 17px; }}
    td {{ padding: 8px 6px; font-size: 12px; }}
    th {{ padding: 8px 6px; font-size: 10px; }}
    .rank {{ font-size: 14px; }}
    .highlight {{ font-size: 14px; }}
    .store-btn {{ font-size: 11px; padding: 9px 4px; }}
    .product-img {{ width: 36px; height: 36px; }}
    .no-img {{ width: 36px; height: 36px; }}
    .product-cell {{ gap: 8px; }}
  }}
</style>
</head>
<body>
<div class="container">
  <header>
    <h1>VIVAIA Japan \u2014 \u8ca9\u58f2 Top 10</h1>
    <div class="time">\u66f4\u65b0: {now}\u3000\uff5c\u3000\u30c7\u30fc\u30bf\u30bd\u30fc\u30b9: Metabase</div>
  </header>
  <div class="store-nav">
    {store_nav}
  </div>
  {store_sections}
</div>
<footer>Auto-generated hourly from Metabase</footer>
<script>
// Store navigation
document.querySelectorAll('.store-btn').forEach(btn => {{
  btn.addEventListener('click', () => {{
    document.querySelectorAll('.store-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.store-section').forEach(s => s.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById(btn.dataset.store).classList.add('active');
  }});
}});
// Period tabs (scoped within each store section)
document.querySelectorAll('.tab-btn').forEach(btn => {{
  btn.addEventListener('click', () => {{
    const section = btn.closest('.store-section');
    section.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    section.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById(btn.dataset.tab).classList.add('active');
  }});
}});
</script>
</body>
</html>"""


if __name__ == "__main__":
    print("Fetching product images (card 90)...")
    img_map = fetch_image_map()
    print(f"  {len(img_map)} SPU images loaded")

    all_data = []
    for card_id, label, name_idx, color_idx, sales_start in SOURCES:
        print(f"Fetching {label} (card {card_id})...")
        raw = fetch_card(card_id)
        spu_map = aggregate(raw, name_idx, color_idx, sales_start)
        print(f"  {len(raw['data']['rows'])} rows -> {len(spu_map)} SPUs")
        all_data.append((card_id, label, spu_map))

    html = build_html(all_data, img_map)
    OUTPUT.write_text(html, encoding="utf-8")
    print(f"\nDashboard saved to {OUTPUT}")
