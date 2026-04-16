#!/usr/bin/env python3
"""
Generate static HTML shell for VIVAIA Dashboard.
All data is fetched client-side in real-time via Cloudflare Worker proxy.
No server-side data fetching needed.
"""
from pathlib import Path
from datetime import datetime, timezone, timedelta

DIR = Path(__file__).parent
OUTPUT = DIR / "index.html"
WORKER = "https://vivaia-api-proxy.vivaia-dash.workers.dev"

def build():
    jst = timezone(timedelta(hours=9))
    now = datetime.now(jst).strftime("%Y-%m-%d %H:%M")

    html = f"""<!DOCTYPE html>
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
.stats {{ display:grid; grid-template-columns:repeat(4,1fr); gap:8px; margin-bottom:16px; }}
.stat-card {{ background:#fff; border-radius:10px; padding:10px 12px; box-shadow:0 1px 3px rgba(0,0,0,.06); }}
.stat-card .label {{ font-size:10px; color:#636e72; }}
.stat-card .value {{ font-size:20px; font-weight:700; color:#0984e3; }}
.tabs {{ display:flex; gap:5px; margin-bottom:12px; }}
.tab-btn {{ padding:6px 12px; border:none; border-radius:7px; background:#dfe6e9; cursor:pointer; font-size:12px; font-weight:500; transition:all .2s; white-space:nowrap; }}
.tab-btn.active {{ background:#0984e3; color:#fff; }}
.tab-content {{ display:none; }}
.tab-content.active {{ display:block; }}
.table-wrap {{ overflow-x:auto; border-radius:10px; box-shadow:0 1px 3px rgba(0,0,0,.06); max-height:calc(100vh - 200px); overflow-y:auto; }}
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
.rk-summary {{ display:flex; align-items:center; gap:20px; background:#fff; border-radius:10px; padding:14px 18px; margin-bottom:14px; box-shadow:0 1px 3px rgba(0,0,0,.06); }}
.rk-total-num {{ font-size:28px; font-weight:700; color:#0984e3; }}
.rk-total-label {{ font-size:11px; color:#636e72; margin-left:6px; }}
.rk-comp {{ display:flex; align-items:center; gap:6px; }}
.rk-comp-label {{ font-size:10px; color:#636e72; font-weight:600; }}
.pct-up {{ color:#00b894; font-weight:600; font-size:13px; }}
.pct-down {{ color:#e74c3c; font-weight:600; font-size:13px; }}
.pct-na {{ color:#b2bec3; font-size:12px; }}
/* Search & filters */
.search-bar {{ margin-bottom:10px; }}
.search-bar input {{ width:100%; padding:10px 12px; border:1px solid #dfe6e9; border-radius:8px; font-size:14px; background:#fff; }}
.search-bar input:focus {{ outline:none; border-color:#0984e3; box-shadow:0 0 0 2px rgba(9,132,227,.15); }}
.filter-bar {{ display:flex; gap:8px; margin-bottom:14px; flex-wrap:wrap; align-items:flex-end; }}
.filter-row {{ display:flex; gap:8px; margin-bottom:8px; align-items:flex-end; }}
.filter-row .filter-group {{ flex:1; }}
.filter-group {{ flex:1; min-width:130px; }}
.filter-group label {{ display:block; font-size:10px; color:#636e72; margin-bottom:3px; font-weight:600; }}
.filter-group select, .filter-group input {{ width:100%; padding:7px 8px; border:1px solid #dfe6e9; border-radius:7px; font-size:12px; background:#fff; }}
.inv-count {{ font-size:11px; color:#636e72; margin-bottom:10px; }}
.inv-table td.stock {{ text-align:center; font-variant-numeric:tabular-nums; width:42px; min-width:42px; max-width:42px; padding:6px 2px; }}
.inv-table td.stock.has-stock {{ font-weight:600; color:#2d3436; }}
.inv-table th.stock {{ text-align:center; font-size:9px; padding:6px 2px; width:42px; min-width:42px; max-width:42px; }}
.inv-table td.stock:nth-last-child(2) {{ background:#f4f6f7; font-weight:700; border-left:2px solid #ddd; }}
.inv-table th:nth-last-child(2) {{ background:#edf0f2; border-left:2px solid #ddd; }}
.inv-table td.stock:last-child {{ border-left:2px solid #ddd; }}
.inv-table th:last-child {{ border-left:2px solid #ddd; }}
.inv-table td.stock.zero {{ color:#ccc; }}
.inv-table tbody tr:nth-child(odd) {{ background:#fafbfc; }}
.inv-table thead {{ position:sticky; top:0; z-index:10; background:#f8f9fa; box-shadow:0 1px 2px rgba(0,0,0,.1); }}
.inv-img {{ width:32px; height:32px; border-radius:4px; object-fit:cover; background:#f1f2f6; flex-shrink:0; }}
.inv-table td.color-col {{ font-size:11px; white-space:nowrap; width:1%; padding-right:4px; }}
.inv-table td.size-col {{ font-size:11px; text-align:center; white-space:nowrap; width:1%; padding-right:4px; }}
.inv-table td.name-col {{ font-size:12px; font-weight:600; white-space:nowrap; width:1%; padding-right:4px; }}
.inv-table td.img-col {{ width:32px; padding:4px; }}
.clear-btn {{ padding:7px 14px; border:1px solid #dfe6e9; border-radius:7px; background:#fff; font-size:12px; cursor:pointer; color:#636e72; white-space:nowrap; transition:all .2s; }}
.clear-btn:hover {{ background:#e74c3c; color:#fff; border-color:#e74c3c; }}
.mobile-product {{ display:none; }}
.mobile-img {{ display:none; }}
.desktop-only {{ }}
.d-short {{ display:none; }}
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
.sa-card-primary {{ background:#0984e3 !important; }}
.sa-card-primary .sa-label {{ color:rgba(255,255,255,.7); }}
.sa-card-primary .sa-value {{ color:#fff; font-size:26px; }}
.sa-card-primary .sa-up,.sa-card-primary .sa-down,.sa-card-primary .sa-compare-val {{ color:rgba(255,255,255,.85); }}
.sa-card .sa-sub {{ font-size:11px; margin-top:4px; }}
.sa-card .sa-up {{ color:#00b894; }}
.sa-card .sa-down {{ color:#e74c3c; }}
.sa-card .sa-compare-val {{ font-size:13px; color:#636e72; }}
.sa-quick {{ display:flex; gap:5px; margin-bottom:10px; flex-wrap:wrap; }}
.sa-quick-btn {{ padding:5px 8px; border:1px solid #dfe6e9; border-radius:6px; background:#fff; font-size:11px; cursor:pointer; transition:all .2s; }}
.sa-quick-btn.active {{ background:#0984e3; color:#fff; border-color:#0984e3; }}
.sa-quick-btn:hover {{ border-color:#0984e3; }}
.sa-to2-auto {{ font-size:11px; color:#636e72; }}
.sa-chart-wrap {{ background:#fff; border-radius:10px; padding:16px; box-shadow:0 1px 3px rgba(0,0,0,.06); }}
/* Loading indicator */
.loading {{ text-align:center; padding:40px; color:#636e72; font-size:13px; }}
.loading::after {{ content:''; display:inline-block; width:16px; height:16px; border:2px solid #dfe6e9; border-top-color:#0984e3; border-radius:50%; animation:spin .6s linear infinite; margin-left:8px; vertical-align:middle; }}
@keyframes spin {{ to {{ transform:rotate(360deg); }} }}
/* Mobile */
@media (max-width:768px) {{
  .sidebar {{ position:fixed; bottom:0; top:auto; left:0; width:100%; height:auto; display:flex; padding:0; z-index:100; }}
  .sidebar .logo {{ display:none; }}
  .sidebar a {{ flex:1; text-align:center; padding:10px 4px; font-size:11px; border-top:1px solid #636e72; }}
  .main {{ margin-left:0; margin-bottom:50px; padding:14px 10px; max-width:100vw; }}
  .hide-mobile {{ display:none; }}
  .stats {{ grid-template-columns:repeat(2,1fr); }}
  .sa-cards {{ grid-template-columns:repeat(2,1fr); }}
  .sa-date-row {{ flex-direction:column; align-items:stretch; }}
  .sa-card .sa-value {{ font-size:18px; }}
  .store-btn {{ font-size:10px; padding:7px 2px; white-space:nowrap; }}
  .filter-bar {{ flex-direction:column; }}
  .inv-table-wrap {{ overflow-x:hidden; }}
  .rk-table-wrap {{ overflow-x:hidden; }}
  .rk-table th {{ font-size:9px; padding:6px 3px; }}
  .rk-table td {{ padding:6px 3px; font-size:11px; }}
  .rk-table .rank {{ font-size:13px; }}
  .rk-table .product-img {{ width:32px; height:32px; }}
  .rk-table .product-cell {{ gap:5px; }}
  .rk-table .product-name {{ font-size:11px; }}
  .rk-table .product-color {{ font-size:9px; }}
  .rk-table .highlight {{ font-size:12px; }}
  .rk-table .num {{ font-size:10px; }}
  .filter-group {{ min-width:100%; }}
  .inv-table .desktop-only {{ display:none; }}
  .inv-table .mobile-product {{ display:table-cell; padding:5px 2px; vertical-align:middle; }}
  .inv-table .mobile-img {{ display:table-cell; padding:3px 1px; width:30px; vertical-align:middle; }}
  .inv-table .mobile-img .inv-img {{ width:30px; height:30px; }}
  .inv-table th.stock {{ padding:3px 1px; font-size:8px; }}
  .inv-table td.stock {{ padding:4px 1px; font-size:11px; }}
  .inv-table td.img-col {{ padding:3px; }}
  .d-full {{ display:none; }}
  .d-short {{ display:inline; }}
  .inv-table tbody tr:nth-child(even) {{ background:#fafbfc; }}
  .inv-table td.stock:first-of-type {{ border-left:2px solid #e9ecef; }}
  .m-name {{ font-weight:600; font-size:12px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:80px; }}
  .m-detail {{ font-size:9px; color:#999; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:80px; margin-top:1px; }}
  .m-size {{ font-size:10px; color:#0984e3; margin-top:1px; }}
  .product-img {{ width:36px; height:36px; }}
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
  <!-- Sales Analysis -->
  <div id="page-analysis" class="page active">
    <header><h1>売上分析</h1><div class="time" id="sa-time">読み込み中...</div></header>
    <div class="store-nav sa-store-nav">
      <button class="store-btn active" data-sa-store="全体">VJP全体</button>
      <button class="store-btn" data-sa-store="EC">EC</button>
      <button class="store-btn" data-sa-store="店舗合計">店舗計</button>
      <button class="store-btn" data-sa-store="ハラカド店">ハラカド</button>
      <button class="store-btn" data-sa-store="新宿店">新宿</button>
      <button class="store-btn" data-sa-store="大阪店">大阪</button>
      <button class="store-btn" data-sa-store="二子玉川店">二子玉川</button>
    </div>
    <div class="sa-controls">
      <div class="sa-quick">
        <button class="sa-quick-btn active" data-range="today">今日</button>
        <button class="sa-quick-btn" data-range="yesterday">昨日</button>
        <button class="sa-quick-btn" data-range="last3">過去3日</button>
        <button class="sa-quick-btn" data-range="last7">過去7日</button>
        <button class="sa-quick-btn" data-range="last15">過去15日</button>
        <button class="sa-quick-btn" data-range="last30">過去30日</button>
      </div>
      <div class="sa-quick">
        <button class="sa-quick-btn" data-range="thisweek">今週</button>
        <button class="sa-quick-btn" data-range="lastweek">先週</button>
        <button class="sa-quick-btn" data-range="thismonth">今月</button>
        <button class="sa-quick-btn" data-range="lastmonth">先月</button>
        <button class="sa-quick-btn" data-range="thisyear">今年</button>
        <button class="sa-quick-btn" data-range="lastyear">去年</button>
      </div>
      <div class="sa-date-row">
        <div class="sa-date-group"><label>期間</label><input type="date" id="sa-from"> ～ <input type="date" id="sa-to"></div>
        <label class="sa-compare-toggle"><input type="checkbox" id="sa-compare-check"> 比較</label>
        <div class="sa-date-group" id="sa-compare-group" style="display:none"><label>比較開始日</label><input type="date" id="sa-from2"> <span id="sa-to2-label" class="sa-to2-auto"></span></div>
      </div>
    </div>
    <div class="sa-cards" id="sa-cards"><div class="loading">データ読み込み中</div></div>
    <div class="sa-chart-wrap"><canvas id="sa-chart" height="280"></canvas></div>
  </div>
  <!-- Ranking -->
  <div id="page-ranking" class="page">
    <header><h1>商品ランキング</h1><div class="time" id="rk-time">読み込み中...</div></header>
    <div class="store-nav rk-store-nav">
      <button class="store-btn active" data-rk-store="all">VJP全体</button>
      <button class="store-btn" data-rk-store="ec">EC</button>
      <button class="store-btn" data-rk-store="offline">店舗計</button>
      <button class="store-btn" data-rk-store="1">ハラカド</button>
      <button class="store-btn" data-rk-store="2">新宿</button>
      <button class="store-btn" data-rk-store="3">大阪</button>
      <button class="store-btn" data-rk-store="13">二子玉川</button>
    </div>
    <div class="sa-quick rk-quick">
      <button class="sa-quick-btn active" data-rk-range="today">今日</button>
      <button class="sa-quick-btn" data-rk-range="yesterday">昨日</button>
      <button class="sa-quick-btn" data-rk-range="last3">過去3日</button>
      <button class="sa-quick-btn" data-rk-range="last7">過去7日</button>
      <button class="sa-quick-btn" data-rk-range="last15">過去15日</button>
      <button class="sa-quick-btn" data-rk-range="last30">過去30日</button>
    </div>
    <div class="sa-quick rk-quick">
      <button class="sa-quick-btn" data-rk-range="thisweek">今週</button>
      <button class="sa-quick-btn" data-rk-range="lastweek">先週</button>
      <button class="sa-quick-btn" data-rk-range="thismonth">今月</button>
      <button class="sa-quick-btn" data-rk-range="lastmonth">先月</button>
      <button class="sa-quick-btn" data-rk-range="thisyear">今年</button>
      <button class="sa-quick-btn" data-rk-range="lastyear">去年</button>
    </div>
    <div class="sa-date-row" style="margin-bottom:14px"><div class="sa-date-group"><label>期間</label><input type="date" id="rk-from"> ～ <input type="date" id="rk-to"></div></div>
    <div class="search-bar" style="margin-bottom:10px"><input id="rk-search" type="text" placeholder="商品名で検索..." oninput="onRkSearch()"></div>
    <div class="rk-summary" id="rk-summary"><div class="loading">データ読み込み中</div></div>
    <div class="table-wrap rk-table-wrap"><table class="rk-table"><thead><tr><th width="30">#</th><th>商品</th><th class="num">数量</th><th class="num" id="rk-comp-header">前期比</th><th class="num" id="rk-yoy-header">前年比</th></tr></thead><tbody id="rk-body"></tbody></table></div>
  </div>
  <!-- Inventory -->
  <div id="page-inventory" class="page">
    <header><h1>在庫確認</h1><div class="time" id="inv-time">読み込み中...</div></header>
    <div class="search-bar" style="display:flex;gap:8px;"><input id="f-search" type="text" placeholder="商品名・カラー・UPCで検索..." style="flex:1;"><button id="inv-search-btn" style="padding:10px 18px;border:none;border-radius:8px;background:#0984e3;color:#fff;font-size:13px;font-weight:600;cursor:pointer;white-space:nowrap;">検索</button></div>
    <input id="f-upc" type="hidden" value="">
    <div class="filter-row"><div class="filter-group"><label>カテゴリ</label><select id="f-cat"><option value="">すべて</option></select></div><div class="filter-group"><label>商品名</label><select id="f-name"><option value="">すべて</option></select></div></div>
    <div class="filter-row"><div class="filter-group"><label>カラー</label><select id="f-color"><option value="">すべて</option></select></div><div class="filter-group"><label>サイズ</label><select id="f-size"><option value="">すべて</option></select></div><button class="clear-btn" id="clear-filters">クリア</button></div>
    <div class="inv-count" id="inv-count"><div class="loading">データ読み込み中</div></div>
    <div class="table-wrap inv-table-wrap"><table class="inv-table"><thead><tr>
      <th class="desktop-only">画像</th><th class="desktop-only">商品名</th><th class="desktop-only">カラー</th><th class="desktop-only" style="text-align:center">サイズ</th><th class="mobile-img">画像</th><th class="mobile-product">商品</th>
      <th class="stock"><span class="d-full">ハラカド</span><span class="d-short">原宿</span></th><th class="stock">新宿</th><th class="stock">大阪</th><th class="stock"><span class="d-full">二子玉川</span><span class="d-short">二子</span></th><th class="stock"><span class="d-full">店舗合計</span><span class="d-short">合計</span></th><th class="stock">EC</th>
    </tr></thead><tbody id="inv-body"></tbody></table></div>
  </div>
</div>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>
<script>
const W = '{WORKER}';

// ── Login ──
const PW_HASH = 'a49aff1951a384d5fa0f4860ab58c383052caf6e3ce7b6caa998e38ec3afc5db';
async function sha256(msg) {{ const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(msg)); return [...new Uint8Array(buf)].map(b => b.toString(16).padStart(2,'0')).join(''); }}
function unlockApp() {{ document.getElementById('login-overlay').style.display='none'; document.querySelector('.sidebar').style.display=''; document.querySelector('.main').style.display=''; loadSalesAnalysis(); }}
if (localStorage.getItem('vj_auth') === PW_HASH) {{ unlockApp(); }}
document.getElementById('login-btn').addEventListener('click', async () => {{ const h = await sha256(document.getElementById('login-pw').value); if (h === PW_HASH) {{ localStorage.setItem('vj_auth', PW_HASH); unlockApp(); }} else {{ document.getElementById('login-err').style.display='block'; }} }});
document.getElementById('login-pw').addEventListener('keydown', e => {{ if (e.key === 'Enter') document.getElementById('login-btn').click(); }});

// ── Helpers ──
async function mbQuery(cardId, format='json') {{
  const url = W + '/api/card/' + cardId + '/query' + (format === 'csv' ? '/csv' : '');
  const resp = await fetch(url, {{ method: 'POST', headers: {{'Content-Type': 'application/json'}}, body: '{{}}' }});
  if (format === 'csv') return resp.text();
  return resp.json();
}}
async function mbSQL(sql) {{
  const resp = await fetch(W + '/api/dataset', {{ method: 'POST', headers: {{'Content-Type': 'application/json'}}, body: JSON.stringify({{ database: 2, type: 'native', native: {{ query: sql }} }}) }});
  return resp.json();
}}
function parseCSV(text) {{
  const lines = text.trim().split('\\n');
  const headers = lines[0].split(',').map(h => h.replace(/"/g,''));
  return lines.slice(1).map(line => {{
    const vals = []; let cur = ''; let inQ = false;
    for (const c of line) {{
      if (c === '"') {{ inQ = !inQ; }} else if (c === ',' && !inQ) {{ vals.push(cur); cur = ''; }} else {{ cur += c; }}
    }}
    vals.push(cur);
    return vals;
  }});
}}
function addDays(ds, n) {{ const d = new Date(ds); d.setDate(d.getDate()+n); return d.toISOString().slice(0,10); }}
function diffDays(a, b) {{ return Math.round((new Date(b)-new Date(a))/86400000); }}
function quickRange(key) {{
  const t = new Date(); const fmt = d => d.toISOString().slice(0,10);
  const mon = d => {{ const r=new Date(d); r.setDate(r.getDate()-(r.getDay()||7)+1); return r; }};
  switch(key) {{
    case 'today': return [fmt(t),fmt(t)];
    case 'yesterday': {{ const y=new Date(t); y.setDate(y.getDate()-1); return [fmt(y),fmt(y)]; }}
    case 'last3': {{ const d=new Date(t); d.setDate(d.getDate()-2); return [fmt(d),fmt(t)]; }}
    case 'last7': {{ const d=new Date(t); d.setDate(d.getDate()-6); return [fmt(d),fmt(t)]; }}
    case 'last15': {{ const d=new Date(t); d.setDate(d.getDate()-14); return [fmt(d),fmt(t)]; }}
    case 'last30': {{ const d=new Date(t); d.setDate(d.getDate()-29); return [fmt(d),fmt(t)]; }}
    case 'thisweek': return [fmt(mon(t)),fmt(t)];
    case 'lastweek': {{ const m=mon(t); m.setDate(m.getDate()-7); const e=new Date(m); e.setDate(e.getDate()+6); return [fmt(m),fmt(e)]; }}
    case 'thismonth': return [fmt(t).slice(0,8)+'01',fmt(t)];
    case 'lastmonth': {{ const f=new Date(t.getFullYear(),t.getMonth()-1,1); const l=new Date(t.getFullYear(),t.getMonth(),0); return [fmt(f),fmt(l)]; }}
    case 'thisyear': return [t.getFullYear()+'-01-01',fmt(t)];
    case 'lastyear': return [(t.getFullYear()-1)+'-01-01',(t.getFullYear()-1)+'-12-31'];
  }}
}}
function pctHtml(cur, prev) {{
  if (!prev) return '<span class="pct-na">-</span>';
  const p = ((cur-prev)/prev*100).toFixed(1);
  return p >= 0 ? '<span class="pct-up">↑'+p+'%</span>' : '<span class="pct-down">↓'+Math.abs(p).toFixed(1)+'%</span>';
}}
function nowJST() {{ return new Date(Date.now()+9*3600000).toISOString().slice(0,16).replace('T',' '); }}

// ── Page navigation ──
let pageLoaded = {{ analysis: false, ranking: false, inventory: false }};
document.querySelectorAll('.sidebar a').forEach(a => {{
  a.addEventListener('click', e => {{
    e.preventDefault();
    document.querySelectorAll('.sidebar a').forEach(x => x.classList.remove('active'));
    document.querySelectorAll('.page').forEach(x => x.classList.remove('active'));
    a.classList.add('active');
    document.getElementById('page-' + a.dataset.page).classList.add('active');
    if (a.dataset.page === 'ranking' && !pageLoaded.ranking) loadRanking();
    if (a.dataset.page === 'inventory' && !pageLoaded.inventory) loadInventory();
  }});
}});

// ══════════════════════════════════════════
// SALES ANALYSIS
// ══════════════════════════════════════════
let SA_DATA = null, saChart = null, saStore = '全体';

async function loadSalesAnalysis() {{
  document.getElementById('sa-time').textContent = '読み込み中...';
  const [offResp, ecCSV, todayResp] = await Promise.all([
    mbSQL("SELECT report_date, store_scope, sales_amount, sales_qty, customers_count, avg_transaction_value FROM daily_sales_reports ORDER BY report_date, store_scope"),
    mbQuery(136, 'csv'),
    mbQuery(133, 'json')
  ]);
  const scopeMap = {{'1':'ハラカド店','2':'新宿店','3':'大阪店','13':'二子玉川店','all':'店舗合計'}};
  const todayStoreMap = {{'グラングリーン大阪店':'大阪店','ハラカド店':'ハラカド店','二子玉川店':'二子玉川店','新宿マルイ本館店':'新宿店'}};
  SA_DATA = [];
  const offByDate = {{}};
  for (const r of offResp.data.rows) {{
    const date = r[0].slice(0,10), store = scopeMap[String(r[1])] || String(r[1]);
    const sales = Math.round(r[2]||0), qty = r[3]||0, cust = r[4]||0, atv = Math.round(r[5]||0);
    SA_DATA.push({{ date, store, sales, qty, customers: cust, atv }});
    if (store === '店舗合計') offByDate[date] = {{ sales, qty, customers: cust }};
  }}
  // Add today's real-time data from card 133
  const todayStr = new Date(Date.now()+9*3600000).toISOString().slice(0,10);
  let todayOffTotal = {{ sales:0, qty:0, customers:0 }};
  for (const r of todayResp.data.rows) {{
    const storeName = todayStoreMap[r[0]];
    if (!storeName) continue;
    const sales = Math.round(r[1]||0), qty = r[2]||0, atv = Math.round(r[3]||0);
    const cust = atv > 0 ? Math.round(sales / atv) : 0;
    SA_DATA.push({{ date: todayStr, store: storeName, sales, qty, customers: cust, atv }});
    todayOffTotal.sales += sales;
    todayOffTotal.qty += qty;
    todayOffTotal.customers += cust;
  }}
  if (todayOffTotal.sales > 0) {{
    SA_DATA.push({{ date: todayStr, store: '店舗合計', sales: todayOffTotal.sales, qty: todayOffTotal.qty, customers: todayOffTotal.customers, atv: todayOffTotal.customers ? Math.round(todayOffTotal.sales/todayOffTotal.customers) : 0 }});
    offByDate[todayStr] = todayOffTotal;
  }}
  // EC daily
  for (const row of parseCSV(ecCSV)) {{
    const date = row[0].slice(0,10), sales = Math.round(parseFloat(row[1])||0), qty = parseInt(row[2])||0, cust = parseInt(row[3])||0;
    SA_DATA.push({{ date, store: 'EC', sales, qty, customers: cust, atv: cust ? Math.round(sales/cust) : 0 }});
    const off = offByDate[date] || {{ sales:0, qty:0, customers:0 }};
    const ts = off.sales+sales, tq = off.qty+qty, tc = off.customers+cust;
    SA_DATA.push({{ date, store: '全体', sales: ts, qty: tq, customers: tc, atv: tc ? Math.round(ts/tc) : 0 }});
  }}
  document.getElementById('sa-time').textContent = '更新: ' + nowJST() + '（リアルタイム）';
  pageLoaded.analysis = true;
  initSAControls();
  renderSA();
}}

function initSAControls() {{
  const [f,t] = quickRange('today');
  document.getElementById('sa-from').value = f;
  document.getElementById('sa-to').value = t;
  document.getElementById('sa-from2').value = addDays(f, -(diffDays(f,t)+1));
  document.querySelectorAll('.sa-store-nav .store-btn').forEach(btn => btn.addEventListener('click', () => {{
    document.querySelectorAll('.sa-store-nav .store-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active'); saStore = btn.dataset.saStore; renderSA();
  }}));
  document.querySelectorAll('.sa-controls .sa-quick-btn').forEach(btn => btn.addEventListener('click', () => {{
    document.querySelectorAll('.sa-controls .sa-quick-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    const [f,t] = quickRange(btn.dataset.range);
    document.getElementById('sa-from').value = f; document.getElementById('sa-to').value = t;
    document.getElementById('sa-from2').value = addDays(f, -(diffDays(f,t)+1));
    updateSACompareTo(); renderSA();
  }}));
  ['sa-from','sa-to'].forEach(id => document.getElementById(id).addEventListener('change', () => {{ updateSACompareTo(); renderSA(); }}));
  document.getElementById('sa-from2').addEventListener('change', () => {{ updateSACompareTo(); renderSA(); }});
  document.getElementById('sa-compare-check').addEventListener('change', e => {{
    document.getElementById('sa-compare-group').style.display = e.target.checked ? 'flex' : 'none';
    updateSACompareTo(); renderSA();
  }});
}}
function updateSACompareTo() {{
  const f1=document.getElementById('sa-from').value, t1=document.getElementById('sa-to').value, f2=document.getElementById('sa-from2').value;
  if (f1&&t1&&f2) document.getElementById('sa-to2-label').textContent = '～ ' + addDays(f2, diffDays(f1,t1));
}}
function renderSA() {{
  if (!SA_DATA) return;
  const f1=document.getElementById('sa-from').value, t1=document.getElementById('sa-to').value;
  const comparing=document.getElementById('sa-compare-check').checked;
  const f2=document.getElementById('sa-from2').value, days=diffDays(f1,t1), t2=addDays(f2,days);
  const a = SA_DATA.filter(d => d.store===saStore && d.date>=f1 && d.date<=t1).sort((a,b)=>a.date.localeCompare(b.date));
  const sum = arr => ({{ sales:arr.reduce((s,d)=>s+d.sales,0), qty:arr.reduce((s,d)=>s+d.qty,0), customers:arr.reduce((s,d)=>s+d.customers,0), atv: arr.length ? Math.round(arr.reduce((s,d)=>s+d.sales,0)/Math.max(arr.reduce((s,d)=>s+d.customers,0),1)) : 0 }});
  const sumA = sum(a);
  let sumB=null, b=[];
  if (comparing&&f2) {{ b=SA_DATA.filter(d=>d.store===saStore&&d.date>=f2&&d.date<=t2).sort((a,b)=>a.date.localeCompare(b.date)); sumB=sum(b); }}
  const fmtYen=n=>'¥'+Math.round(n).toLocaleString(), fmtNum=n=>Math.round(n).toLocaleString();
  const pct=(c,p)=>{{ if(!p)return''; const v=((c-p)/p*100).toFixed(1); return '<div class="sa-sub '+(v>=0?'sa-up':'sa-down')+'">'+(v>=0?'+':'')+v+'%</div>'; }};
  const metrics=[{{l:'売上',a:sumA.sales,b:sumB?sumB.sales:0,f:fmtYen}},{{l:'取引数',a:sumA.qty,b:sumB?sumB.qty:0,f:fmtNum}},{{l:'客数',a:sumA.customers,b:sumB?sumB.customers:0,f:fmtNum}},{{l:'客単価',a:sumA.atv,b:sumB?sumB.atv:0,f:fmtYen}}];
  document.getElementById('sa-cards').innerHTML = metrics.map((m,i) => '<div class="sa-card'+(i===0?' sa-card-primary':'')+'"><div class="sa-label">'+m.l+'</div><div class="sa-value">'+m.f(m.a)+'</div>'+(comparing&&sumB?pct(m.a,m.b)+'<div class="sa-sub sa-compare-val">比較: '+m.f(m.b)+'</div>':'')+'</div>').join('');
  // Chart - for single day, show +/- 2 days context with selected day highlighted red
  const ctx=document.getElementById('sa-chart').getContext('2d');
  if(saChart)saChart.destroy();
  let chartData, chartLabels, pointColors, pointRadii;
  if (days === 0) {{
    // Single day: show 5 days (2 before, selected, 2 after)
    const d0 = addDays(f1, -2), d4 = addDays(f1, 2);
    const nearby = SA_DATA.filter(d => d.store===saStore && d.date>=d0 && d.date<=d4).sort((a,b)=>a.date.localeCompare(b.date));
    chartData = nearby.map(d => d.sales);
    chartLabels = nearby.map(d => d.date.slice(5));
    pointColors = nearby.map(d => d.date === f1 ? '#e74c3c' : '#0984e3');
    pointRadii = nearby.map(d => d.date === f1 ? 7 : 3);
  }} else {{
    chartData = a.map(d => d.sales);
    chartLabels = a.map(d => d.date.slice(5));
    pointColors = '#0984e3';
    pointRadii = a.length > 31 ? 0 : 3;
  }}
  const ds=[{{label:f1+'～'+t1,data:chartData,borderColor:'#0984e3',backgroundColor:'rgba(9,132,227,.08)',fill:true,tension:.3,pointBackgroundColor:pointColors,pointRadius:pointRadii,borderWidth:2}}];
  if(comparing&&b.length) ds.push({{label:f2+'～'+t2,data:b.map(d=>d.sales),borderColor:'#636e72',backgroundColor:'rgba(99,110,114,.05)',fill:true,tension:.3,borderDash:[6,3],pointRadius:b.length>31?0:3,borderWidth:2}});
  saChart=new Chart(ctx,{{type:'line',data:{{labels:chartLabels,datasets:ds}},options:{{responsive:true,maintainAspectRatio:false,interaction:{{mode:'index',intersect:false}},plugins:{{legend:{{display:comparing}},tooltip:{{callbacks:{{label:i=>i.dataset.label+': ¥'+i.raw.toLocaleString()}}}}}},scales:{{y:{{beginAtZero:true,ticks:{{callback:v=>v>=10000?(v/10000).toFixed(0)+'万':v}}}}}}}}}});
}}

// ══════════════════════════════════════════
// RANKING
// ══════════════════════════════════════════
let RK_RAW=null, RK_INFO=null, rkStore='all';
// rkPeriodLabel is now always computed dynamically with dates

async function loadRanking() {{
  document.getElementById('rk-time').textContent = '読み込み中...';
  const [offCSV, ecCSV, infoCSV] = await Promise.all([
    mbQuery(134, 'csv'), mbQuery(135, 'csv'), mbQuery(90, 'csv')
  ]);
  // Parse offline + EC ranking data
  const dd = {{}};
  for (const r of parseCSV(offCSV)) {{
    const k = r[0]+'|'+r[1].slice(0,10)+'|'+r[2];
    dd[k] = (dd[k]||0) + (parseInt(r[3])||0);
  }}
  for (const r of parseCSV(ecCSV)) {{
    if (!r[2]) continue;
    const k = r[0]+'|'+r[1].slice(0,10)+'|'+r[2];
    dd[k] = (dd[k]||0) + (parseInt(r[3])||0);
  }}
  // Build "all" totals
  const allT = {{}};
  for (const [k, q] of Object.entries(dd)) {{
    const [s,d,spu] = k.split('|');
    const ak = 'all|'+d+'|'+spu;
    allT[ak] = (allT[ak]||0) + q;
  }}
  Object.assign(dd, allT);
  RK_RAW = dd;
  // SPU info from card 90 CSV (全量)
  RK_INFO = {{}};
  for (const r of parseCSV(infoCSV)) {{
    // CSV columns: 画像,SPU,SKU,UPC,カテゴリ,商品名,カラー,サイズ,...
    const spu = r[1];
    if (!RK_INFO[spu]) RK_INFO[spu] = {{ name: r[5]||'', color: r[6]||'', img: r[0]||'' }};
  }}
  document.getElementById('rk-time').textContent = '更新: ' + nowJST() + '（リアルタイム）';
  pageLoaded.ranking = true;
  initRKControls();
  renderRanking();
}}

function rkAggregate(store, from, to) {{
  const map = {{}};
  const offlineStores = ['1','2','3','13'];
  for (const [k, q] of Object.entries(RK_RAW)) {{
    const [s,d,spu] = k.split('|');
    if (d>=from && d<=to) {{
      if (store === 'offline' ? offlineStores.includes(s) : s===store) {{
        map[spu] = (map[spu]||0) + q;
      }}
    }}
  }}
  return map;
}}

function initRKControls() {{
  const [f,t] = quickRange('today');
  document.getElementById('rk-from').value = f; document.getElementById('rk-to').value = t;
  document.querySelectorAll('.rk-store-nav .store-btn').forEach(btn => btn.addEventListener('click', () => {{
    document.querySelectorAll('.rk-store-nav .store-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active'); rkStore=btn.dataset.rkStore; renderRanking();
  }}));
  document.querySelectorAll('.rk-quick .sa-quick-btn').forEach(btn => btn.addEventListener('click', () => {{
    document.querySelectorAll('.rk-quick .sa-quick-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    const [f,t]=quickRange(btn.dataset.rkRange);
    document.getElementById('rk-from').value=f; document.getElementById('rk-to').value=t; renderRanking();
  }}));
  ['rk-from','rk-to'].forEach(id => document.getElementById(id).addEventListener('change', () => {{
    document.querySelectorAll('.rk-quick .sa-quick-btn').forEach(b => b.classList.remove('active')); renderRanking();
  }}));
}}

function renderRanking() {{
  if (!RK_RAW) return;
  const f1=document.getElementById('rk-from').value, t1=document.getElementById('rk-to').value;
  if (!f1||!t1) return;
  const days=diffDays(f1,t1);
  const cur=rkAggregate(rkStore,f1,t1);
  const pf=addDays(f1,-1), pt=addDays(pf,-days);
  const prev=rkAggregate(rkStore,pt,pf);
  const yf=addDays(f1,-365), yt=addDays(t1,-365);
  const yoy=rkAggregate(rkStore,yf,yt);
  const rkSearch = (document.getElementById('rk-search').value||'').trim().toLowerCase();
  const topN = (rkStore === 'all' || rkStore === 'ec') ? 50 : 30;
  const allRanked=Object.entries(cur).sort((a,b)=>b[1]-a[1]);
  // If searching, find matching products with their actual rank
  let ranked;
  if (rkSearch) {{
    ranked = [];
    allRanked.forEach(([spu,qty], i) => {{
      const info = RK_INFO[spu] || {{}};
      const name = (info.name||spu).toLowerCase();
      const color = (info.color||'').toLowerCase();
      if (name.includes(rkSearch) || color.includes(rkSearch)) {{
        ranked.push([spu, qty, i+1]); // [spu, qty, actualRank]
      }}
    }});
  }} else {{
    ranked = allRanked.slice(0, topN).map(([spu,qty], i) => [spu, qty, i+1]);
  }}
  const tc=Object.values(cur).reduce((s,v)=>s+v,0), tp=Object.values(prev).reduce((s,v)=>s+v,0), ty=Object.values(yoy).reduce((s,v)=>s+v,0);
  const prevDates = pt.slice(5)+' ~ '+pf.slice(5);
  const yoyDates = yf.slice(5)+' ~ '+yt.slice(5);
  document.getElementById('rk-comp-header').innerHTML = '前期比<br class="br-mobile">('+prevDates+')';
  document.getElementById('rk-yoy-header').innerHTML = '前年比<br class="br-mobile">('+yoyDates+')';
  document.getElementById('rk-summary').innerHTML='<div class="rk-total"><span class="rk-total-num">'+tc.toLocaleString()+'</span><span class="rk-total-label">販売数</span></div><div class="rk-comp"><span class="rk-comp-label">前期比<br>('+prevDates+')</span>'+pctHtml(tc,tp)+'</div><div class="rk-comp"><span class="rk-comp-label">前年比<br>('+yoyDates+')</span>'+pctHtml(tc,ty)+'</div>';
  const medals = {{1:'🥇',2:'🥈',3:'🥉'}};
  document.getElementById('rk-body').innerHTML=ranked.map(([spu, qty, rank]) => {{
    const info=RK_INFO[spu]||{{}};
    const img=info.img?'<img class="product-img" src="'+info.img+'" loading="lazy">':'<div class="product-img no-img"></div>';
    const badge = medals[rank] || rank;
    return '<tr><td class="rank">'+badge+'</td><td class="product-cell">'+img+'<div class="product-info"><div class="product-name">'+(info.name||spu)+'</div><div class="product-color">'+(info.color||'')+'</div></div></td><td class="num highlight">'+qty+'</td><td class="num">'+pctHtml(qty,prev[spu]||0)+'</td><td class="num">'+pctHtml(qty,yoy[spu]||0)+'</td></tr>';
  }}).join('');
}}

// ══════════════════════════════════════════
// INVENTORY
// ══════════════════════════════════════════
let INV_DATA=null;

async function loadInventory() {{
  document.getElementById('inv-time').textContent = '読み込み中...';
  const [invCSV, prodCSV, ecInvCSV] = await Promise.all([
    mbQuery(120, 'csv'), mbQuery(90, 'csv'), mbQuery(137, 'csv')
  ]);
  // Store inventory by SKU (card 120)
  const storeInv={{}};
  for (const r of parseCSV(invCSV)) {{
    storeInv[r[0]] = {{ hara:parseInt(r[1])||0, shinjuku:parseInt(r[2])||0, osaka:parseInt(r[3])||0, futako:parseInt(r[4])||0, total:parseInt(r[6])||0 }};
  }}
  // EC inventory by SKU (card 137, CSV全量)
  const ecInv={{}};
  for (const r of parseCSV(ecInvCSV)) ecInv[r[0]] = parseInt(r[1])||0;
  // Base: card 90 (全商品), merge store + EC inventory
  INV_DATA = [];
  for (const r of parseCSV(prodCSV)) {{
    const sku=r[2], si=storeInv[sku]||{{}}, ecQty=ecInv[sku]||0;
    var pname = r[5]||'';
    if (sku && parseInt(sku.slice(-3)) >= 17 && pname.includes('Walker') && pname.includes('超撥水')) pname += ' (Wide)';
    INV_DATA.push({{ sku, img:r[0]||'', upc:r[3]||'', cat:r[4]||'', name:pname, color:r[6]||'', size:r[7]||'',
      hara:si.hara||0, shinjuku:si.shinjuku||0, osaka:si.osaka||0, futako:si.futako||0, total:si.total||0, ec:ecQty }});
  }}
  document.getElementById('inv-time').textContent = '更新: ' + nowJST() + '（リアルタイム）';
  pageLoaded.inventory = true;
  initInventory();
}}

function populateSelect(id, values) {{
  const sel=document.getElementById(id); const cur=sel.value;
  while(sel.options.length>1) sel.remove(1);
  [...values].sort().forEach(v => {{ const o=document.createElement('option'); o.value=v; o.textContent=v; sel.appendChild(o); }});
  if([...values].includes(cur)) sel.value=cur;
}}
function updateInvCascade() {{
  const fSearch=document.getElementById('f-search').value.trim().toLowerCase();
  const fUpc=document.getElementById('f-upc').value.trim();
  const fCat=document.getElementById('f-cat').value, fName=document.getElementById('f-name').value, fColor=document.getElementById('f-color').value;
  let pool=INV_DATA;
  if(fSearch) pool=pool.filter(d=>(d.name||'').toLowerCase().includes(fSearch)||(d.color||'').toLowerCase().includes(fSearch)||(d.upc||'').includes(fSearch)||(d.sku||'').toLowerCase().includes(fSearch));
  if(fUpc) pool=pool.filter(d=>d.upc===fUpc);
  populateSelect('f-cat', new Set(pool.filter(d=>d.cat).map(d=>d.cat)));
  if(fCat) pool=pool.filter(d=>d.cat===fCat);
  populateSelect('f-name', new Set(pool.filter(d=>d.name).map(d=>d.name)));
  if(fName) pool=pool.filter(d=>d.name===fName);
  populateSelect('f-color', new Set(pool.filter(d=>d.color).map(d=>d.color)));
  if(fColor) pool=pool.filter(d=>d.color===fColor);
  populateSelect('f-size', new Set(pool.filter(d=>d.size).map(d=>d.size)));
}}
function renderInventory() {{
  if(!INV_DATA) return;
  const fSearch=document.getElementById('f-search').value.trim().toLowerCase();
  const fUpc=document.getElementById('f-upc').value.trim(), fCat=document.getElementById('f-cat').value, fName=document.getElementById('f-name').value, fColor=document.getElementById('f-color').value, fSize=document.getElementById('f-size').value;
  let filtered=INV_DATA;
  if(fSearch) filtered=filtered.filter(d=>(d.name||'').toLowerCase().includes(fSearch)||(d.color||'').toLowerCase().includes(fSearch)||(d.upc||'').includes(fSearch)||(d.sku||'').toLowerCase().includes(fSearch));
  if(fUpc) filtered=filtered.filter(d=>d.upc===fUpc);
  if(fCat) filtered=filtered.filter(d=>d.cat===fCat);
  if(fName) filtered=filtered.filter(d=>d.name===fName);
  if(fColor) filtered=filtered.filter(d=>d.color===fColor);
  if(fSize) filtered=filtered.filter(d=>d.size===fSize);
  if(!(fSearch||fUpc||fCat||fName||fColor||fSize)) filtered=filtered.filter(d=>d.total>0);
  filtered.sort((a,b)=>a.name.localeCompare(b.name,'ja')||a.color.localeCompare(b.color,'ja')||a.size.localeCompare(b.size));
  document.getElementById('inv-count').textContent=filtered.length+' 件表示';
  const sc=v=>v>0?'<td class="stock has-stock">'+v+'</td>':'<td class="stock zero">0</td>';
  document.getElementById('inv-body').innerHTML=filtered.map(d => {{
    const img=d.img?'<img class="inv-img" src="'+d.img+'" loading="lazy">':'';
    const detail=d.color+(d.size?' / '+d.size:'');
    return '<tr><td class="desktop-only img-col">'+img+'</td><td class="name-col desktop-only">'+d.name+'</td><td class="color-col desktop-only">'+d.color+'</td><td class="size-col desktop-only">'+d.size+'</td><td class="mobile-img">'+img+'</td><td class="mobile-product"><div class="m-name">'+d.name+'</div><div class="m-detail">'+d.color+'</div><div class="m-size">'+d.size+'</div></td>'+sc(d.hara)+sc(d.shinjuku)+sc(d.osaka)+sc(d.futako)+sc(d.total)+sc(d.ec)+'</tr>';
  }}).join('');
}}
function initInventory() {{
  const upcInput=document.getElementById('f-upc'), upcList=document.getElementById('upc-list');
  const allUpcs=[...new Set(INV_DATA.filter(d=>d.upc).map(d=>d.upc))].sort();
  upcInput.addEventListener('input', () => {{
    const val=upcInput.value.trim(); upcList.innerHTML='';
    if(val.length>=2) allUpcs.filter(u=>u.startsWith(val)).slice(0,20).forEach(u=>{{const o=document.createElement('option');o.value=u;upcList.appendChild(o);}});
    if(allUpcs.includes(val)||val===''){{ updateInvCascade(); renderInventory(); }}
  }});
  upcInput.addEventListener('change',()=>{{ updateInvCascade(); renderInventory(); }});
  document.getElementById('f-cat').addEventListener('change',()=>{{ document.getElementById('f-name').value='';document.getElementById('f-color').value='';document.getElementById('f-size').value=''; updateInvCascade(); renderInventory(); }});
  document.getElementById('f-name').addEventListener('change',()=>{{ document.getElementById('f-color').value='';document.getElementById('f-size').value=''; updateInvCascade(); renderInventory(); }});
  document.getElementById('f-color').addEventListener('change',()=>{{ document.getElementById('f-size').value=''; updateInvCascade(); renderInventory(); }});
  document.getElementById('f-size').addEventListener('change',()=>renderInventory());
  // Search: input + button + Enter
  var _ist = null;
  function doInvSearch() {{
    try {{
      var btn = document.getElementById('inv-search-btn');
      btn.textContent = '検索中...';
      btn.style.background = '#e17055';
      document.getElementById('f-cat').value='';
      document.getElementById('f-name').value='';
      document.getElementById('f-color').value='';
      document.getElementById('f-size').value='';
      updateInvCascade();
      renderInventory();
      btn.textContent = '検索';
      btn.style.background = '#0984e3';
    }} catch(err) {{
      document.getElementById('inv-count').textContent = 'ERROR: ' + err.message;
      document.getElementById('inv-count').style.color = 'red';
    }}
  }}
  var searchInput = document.getElementById('f-search');
  var searchBtn = document.getElementById('inv-search-btn');
  searchInput.oninput = function() {{
    if (_ist) clearTimeout(_ist);
    _ist = setTimeout(doInvSearch, 300);
  }};
  searchInput.onkeyup = function(e) {{
    if (e.key === 'Enter') doInvSearch();
  }};
  searchBtn.onclick = doInvSearch;
  document.getElementById('clear-filters').addEventListener('click', function() {{
    ['f-upc','f-cat','f-name','f-color','f-size','f-search'].forEach(function(id) {{ document.getElementById(id).value=''; }});
    updateInvCascade(); renderInventory();
  }});
  updateInvCascade(); renderInventory();
}}
// Ranking search
let _rkSearchTimer = null;
function onRkSearch() {{
  if (_rkSearchTimer) clearTimeout(_rkSearchTimer);
  _rkSearchTimer = setTimeout(function() {{
    if (!RK_RAW) return;
    renderRanking();
  }}, 200);
}}

// onInvSearch/onInvClear now bound inside initInventory()
</script>
</body>
</html>"""

    OUTPUT.write_text(html.replace("{WORKER}", WORKER), encoding="utf-8")
    print(f"Static dashboard saved to {OUTPUT}")

if __name__ == "__main__":
    build()
