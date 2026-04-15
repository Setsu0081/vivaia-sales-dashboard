#!/usr/bin/env python3
"""
从 Metabase (bi.vivaia.jp) 拉取 MD_VJP过去销量，
按 SPU 汇总后生成 Top 10 商品销量 HTML 报表。
"""

import json
import os
import urllib.request
import ssl
from collections import defaultdict
from datetime import datetime
from pathlib import Path

API_URL = "https://bi.vivaia.jp/api/card/117/query"
API_KEY = os.environ["METABASE_API_KEY"]
OUTPUT = Path(__file__).parent / "index.html"


def fetch_data():
    ctx = ssl.create_default_context()
    req = urllib.request.Request(
        API_URL,
        method="POST",
        headers={"X-Api-Key": API_KEY, "Content-Type": "application/json"},
        data=b"{}",
    )
    with urllib.request.urlopen(req, context=ctx) as resp:
        return json.loads(resp.read())


def aggregate(raw):
    rows = raw["data"]["rows"]
    spu_map = defaultdict(lambda: {"name": "", "cat": "", "color": "", "l1": 0, "l3": 0, "l7": 0, "l15": 0, "l30": 0})
    for r in rows:
        spu, cat, name, color = r[0], r[3], r[4], r[5] or ""
        d = spu_map[spu]
        d["name"] = name
        d["cat"] = cat
        d["color"] = color
        d["l1"] += r[7] or 0
        d["l3"] += r[8] or 0
        d["l7"] += r[9] or 0
        d["l15"] += r[10] or 0
        d["l30"] += r[11] or 0
    return spu_map


def build_html(spu_map):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    def top10(key):
        return sorted(spu_map.items(), key=lambda x: x[1][key], reverse=True)[:10]

    periods = [
        ("過去 1 日", "l1"),
        ("過去 3 日", "l3"),
        ("過去 7 日", "l7"),
        ("過去 15 日", "l15"),
        ("過去 30 日", "l30"),
    ]

    def trend_bar(d):
        vals = [d["l1"], d["l3"], d["l7"], d["l15"], d["l30"]]
        mx = max(vals) if max(vals) > 0 else 1
        bars = []
        labels = ["1d", "3d", "7d", "15d", "30d"]
        for v, lb in zip(vals, labels):
            pct = v / mx * 100
            bars.append(
                f'<div class="bar-wrap" title="{lb}: {int(v)}">'
                f'<div class="bar" style="height:{max(pct,4)}%"></div>'
                f'<span class="bar-label">{lb}</span></div>'
            )
        return "".join(bars)

    tab_buttons = ""
    tab_contents = ""
    for i, (label, key) in enumerate(periods):
        active = "active" if i == 2 else ""
        tab_buttons += f'<button class="tab-btn {active}" data-tab="tab-{key}">{label}</button>\n'

        ranked = top10(key)
        rows_html = ""
        for rank, (spu, d) in enumerate(ranked, 1):
            medal = {1: "\U0001f947", 2: "\U0001f948", 3: "\U0001f949"}.get(rank, str(rank))
            rows_html += f"""
            <tr>
                <td class="rank">{medal}</td>
                <td>
                    <div class="product-name">{d['name']}</div>
                    <div class="product-cat">{d['cat']}\u3000{d['color']}</div>
                </td>
                <td class="num highlight">{int(d[key])}</td>
                <td class="num">{int(d['l1'])}</td>
                <td class="num">{int(d['l3'])}</td>
                <td class="num">{int(d['l7'])}</td>
                <td class="num">{int(d['l15'])}</td>
                <td class="num">{int(d['l30'])}</td>
                <td class="trend">{trend_bar(d)}</td>
            </tr>"""

        tab_contents += f"""
        <div class="tab-content {'active' if i == 2 else ''}" id="tab-{key}">
            <table>
                <thead>
                    <tr>
                        <th width="50">#</th>
                        <th>商品</th>
                        <th class="num">該当期間</th>
                        <th class="num">1日</th>
                        <th class="num">3日</th>
                        <th class="num">7日</th>
                        <th class="num">15日</th>
                        <th class="num">30日</th>
                        <th width="140">トレンド</th>
                    </tr>
                </thead>
                <tbody>{rows_html}
                </tbody>
            </table>
        </div>"""

    total_l1 = sum(d["l1"] for d in spu_map.values())
    total_l7 = sum(d["l7"] for d in spu_map.values())
    total_l30 = sum(d["l30"] for d in spu_map.values())
    active_spu = sum(1 for d in spu_map.values() if d["l7"] > 0)

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>VJP 販売 Top 10 — {now}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, 'Helvetica Neue', 'Segoe UI', sans-serif; background: #f5f6fa; color: #2d3436; }}
  .container {{ max-width: 1080px; margin: 0 auto; padding: 24px 16px; }}
  header {{ margin-bottom: 24px; }}
  header h1 {{ font-size: 22px; font-weight: 700; }}
  header .time {{ color: #636e72; font-size: 13px; margin-top: 4px; }}
  .stats {{ display: flex; gap: 16px; margin-bottom: 24px; flex-wrap: wrap; }}
  .stat-card {{ background: #fff; border-radius: 12px; padding: 16px 20px; flex: 1; min-width: 140px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }}
  .stat-card .label {{ font-size: 12px; color: #636e72; margin-bottom: 4px; }}
  .stat-card .value {{ font-size: 26px; font-weight: 700; color: #0984e3; }}
  .tabs {{ display: flex; gap: 6px; margin-bottom: 16px; flex-wrap: wrap; }}
  .tab-btn {{ padding: 8px 18px; border: none; border-radius: 8px; background: #dfe6e9; cursor: pointer; font-size: 14px; font-weight: 500; transition: all .2s; }}
  .tab-btn.active {{ background: #0984e3; color: #fff; }}
  .tab-btn:hover {{ background: #74b9ff; color: #fff; }}
  .tab-content {{ display: none; }}
  .tab-content.active {{ display: block; }}
  table {{ width: 100%; background: #fff; border-radius: 12px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.06); border-collapse: collapse; }}
  thead {{ background: #f8f9fa; }}
  th {{ padding: 12px 14px; text-align: left; font-size: 12px; color: #636e72; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }}
  td {{ padding: 14px; border-top: 1px solid #f1f2f6; font-size: 14px; }}
  tr:hover {{ background: #f8f9fa; }}
  .rank {{ font-size: 18px; text-align: center; }}
  .product-name {{ font-weight: 600; }}
  .product-cat {{ font-size: 12px; color: #636e72; margin-top: 2px; }}
  .num {{ text-align: right; font-variant-numeric: tabular-nums; }}
  .highlight {{ font-weight: 700; color: #0984e3; font-size: 16px; }}
  th.num {{ text-align: right; }}
  .trend {{ display: flex; align-items: flex-end; gap: 3px; height: 40px; }}
  .bar-wrap {{ display: flex; flex-direction: column; align-items: center; height: 100%; justify-content: flex-end; }}
  .bar {{ width: 14px; background: linear-gradient(180deg, #0984e3, #74b9ff); border-radius: 3px 3px 0 0; min-height: 2px; transition: height .3s; }}
  .bar-label {{ font-size: 8px; color: #b2bec3; margin-top: 2px; }}
  footer {{ text-align: center; margin-top: 32px; font-size: 12px; color: #b2bec3; }}
</style>
</head>
<body>
<div class="container">
  <header>
    <h1>VIVAIA Japan — 販売 Top 10</h1>
    <div class="time">更新: {now}　｜　データソース: Metabase MD_VJP过去销量</div>
  </header>
  <div class="stats">
    <div class="stat-card"><div class="label">昨日販売数</div><div class="value">{int(total_l1)}</div></div>
    <div class="stat-card"><div class="label">過去 7 日</div><div class="value">{int(total_l7)}</div></div>
    <div class="stat-card"><div class="label">過去 30 日</div><div class="value">{int(total_l30)}</div></div>
    <div class="stat-card"><div class="label">販売中 SPU 数</div><div class="value">{active_spu}</div></div>
  </div>
  <div class="tabs">
    {tab_buttons}
  </div>
  {tab_contents}
</div>
<footer>Auto-generated daily from Metabase</footer>
<script>
document.querySelectorAll('.tab-btn').forEach(btn => {{
  btn.addEventListener('click', () => {{
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById(btn.dataset.tab).classList.add('active');
  }});
}});
</script>
</body>
</html>"""


if __name__ == "__main__":
    print("Fetching data from Metabase...")
    raw = fetch_data()
    print(f"Rows: {len(raw['data']['rows'])}")
    spu_map = aggregate(raw)
    print(f"SPUs: {len(spu_map)}")
    html = build_html(spu_map)
    OUTPUT.write_text(html, encoding="utf-8")
    print(f"Dashboard saved to {OUTPUT}")
