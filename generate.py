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
<link rel="icon" type="image/png" href="data:image/png;base64,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">
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
.mob-topbar {{ display:none !important; }}
.mob-overlay {{ display:none; }}
.ctrl-section {{ background:#fff; border-radius:10px; padding:10px 14px; margin-bottom:10px; box-shadow:0 1px 2px rgba(0,0,0,.04); }}
.ctrl-section .ctrl-label {{ font-size:9px; color:#b2bec3; font-weight:600; text-transform:uppercase; letter-spacing:1px; margin-bottom:6px; }}
header {{ margin-bottom:16px; }}
header h1 {{ font-size:18px; font-weight:700; }}
header .time {{ color:#636e72; font-size:11px; margin-top:3px; }}
.store-nav {{ display:flex; gap:0; border-radius:10px; overflow:hidden; box-shadow:0 1px 3px rgba(0,0,0,.08); }}
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
.rk-summary {{ display:flex; align-items:center; gap:24px; background:#fff; border-radius:8px; padding:6px 16px; margin-bottom:8px; box-shadow:0 1px 3px rgba(0,0,0,.06); }}
.rk-summary br {{ display:none; }}
.rk-total {{ display:flex; align-items:baseline; gap:8px; }}
.rk-total-num {{ font-size:22px; font-weight:700; color:#0984e3; }}
.rk-total-label {{ font-size:11px; color:#636e72; }}
.th-date {{ font-size:9px; color:#999; font-weight:400; }}
.rk-table th br {{ display:none; }}
.rk-date-label {{ font-size:11px; color:#636e72; font-weight:600; }}
.rk-date-input {{ padding:4px 6px; border:1px solid #dfe6e9; border-radius:6px; font-size:11px; width:120px; }}
@media (max-width:768px) {{ .rk-date-input {{ width:90px; font-size:10px; padding:3px 4px; }} }}
.rk-search-input {{ padding:4px 8px; border:1px solid #dfe6e9; border-radius:6px; font-size:11px; flex:1; min-width:60px; margin-left:8px; }}
.rk-comp {{ display:flex; align-items:center; gap:4px; white-space:nowrap; }}
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
.inv-controls {{ margin-bottom:8px; }}
.inv-search-row {{ display:flex; gap:6px; margin-bottom:6px; }}
.inv-search-input {{ flex:1; padding:7px 10px; border:1px solid #dfe6e9; border-radius:7px; font-size:13px; }}
.inv-search-input:focus {{ outline:none; border-color:#0984e3; }}
.inv-search-btn {{ padding:7px 14px; border:none; border-radius:7px; background:#0984e3; color:#fff; font-size:12px; font-weight:600; cursor:pointer; }}
.inv-filter-row {{ display:flex; gap:6px; align-items:flex-end; }}
.filter-group-sm {{ flex:1; }}
.filter-group-sm label {{ display:block; font-size:9px; color:#636e72; margin-bottom:2px; font-weight:600; }}
.filter-group-sm select {{ width:100%; padding:5px 6px; border:1px solid #dfe6e9; border-radius:6px; font-size:11px; background:#fff; }}
.pd-filters {{ display:flex; gap:8px; margin-bottom:8px; }}
.pd-filters .filter-group-sm {{ flex:1; }}
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
.clear-btn {{ padding:5px 12px; border:1px solid #dfe6e9; border-radius:6px; background:#fff; font-size:11px; cursor:pointer; color:#636e72; white-space:nowrap; transition:all .2s; }}
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
.sa-quick {{ display:flex; gap:4px; flex-wrap:wrap; }}
.sa-quick-row {{ display:flex; gap:4px; margin-bottom:8px; flex-wrap:nowrap; }}
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
  body {{ display:block !important; }}
  .sidebar {{ position:fixed !important; top:0 !important; left:-260px !important; width:240px !important; height:100vh; display:block; padding:16px 0; z-index:200; transition:left .25s ease; box-shadow:none; }}
  .sidebar.open {{ left:0 !important; box-shadow:4px 0 20px rgba(0,0,0,.3); }}
  .sidebar .logo {{ display:block; }}
  .sidebar a {{ display:block; text-align:left; padding:12px 20px; font-size:14px; border-top:none; }}
  .mob-overlay {{ display:none; position:fixed; inset:0; background:rgba(0,0,0,.4); z-index:199; }}
  .mob-overlay.open {{ display:block; }}
  .mob-topbar {{ display:flex !important; align-items:center; padding:10px 12px; background:#2d3436; color:#fff; position:sticky; top:0; z-index:100; }}
  .mob-topbar .hamburger {{ font-size:22px; cursor:pointer; padding:4px 8px; background:none; border:none; color:#fff; }}
  .mob-topbar .mob-title {{ font-size:14px; font-weight:700; margin-left:10px; }}
  .main {{ margin-left:0; margin-bottom:0; padding:10px 10px; max-width:100vw; }}
  .hide-mobile {{ display:none; }}
  .stats {{ grid-template-columns:repeat(2,1fr); }}
  .sa-cards {{ grid-template-columns:repeat(2,1fr); }}
  .sa-date-row {{ flex-direction:column; align-items:stretch; }}
  .sa-card .sa-value {{ font-size:18px; }}
  .store-btn {{ font-size:10px; padding:7px 2px; white-space:nowrap; }}
  .filter-bar {{ flex-direction:column; }}
  .inv-table-wrap {{ overflow-x:hidden; }}
  .rk-table-wrap {{ overflow-x:hidden; }}
  .rk-summary {{ flex-wrap:nowrap; gap:6px; padding:8px 10px; overflow-x:auto; }}
  .rk-summary br {{ display:inline; }}
  .sa-quick-row {{ flex-wrap:wrap; }}
  .rk-total-num {{ font-size:18px; }}
  .rk-total-label {{ font-size:9px; }}
  .rk-comp-label {{ font-size:8px; }}
  .rk-total-num {{ font-size:22px; }}
  .rk-comp {{ font-size:10px; }}
  .rk-comp-label {{ font-size:9px; }}
  .pct-up,.pct-down {{ font-size:11px; }}
  .rk-table th {{ font-size:8px; padding:5px 2px; }}
  .rk-table td {{ padding:5px 2px; font-size:10px; }}
  .rk-table .rank {{ font-size:12px; width:24px; }}
  .rk-table .product-img {{ width:28px; height:28px; }}
  .rk-table .product-cell {{ gap:4px; }}
  .rk-table .product-name {{ font-size:10px; max-width:70px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
  .rk-table .product-color {{ font-size:8px; max-width:70px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
  .rk-table .highlight {{ font-size:11px; }}
  .rk-table .num {{ font-size:9px; }}
  .th-date {{ font-size:7px; }}
  .rk-table th br {{ display:inline; }}
  .filter-group {{ min-width:auto; }}
  .filter-row .filter-group {{ flex:1; min-width:0; }}
  .inv-filter-row {{ flex-wrap:wrap; }}
  .inv-filter-row .filter-group-sm {{ flex:1 1 45%; min-width:0; }}
  .inv-filter-row .clear-btn {{ margin-top:4px; }}
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
    <div style="margin-bottom:8px;"><img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAfUAAABoCAYAAADox2k4AAAABGdBTUEAALGPC/xhBQAAAAFzUkdCAK7OHOkAABcwSURBVHhe7Z3dleVGEYDXEIBxBJCBIYIlA8Mbb4YMCAFnQAhsBIYM7AjMZoAjAL/xBvr2bp3p0faVVKX+q+76zqkzl8UzI3XXf5c0P38TBEEwDr/d5I+b/GuT//APQVCR323yh03+ucl/+YcgCIKgHDjX/23ylw//KwjqQvKIvpFITsFnm/x6k79++F9jg7H/+fGxOt99/DoK3Df3D6Nd2zP2+4XReDCcv32U2oxod1TJPWFNfnh8fPPjJr96fJwKL/bbyg56QpX+7ePjm/eboH/uIagLYtB85eb4+jn/0JDvN0HpyZ5S6QXr8ItNZE2QX25Sk582+fsmrIOsxR6uA4cn+8TX1nsFXCvBG6FVuv+6h7XkWuUr1/52k5Zwzaxr7rp7wTqka9JiPwmaqZ71vH+BIPL14+MHfr8J1zgb+/1ubQPC3n7RA+htD61At756fPzAbzbh3qcGpcPQaE/UEBSHagXF9gLBlIoThcjdk1UwqDuVLHtFZczPyf38EsJ+oQ9cZ8kqioy55nWTGLE2rJEXuFZa0DiZ3D1Zhf0b0d4IcuhXeq0zBvRniP2W3u9UatmvR7j//fqwNsvAApQMYihX2pr1Co4IA7ljiChS6WBT4rpSabVfBJuSTo2f5SlhfAb2R4DfB72rwvfx/ejFqKCvuWtfMfiI/ZKM5tZEK+w/Py94AXvIrdPINlKFZ4anERbOU8V0FYKHxghZhxYBhyqY35W7hivSer8wKhKd3LVohMp/RgMludLsJ+vgITA+S+ZWH5jT7vdeWtuvF5756iWTHxTkjpLNvmi5DHAvOLCWAefOnvXar7uBfeYKD925clzhpZ2IfuauH8nNlKzGHfudoVNVGgqd3Foh+OYlOVqUM+F7Z4fsOnfvCMbZI+AcXdMz4Vp7ciewr8DRkRhB3wtn+7yCzzjjSrGwl0iI8pwdJS/b2WDALbcgZ7JKO+1ZJdUrc6a6y13PkYwwqGQ9V1yhQmFPcxUc/+bl6OHZPaSy0sDcMyz26+FR5dZQUOXWKhUvHa4sP/v41QLBmUcitKySBeUqpXeb9KqgcJw8MqhhhFaUtf2/gp6xp7k9Ys34/zxAFX72+B6PHa04MJfCfvIYogYvOtCSK/4EnfSSFH/CnaCOwlgymlXPeEiAWkyQzwZJkNaZwap6RuLmqbK9ahOzz+JcIdrp97miRySZbo987gR1sAR11wt2A1phkTnbsOgZ1Z3bbFvB/h49HW/RTfny8fGUCOrBXYg7V18e5rYAuxvUaf1ZqqgVgnpaKVKlx/mWHesZ1wp6lgZFeSOjFzSOE2e8avclKIMmMcSuXB7h3Q3qYAlWONvZq6hUIQhKUaXboe2onQeA2YP6Psh5qtKxf+3+RLUeWGEmI30l7BVc6luJoG45v5u9BU9AT4d/okq/T7TgPyVNHOmYearScZhnA3J7eC/8CkcqQXksAXrZoE4V9Y/HRxWzB3WBtYkBl/uQPFqetpi5uksrdW+PilrPLGfez6AeFn0j6XSnbyWCOliq9ZmrqDRhiSq9DBxfWPRshaBOsuNp4p3rtv61Q7cDTEE38AHarpCwbFCnNRpV1AvibL21REfH0oJn4GXGZ5zRMXFU3mY27th9DMwFWu7oG38W15X/KBXUIaqoB1Tp4mxXeXteK6zPrM9Y3XntBtGdS/9muoVZi4GgPARkAvP7TT7b5ItNtLjyHyWDusWxuH1s4ABxtt5aol6wVOszzm/IPXmb2SgRkGNgLriKBGSJT3S0tDNgSyeRPLeee5fukcx25ozSjHpfVLr79T+SETsNZN65az2TmQI7ibDcl7dWNAlIui9WWdHRzmC/rcEfI2kSiC/IrdeRLBvYufHcghyJp7PAM1JlGfEcZhanQAckd71HYqnwR4V74Z68PVVBArLfF6us+CcyI6jrkHiUs30pvq7Ksl1XsqHcgpzJLFWUBJtRFWAWp2DJtJEZWrbcgzgkb9WDJRk7ktmO7s6IoK5D1iunJ3RS9+t1JjMO3F5CqgiNzJAFpW3hUVuiMzkFbaaNzNBCk+pj31IcHeuxyZHM1H25QgT168gRFWuWIz3CuirLrqe1xea9ipLMb+SW6ExOwZJpz9CylTNpb7Mo6NJ+P+6Kt8TmLhHUryPF5VEir50B83bcVRTLMIz3x448tERncgrWys9zCy1NmL3dh8UnXJEZui9XiaB+DTmiQo6QrpdGhj8qLvlIW4qlivAc1FEOnk2Px9jaQZCw/JEX73oG3h5jwxFa3yB3hvdiICgP+oY/PjuesfjqlZLIV1irKK+DL9LGGf2Mb7ZM35Jpn2Xvo5LalLfB0tIDcnvx3H3REJX6NcQfX9ELywzY0Ec+tSp1qgjLH3nxmHWTiMjftF75DKsHBAvt64nJ4D1m23LNvFHPUzcIx6r9k5daoloPBPHHdPGudLOiWldgeezI4+CLZHpk0aMzY6ZvybQ9BUVBzqS9BTDLQKNWvHZftESlfo74A003S2zrqng6+iqOdrEQT1kQCYhct4eW6IxOwfJoCuKpZSsJssekl2ver30NWaF6iqB+jPhjbdC1JJ7DvsmxVvtdsJwxe6pEvLZEZ4LzM/5YgxZPQUBsAh3zVJWyxvLHjWqzQlAPjhEd0MYdy2D3svqWDvdoxEsV5a0lOmumj4Hlrv9IvLTQUhvy1F2AZ/rGv6NbIpKs5P5bjXhbHy1RqR8j/tiiB9pn1hFvXbNiaBUR8fBiDXlm2FNLdFanwPpbgsKwLbQEaQ2yd55IkxGE/SH5PbIVjhkszlVk9iAWQf054o+tHVNLYbBstW5ZLA8tRpSHa7UcMfRiZqdgGZjzsHeSrHiY2UhJ9wNb0SS+BH/5Xo146b5YiaD+HNE3a6JuKQxIQJfFUkWNnAWlVYinZ+tndgqSqWtl5C6LJMTeglXqIK2Jk6UYQLwlPxoiqOcRf3zXTiyFwXD+v/agnGAx7JGNUxIOnoVcOlsbCBweA4taRk4eZVbDGhh7ge0yIMcAo3V9uedvHh9VjLyfQR1kz+8e21rszMs8VXH252tXxTLw0AIZyPDmQGbP9C1t21Gr4PRRvZG7CTnkXLzEzILYmkZG9Rt3iUo9j+hICTvR6hsdqaHss1WlzkJZ3tM9YtDkmniPNVWhtwpqdiz7wV6OeIQiFcC7TXAcXmAt5Y1eBKG7WALTzC344DXsNTZcyk60PoSO1LL6RjDMZTpHMmIVJdmyxyx4hUwfo8zdy5GMlpyR+cu1eZrZAFn/Uo4uXYurMqLfKEFU6p8iA8ulnmSxdJVLJK9usQzMjZQFpRvuscW3glOwDMyN1kKTYwRv8xoSgEsHVUuiVsrJj0QE9deIPy5tJ9p1RoaJB63a74LlGcKRWvBiJLR6Zq0GvINBagfmRmuhSevdw/saUsRWS3c+vPuNoA617MSiv3Ity5EO/2hkhCqKa5BOg9cqYJVMXypdjYxSFUunwdM5ukCiy7XXqFrkZ2tkpO5LCaJSfw02UqPLlvr6qzKMvbau1HGcXt/TTSUnj+lgXMG4WCo7hrtGOL/2WqWTjDCwxJ9crtHFsuzpsgNMC0BMwB+jF6UDKj9Pq28xMKeUEVrd8piO57beSpk+Rpm7pyPpHUg9z2zIetfqYqVrc1W8zSScEZX6C7IWtRJxS1fZknhOgaW1gfRseXtuiaas5BTImnP3dCS995f15jpGm8Y/QwJu7eRbq7+It6cHjoig/kACLutRE8uRT/dkvHX7HSytDehZIcvv9uZsVwYdswzM9dQzab170zNZs9qdjhhgCqCVnVj02XMn9xaW1gbSY/CF3ym/31tLdM9qmb5Uvhqpnf0/A2fA7x/hqEmLVDS17dP1AFMBolJ/0YEW+2o58uluvz0qdeCsy/Ke7h6DCJIV1hoACuphyeTfbtIjeZMM35sjxiZLvtHrCH6+tsvXu/sSlAV9Y09bdLPw9/h9DdhCz6PirhAsc5nOkfQYfJEqZIaNWjHT194z0npgTjpXBK0e3ag7yPq2sg+Zb9FIr+5LaaJSf/HHrRJv6aBpxNvxWTHStrZGWg6+yLDVLBX6ik7BYpSt9xsnwO/19hibtCdbJ9vi2DXi/egMVg/qktC1njIn2d6v7Zl0S857td+BhaJlp6Xl4Iv8Lm/ONniBgPnT4+NlaKG1OurB+OV3edOzXvZhqYRa+o2gDnKM0roS9jbY3RVLK61Vi1KqEI8t0WesmukTdHL3dyStqgHpJHhsEWMbPexDbFMjM3TbVq7U0THuqcc+Wga7Z3tHggpLK61FFiSBYKbzkVWdgiUIIC1atqL/rToDpZBkpJd9aHUZ8bbGe1YO6txLz3uyxKmWR8VDIZulkRZVDRUIv2uGszhhZadA5py7xyOp3bKVTpXHKlLWs5d9SFKhkdZnsaVZ2X4lqPbSN3zBfn3PZKaCUMWIVZTnlugRKzsFSxCoHWwxen6Pt/NeaUf2tg9JvDXiOUlf1X5lYLlnkJT2v0a6HN32HJQTcJzaZwGhpiOUn71spjUhVGmWgblaj2oRXL5+fHSnZ6PYh6Xy9t6CXxE5bu2pbwRobZxa+o+8SCamERa5BlKFeGyJnrFypQ44hdx9HkktR8La1vz5tZCKpZb9abAMMHm26xXtVzq5I+ybJU717mZ1xdJKq5EFieOfLaDB6kHdEgSQGi00nBQ/29swjZwtjvL4nayjRmp1X2qzov3KwPIoR1SWOOX5yOcWIzx2lJ6bND8LacDqQR0sA3PS/iuF55kNCaKjOCpJMjTirTsirGi/EkRH8ceWODVKAtwcabNopaRzEQfh1ejPiKBuCwKlnzmVfSidLNRGpvVHSkasfsNj0r6a/UryO5I/tr5bZVm0SouUbMt4bYleJYL6626MRkrphAQhj4ZOZ0yufZRKHR1N9+mqeEuoYDX7lftF3zxX6siyA3OSmWmk1ACFDEHM/CagCOoPZG5CI6VaaF5nNqwV8aji0c5Xsl/r/Muo0uwdCSM80pbS87EjqfiXPf9YCIuBlajsqDYkY/d2xOOxsj3iy01m7cjNQMkO7Ah8tcko3a3mWKqouw7Sc0tUQ1TqL1impu8GNulEeQvoIOs1ok5gv5YBSG/7sIr9kvzii7mHEYM7yaBF32b2p4dY2y53siBJJGZf9AjqL3BvuXs+EtbvDhIYvT1SJcnIyC3rFQaYVrFfGWZt1rI2IDahkVJHxS6xZEFWh5s6g9nbIxHUX5DujFasOiJ65vksd/QWfI/uS0tWsV/Zx9GHy6SboJHqCf1oZ+qCpS32dhPt99EVkGyQVwAunUktBntteT2xNQh4ndkgicG2mHUZuXICy9p6CuorQNBjTurHTUbXN0ucWlbfrI8dISjClWqKxU0zreoZ1ABEpf4adCB330diSfykK4C+jfJozlXkaMriwFpj9RvW7ktrVrBf0TcPya/YtVa8+YBiyOZaBOfJ9+8DNZuAI9+391ep0COof0qLFhrryPd5q9LTgSUvk+IWv+FlX2a33zRIzppoIbNN9l9GnhtvIau0RCKofwoOPXfvR6KtWiUwenFUgnQyPCW9JFzpXl0RL/c3u/1K8st9esHS7fM4V1MMjC23KCXFY0vUSgT1T7E+bXFVZ8ToRz8fzCEdLW+VhcVveHjj1+z2K/vmrciydPuqdb5GHZQTtBWRBZwtmxKsCYHr/eOjiqtBQBxUC10uCRUvL2gBb9ceA3P+YP0ZkGMg05u+Wa532Ra8dRBBI95aoneISj2PVNMaudJCky6Ap/a1gKPi2r05WLD6jdF9wcz2K/e2ir5V6xCPXqnjDL9/fKwCP9ujww3KYmmNU8WeBQGvj7HhbL5+fHR5bIBNWx5X9NCCnxHsiMcmwZutgCVOfb5JFX0bPahDzczNowIF5SFrfvf4qOKohSaB0WM7Ue7Lw7PCz7Cs+bIt0c7IunMM5nWIzKJvyx754BwtgwhnsmKFHu3351ietjiaxWDt+G88thOxDa7de9Ir96GRkd9XMaP9pv7dc1JljVPFj3w8VOosVI1qwaOzDeqBjlGZajhqoUkW7i0wcj8MLIF3G4nqaXzQN+wIvHaFwBqnlu0OWR87OhIyq9WISv0Yqa41kjNkqfpZb2+IjszwLK1lgAkZ1TfMaL/y2KTngC5Y4tRRt8+Eh0od2HhtFXUE56fFFzNwj6Wy4+8k74OAZN/eKt10YGmGTlYMzI1N+tjkDEGdOKV9PLb4wJyXoA4l25gxIBfksEyxQtqylcBIEuotMKatwBmcLFj2YNmWaGNSu5lF3yyxZdkjH2srbS8eW6KliPb7ORhYbi2OJG1VE0T4N49rJ4M+M7TeUywDc9Xe+HWDmeyX7pZc5ywBHboPzHmq1K2ttD0ztBWDeuBgeAxNAy1EkgHaidJK89YN4vplYGk2G4lqfTxm7AqBdWBu2WrdUkWlsvo5elTq15Bq2yoeg6IMLCHFqoZBsHT58BWjDczNZL9p92TUwUQrloE51qMInip1wFlqq6iUOEsPrnA3KHsL6jghGVhi0KeYgxkES5ev2hu/gg/rKo9NMsMyW7FlGZhjPYrom7egDndaNR4rqKA9VETWpy0wZr7fE2kr1Nu1X8Vi+8u2RCuTrutMrfeUGJhTYH1mPQJ6tN81cO+5NTkTb4aZDiwhI79R7S5py/eqjHQUMYP97o9CZjvqEawDc7ePIjxW6rQ2LFVUBPVAg0VfPL/nHbj+WSt1sOxNDMyVJU008OOzHfUIMTCnBEPLZTnPZFbF0RKVug7tenmb2dhXE7O2QgXrwNwoeLffvb7NXmh1GZjzWKmD1vmsHpwCG1qn4y2okxzLY2ww2/Ppe3CYlj+RGWfrZcA+Un2buSsE1oG5W0dgXoM6xnl1mpWW4uwVSFAH9Obq0xboo6eOEFXrvrU8u5MFS3UYQf0+VK3yN/qF2ZNIiIE5Bdx4rn2xF2/VU02i/a6HIJBbm714GzDL6cLtIR0nWAaYRhjo8my/BPD99a1A84E5r5U64GyvVFER1IM7XKnsGPjxVOXi7OUPt6SMdH5cE0u1HgmuHdZb3oOwGtiUxTcsO6B5VkVF2/012kzf4vxmhLZ6bn1EPBngUYdr1seL9lzt8u2l9/po7XeEguZorVeBhDB3/0dCMrCKPb7ibLow3gj1mrPgtBdPZ8Q1wTnm1gfB+Ly0rbGXo1bgKtUoRyW5+z+T3mfAR3uXk972e5Y8rVKNEody938myxalzwJVBKTXkPXl1ulMMMzVOVo7L90MHMuVoLBCImx1skiv/ba+dKvXrMeVbgj6yH3NjrUzhCx57POstbHsmcQTzo4qnskqhndGbtAH8dAiwxZy1/5MZrYduirP9vKq9AjsVG25azkT7Ld1J0nTbub6Ztc3bYd0L8sF9lwV1UORR+ZOpoiwnjO/PvQKuTUcfTgO29Cew4oQ+Gar2tHhuw5WhPVpldDdtV/uuYX9kvxb9Y3vm83HsG/4ztz9aoX18VBAFGOvSDHg9YDE5ug8WCtUCyu0Z3Owlvv1GHUtMH5rZ2YvBAQqBa/dGtaCSrBUMN8La1OrgChtv+hEDZ1FN0rqG/vlNYDV1DcShJr6NhT7THapjGYH2S7rgZGVyhJzQiKFguEkVlnvtAWK0Y6EOJO7reUj4Z7RK/Rr1CCf6n+tQJ6TUgEzvf7c7ykh+AWxX36fxX7Z/9C3x/qxDi31jf17qm+fffzqHTKXfz8+fngNJAs9KxiigKJL1pZ77rg1rD2KLYLizQRG9O3j45tvNkn3ojXyu8Upy9+nbg2vwcTJ4Nz52mrf5f65d5Fea7CHNWE9cnYwqv3yzo/0mgn6iJDqG9edvu61JaJvcm0t9A3dIrGAEfUt9bvfzRLUgY3lNYR/+vh5VnoGEg0tjK0HOBQc2hcfP/diVD1ote9e7cDLdT8L6qPRQt/SoD466Z65h+zRi8EEfsG4vRh4EARL8ebN/wEK3dtw+/HUhAAAAABJRU5ErkJggg==" style="height:22px;"></div>
    <div style="font-size:12px;color:#636e72;margin-bottom:20px;">Dashboard Login</div>
    <input id="login-pw" type="password" placeholder="パスワードを入力" style="width:100%;padding:10px 12px;border:1px solid #dfe6e9;border-radius:8px;font-size:14px;margin-bottom:12px;">
    <div id="login-err" style="color:#e74c3c;font-size:11px;margin-bottom:8px;display:none;">パスワードが違います</div>
    <button id="login-btn" style="width:100%;padding:10px;border:none;border-radius:8px;background:#0984e3;color:#fff;font-size:14px;font-weight:600;cursor:pointer;">ログイン</button>
  </div>
</div>
<div class="mob-topbar" style="display:none;"><button class="hamburger" id="mob-menu-btn">&#9776;</button><img src="data:image/png;base64,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" style="height:16px;filter:invert(1);margin-left:10px;"></div>
<div class="mob-overlay" id="mob-overlay"></div>
<div class="sidebar" id="sidebar" style="display:none;">
  <div class="logo"><img src="data:image/png;base64,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" style="height:18px;filter:invert(1);"></div>
  <a href="#" class="active" data-page="analysis">売上分析</a>
  <a href="#" data-page="ranking">商品ランキング</a>
  <a href="#" data-page="product">商品別売上</a>
  <a href="#" data-page="inventory">在庫確認</a>
  <a href="#" id="logout-btn" style="position:absolute;bottom:16px;left:0;right:0;color:#e74c3c;border-top:1px solid #636e72;margin-top:auto;">ログアウト</a>
</div>
<div class="main" style="display:none;">
  <!-- Sales Analysis -->
  <div id="page-analysis" class="page active">
    <header><h1>売上分析</h1></header>
    <div class="ctrl-section"><div class="ctrl-label">チャネル</div>
      <div class="store-nav sa-store-nav">
        <button class="store-btn active" data-sa-store="全体">VJP全体</button>
        <button class="store-btn" data-sa-store="EC">EC</button>
        <button class="store-btn" data-sa-store="店舗合計">店舗計</button>
        <button class="store-btn" data-sa-store="ハラカド店">ハラカド</button>
        <button class="store-btn" data-sa-store="新宿店">新宿</button>
        <button class="store-btn" data-sa-store="大阪店">大阪</button>
        <button class="store-btn" data-sa-store="二子玉川店">二子玉川</button>
      </div>
    </div>
    <div class="ctrl-section"><div class="ctrl-label">期間</div>
      <div class="sa-controls">
        <div class="sa-quick-row">
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
        </div>
        <div class="sa-date-row">
          <div class="sa-date-group"><label>期間</label><input type="date" id="sa-from"> ～ <input type="date" id="sa-to"></div>
          <label class="sa-compare-toggle"><input type="checkbox" id="sa-compare-check"> 比較</label>
          <div class="sa-date-group" id="sa-compare-group" style="display:none"><label>比較開始日</label><input type="date" id="sa-from2"> <span id="sa-to2-label" class="sa-to2-auto"></span></div>
        </div>
      </div>
    </div>
    <div class="sa-cards" id="sa-cards"><div class="loading">データ読み込み中</div></div>
    <div class="sa-chart-wrap"><canvas id="sa-chart" height="280"></canvas></div>
  </div>
  <!-- Ranking -->
  <div id="page-ranking" class="page">
    <header><h1>商品ランキング</h1></header>
    <div class="ctrl-section"><div class="ctrl-label">チャネル</div>
      <div class="store-nav rk-store-nav">
        <button class="store-btn active" data-rk-store="all">VJP全体</button>
        <button class="store-btn" data-rk-store="ec">EC</button>
        <button class="store-btn" data-rk-store="offline">店舗計</button>
        <button class="store-btn" data-rk-store="1">ハラカド</button>
        <button class="store-btn" data-rk-store="2">新宿</button>
        <button class="store-btn" data-rk-store="3">大阪</button>
        <button class="store-btn" data-rk-store="13">二子玉川</button>
      </div>
    </div>
    <div class="ctrl-section"><div class="ctrl-label">期間 ・ 検索</div>
      <div class="sa-quick-row">
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
      </div>
      <div class="sa-quick rk-quick" style="align-items:center;margin-top:6px;"><span class="rk-date-label">期間</span><input type="date" id="rk-from" class="rk-date-input"> ～ <input type="date" id="rk-to" class="rk-date-input"><input id="rk-search" type="text" placeholder="検索..." oninput="onRkSearch()" class="rk-search-input"><button onclick="document.getElementById('rk-search').value='';onRkSearch();" class="clear-btn" style="margin-left:4px;">クリア</button></div>
    </div>
    <div class="rk-summary" id="rk-summary"><div class="loading">データ読み込み中</div></div>
    <div class="table-wrap rk-table-wrap"><table class="rk-table"><thead><tr><th width="30">#</th><th>商品</th><th class="num">販売数</th><th class="num" id="rk-comp-header">前期比</th><th class="num" id="rk-yoy-header">前年比</th></tr></thead><tbody id="rk-body"></tbody></table></div>
  </div>
  <!-- Product Sales -->
  <div id="page-product" class="page">
    <header><h1>商品別売上</h1></header>
    <div class="ctrl-section"><div class="ctrl-label">商品検索</div>
      <div class="pd-filters">
        <div class="filter-group-sm"><label>カテゴリ</label><select id="pd-cat"><option value="">すべて</option></select></div>
        <div class="filter-group-sm"><label>商品名</label><select id="pd-name"><option value="">すべて</option></select></div>
        <div class="filter-group-sm"><label>カラー</label><select id="pd-color"><option value="">すべて</option></select></div>
      </div>
      <div class="sa-quick" style="align-items:center;margin-top:6px;"><input id="pd-search" type="text" placeholder="商品名で検索..." class="rk-search-input" style="margin-left:0;" oninput="onPdSearch()"><button onclick="document.getElementById('pd-search').value='';document.getElementById('pd-cat').value='';document.getElementById('pd-name').value='';document.getElementById('pd-color').value='';pdUpdateCascade();renderProductPage();" class="clear-btn" style="margin-left:4px;">クリア</button></div>
    </div>
    <div class="ctrl-section"><div class="ctrl-label">期間 ・ チャネル</div>
      <div class="sa-quick-row">
        <div class="sa-quick">
          <button class="sa-quick-btn active" data-pd-range="today">今日</button>
          <button class="sa-quick-btn" data-pd-range="yesterday">昨日</button>
          <button class="sa-quick-btn" data-pd-range="last3">過去3日</button>
          <button class="sa-quick-btn" data-pd-range="last7">過去7日</button>
          <button class="sa-quick-btn" data-pd-range="last15">過去15日</button>
          <button class="sa-quick-btn" data-pd-range="last30">過去30日</button>
        </div>
        <div class="sa-quick">
          <button class="sa-quick-btn" data-pd-range="thisweek">今週</button>
          <button class="sa-quick-btn" data-pd-range="lastweek">先週</button>
          <button class="sa-quick-btn" data-pd-range="thismonth">今月</button>
          <button class="sa-quick-btn" data-pd-range="lastmonth">先月</button>
          <button class="sa-quick-btn" data-pd-range="thisyear">今年</button>
          <button class="sa-quick-btn" data-pd-range="lastyear">去年</button>
        </div>
      </div>
      <div style="display:flex;align-items:center;gap:6px;margin-top:6px;flex-wrap:wrap;">
        <span class="rk-date-label">期間</span><input type="date" id="pd-from" class="rk-date-input"> ～ <input type="date" id="pd-to" class="rk-date-input">
        <label class="sa-compare-toggle" style="margin-left:8px;"><input type="checkbox" id="pd-compare-check"> 比較</label>
        <span id="pd-compare-group" style="display:none;"><input type="date" id="pd-from2" class="rk-date-input"> <span id="pd-to2-label" class="sa-to2-auto"></span></span>
        <span style="margin-left:8px;" id="pd-channel-checks"></span>
      </div>
    </div>
    <div id="pd-result"></div>
    <div class="sa-chart-wrap" style="margin-top:12px;"><canvas id="pd-chart" height="280"></canvas></div>
  </div>
  <!-- Inventory -->
  <div id="page-inventory" class="page">
    <header><h1>在庫確認</h1></header>
    <div class="ctrl-section"><div class="ctrl-label">商品検索</div>
      <div class="inv-controls">
        <div class="inv-search-row"><input id="f-search" type="text" placeholder="商品名・カラー・UPCで検索..." class="inv-search-input"><button id="inv-search-btn" class="inv-search-btn">検索</button><button class="clear-btn" id="clear-filters">クリア</button></div>
        <input id="f-upc" type="hidden" value="">
        <div class="inv-filter-row">
          <div class="filter-group-sm"><label>カテゴリ</label><select id="f-cat"><option value="">すべて</option></select></div>
          <div class="filter-group-sm"><label>商品名</label><select id="f-name"><option value="">すべて</option></select></div>
          <div class="filter-group-sm"><label>カラー</label><select id="f-color"><option value="">すべて</option></select></div>
          <div class="filter-group-sm"><label>サイズ</label><select id="f-size"><option value="">すべて</option></select></div>
        </div>
      </div>
    </div>
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
const USERS = {{
  'a49aff1951a384d5fa0f4860ab58c383052caf6e3ce7b6caa998e38ec3afc5db': {{ role:'admin', pages:['analysis','ranking','product','inventory'] }},
  'd3c80431f50c5e15f5b36f6ca66ecc0f7cf23db877a14760448cdd6c83a846cc': {{ role:'viewer', pages:['analysis'] }}
}};
let currentUser = null;
async function sha256(msg) {{ const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(msg)); return [...new Uint8Array(buf)].map(b => b.toString(16).padStart(2,'0')).join(''); }}
function unlockApp(hash) {{
  currentUser = USERS[hash];
  document.getElementById('login-overlay').style.display='none';
  document.getElementById('sidebar').style.display='block';
  document.querySelector('.main').style.display='';
  document.querySelector('.mob-topbar').style.removeProperty('display');
  // Show/hide menu items based on role
  document.querySelectorAll('.sidebar a[data-page]').forEach(a => {{
    a.style.display = currentUser.pages.includes(a.dataset.page) ? '' : 'none';
  }});
  // Set first allowed page as active
  const firstPage = currentUser.pages[0];
  document.querySelectorAll('.sidebar a').forEach(x => x.classList.remove('active'));
  document.querySelectorAll('.page').forEach(x => x.classList.remove('active'));
  const firstLink = document.querySelector('.sidebar a[data-page="'+firstPage+'"]');
  if (firstLink) firstLink.classList.add('active');
  document.getElementById('page-'+firstPage).classList.add('active');
  preloadProductInfo(); loadSalesAnalysis();
}}

// Preload card 90 (product info) into localStorage, refresh every 24h
let _prodInfoCache = null;
async function preloadProductInfo() {{
  const cacheKey = 'vj_prod_info';
  const cacheTimeKey = 'vj_prod_info_time';
  const cached = localStorage.getItem(cacheKey);
  const cachedTime = parseInt(localStorage.getItem(cacheTimeKey) || '0');
  const now = Date.now();
  if (cached && (now - cachedTime) < 86400000) {{
    _prodInfoCache = cached;
    return;
  }}
  // Fetch in background, don't block anything
  try {{
    const csv = await mbQuery(90, 'csv');
    localStorage.setItem(cacheKey, csv);
    localStorage.setItem(cacheTimeKey, String(now));
    _prodInfoCache = csv;
  }} catch(e) {{ /* silent fail, will fetch normally later */ }}
}}

function getCachedProductCSV() {{
  if (_prodInfoCache) return Promise.resolve(_prodInfoCache);
  const cached = localStorage.getItem('vj_prod_info');
  if (cached) {{ _prodInfoCache = cached; return Promise.resolve(cached); }}
  return mbQuery(90, 'csv').then(csv => {{ _prodInfoCache = csv; return csv; }});
}}
const savedAuth = localStorage.getItem('vj_auth');
if (savedAuth && USERS[savedAuth]) {{ unlockApp(savedAuth); }}
document.getElementById('login-btn').addEventListener('click', async () => {{ const h = await sha256(document.getElementById('login-pw').value); if (USERS[h]) {{ localStorage.setItem('vj_auth', h); unlockApp(h); }} else {{ document.getElementById('login-err').style.display='block'; }} }});
document.getElementById('login-pw').addEventListener('keydown', e => {{ if (e.key === 'Enter') document.getElementById('login-btn').click(); }});
document.getElementById('logout-btn').addEventListener('click', e => {{ e.preventDefault(); localStorage.removeItem('vj_auth'); location.reload(); }});

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

// ── Mobile hamburger menu ──
const mobMenuBtn = document.getElementById('mob-menu-btn');
const mobOverlay = document.getElementById('mob-overlay');
const sidebar = document.querySelector('.sidebar');
function openMobMenu() {{ sidebar.classList.add('open'); mobOverlay.classList.add('open'); }}
function closeMobMenu() {{ sidebar.classList.remove('open'); mobOverlay.classList.remove('open'); }}
mobMenuBtn.addEventListener('click', openMobMenu);
mobOverlay.addEventListener('click', closeMobMenu);

// ── Page navigation ──
let pageLoaded = {{ analysis: false, ranking: false, product: false, inventory: false }};
document.querySelectorAll('.sidebar a').forEach(a => {{
  a.addEventListener('click', e => {{
    e.preventDefault();
    document.querySelectorAll('.sidebar a').forEach(x => x.classList.remove('active'));
    document.querySelectorAll('.page').forEach(x => x.classList.remove('active'));
    a.classList.add('active');
    document.getElementById('page-' + a.dataset.page).classList.add('active');
    if (a.dataset.page === 'ranking' && !pageLoaded.ranking) loadRanking();
    if (a.dataset.page === 'product' && !pageLoaded.product) loadProductPage();
    if (a.dataset.page === 'inventory' && !pageLoaded.inventory) loadInventory();
    closeMobMenu();
  }});
}});

// ══════════════════════════════════════════
// SALES ANALYSIS
// ══════════════════════════════════════════
let SA_DATA = null, saChart = null, saStore = '全体';

async function loadSalesAnalysis() {{
  const [offResp, ecCSV, todayResp] = await Promise.all([
    mbSQL("SELECT report_date, store_scope, sales_amount, sales_qty, customers_count, avg_transaction_value FROM daily_sales_reports WHERE report_date < CURRENT_DATE ORDER BY report_date, store_scope"),
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
    const sales = Math.round(r[1]||0), txnCount = r[2]||0, atv = Math.round(r[3]||0);
    // card 133 only has 取引数, not 販売点数. Use 取引数 as customers (=取引数), qty unknown so use txnCount as approximation
    SA_DATA.push({{ date: todayStr, store: storeName, sales, qty: txnCount, customers: txnCount, atv }});
    todayOffTotal.sales += sales;
    todayOffTotal.qty += txnCount;
    todayOffTotal.customers += txnCount;
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
  const fmtRate = n => n.toFixed(2);
  const setRateA = sumA.customers ? sumA.qty / sumA.customers : 0;
  const setRateB = sumB && sumB.customers ? sumB.qty / sumB.customers : 0;
  const metrics=[{{l:'売上',a:sumA.sales,b:sumB?sumB.sales:0,f:fmtYen}},{{l:'セット率',a:setRateA,b:setRateB,f:fmtRate}},{{l:'客数',a:sumA.customers,b:sumB?sumB.customers:0,f:fmtNum}},{{l:'客単価',a:sumA.atv,b:sumB?sumB.atv:0,f:fmtYen}}];
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

async function ensureRankingData() {{
  if (RK_RAW) return;
  await loadRanking();
}}

async function loadRanking() {{
  const [offCSV, ecCSV, infoCSV] = await Promise.all([
    mbQuery(134, 'csv'), mbQuery(135, 'csv'), getCachedProductCSV()
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
  const topN = 50;
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
  document.getElementById('rk-comp-header').innerHTML = '前期比<br><span class="th-date">('+prevDates+')</span>';
  document.getElementById('rk-yoy-header').innerHTML = '前年比<br><span class="th-date">('+yoyDates+')</span>';
  document.getElementById('rk-summary').innerHTML='<div class="rk-total"><span class="rk-total-label">販売数</span><span class="rk-total-num">'+tc.toLocaleString()+'</span></div><div class="rk-comp"><span class="rk-comp-label">前期比<br>('+prevDates+')</span>'+pctHtml(tc,tp)+'</div><div class="rk-comp"><span class="rk-comp-label">前年比<br>('+yoyDates+')</span>'+pctHtml(tc,ty)+'</div>';
  const medals = {{1:'🥇',2:'🥈',3:'🥉'}};
  document.getElementById('rk-body').innerHTML=ranked.map(([spu, qty, rank]) => {{
    const info=RK_INFO[spu]||{{}};
    const img=info.img?'<img class="product-img" src="'+info.img+'" loading="lazy">':'<div class="product-img no-img"></div>';
    const badge = medals[rank] || rank;
    return '<tr><td class="rank">'+badge+'</td><td class="product-cell">'+img+'<div class="product-info"><div class="product-name">'+(info.name||spu)+'</div><div class="product-color">'+(info.color||'')+'</div></div></td><td class="num highlight">'+qty+'</td><td class="num">'+pctHtml(qty,prev[spu]||0)+'</td><td class="num">'+pctHtml(qty,yoy[spu]||0)+'</td></tr>';
  }}).join('');
}}

// ══════════════════════════════════════════
// ══════════════════════════════════════════
// PRODUCT SALES PAGE
// ══════════════════════════════════════════
let PD_SPU_LIST = null;

async function loadProductPage() {{
  // Reuse ranking data (or load if not loaded yet)
  await ensureRankingData();
  // Also need product info with UPC + category
  const prodCSV = await getCachedProductCSV();
  // Build SPU list with info
  const seen = {{}};
  PD_SPU_LIST = [];
  for (const r of parseCSV(prodCSV)) {{
    const spu = r[1];
    if (!seen[spu]) {{
      seen[spu] = true;
      PD_SPU_LIST.push({{ spu, name:r[5]||'', color:r[6]||'', cat:r[4]||'', img:r[0]||'', upc:r[3]||'' }});
    }}
  }}
  pageLoaded.product = true;
  initProductPage();
}}

function pdPopulate(id, vals) {{
  const sel = document.getElementById(id);
  const cur = sel.value;
  while(sel.options.length > 1) sel.remove(1);
  [...vals].sort().forEach(v => {{ const o = document.createElement('option'); o.value=v; o.textContent=v; sel.appendChild(o); }});
  if ([...vals].includes(cur)) sel.value = cur;
}}

function pdUpdateCascade() {{
  const search = (document.getElementById('pd-search')||{{}}).value;
  const sq = (search||'').trim().toLowerCase();
  const cat = document.getElementById('pd-cat').value;
  const name = document.getElementById('pd-name').value;
  let pool = PD_SPU_LIST;
  if (sq) pool = pool.filter(d => (d.name||'').toLowerCase().includes(sq) || (d.color||'').toLowerCase().includes(sq));
  pdPopulate('pd-cat', new Set(pool.filter(d=>d.cat).map(d=>d.cat)));
  if (cat) pool = pool.filter(d => d.cat === cat);
  pdPopulate('pd-name', new Set(pool.filter(d=>d.name).map(d=>d.name)));
  if (name) pool = pool.filter(d => d.name === name);
  pdPopulate('pd-color', new Set(pool.filter(d=>d.color).map(d=>d.color)));
}}

function pdGetSelectedSPUs() {{
  const search = (document.getElementById('pd-search')||{{}}).value;
  const sq = (search||'').trim().toLowerCase();
  const cat = document.getElementById('pd-cat').value;
  const name = document.getElementById('pd-name').value;
  const color = document.getElementById('pd-color').value;
  let pool = PD_SPU_LIST;
  if (sq) pool = pool.filter(d => (d.name||'').toLowerCase().includes(sq) || (d.color||'').toLowerCase().includes(sq));
  if (cat) pool = pool.filter(d => d.cat === cat);
  if (name) pool = pool.filter(d => d.name === name);
  if (color) pool = pool.filter(d => d.color === color);
  return pool;
}}

let _pdSearchTimer = null;
function onPdSearch() {{
  if (_pdSearchTimer) clearTimeout(_pdSearchTimer);
  _pdSearchTimer = setTimeout(function() {{
    if (!PD_SPU_LIST) return;
    document.getElementById('pd-cat').value='';
    document.getElementById('pd-name').value='';
    document.getElementById('pd-color').value='';
    pdUpdateCascade();
    renderProductPage();
  }}, 300);
}}

let pdChart = null;
const PD_CHANNELS = [
  {{id:'all',label:'全体',color:'#2d3436'}},
  {{id:'ec',label:'EC',color:'#0984e3'}},
  {{id:'1',label:'ハラカド',color:'#00b894'}},
  {{id:'2',label:'新宿',color:'#e17055'}},
  {{id:'3',label:'大阪',color:'#fdcb6e'}},
  {{id:'13',label:'二子玉川',color:'#a29bfe'}},
  {{id:'offline',label:'店舗計',color:'#636e72'}}
];

function renderProductPage() {{
  if (!RK_RAW || !PD_SPU_LIST) return;
  const f1 = document.getElementById('pd-from').value;
  const t1 = document.getElementById('pd-to').value;
  if (!f1 || !t1) return;

  const selected = pdGetSelectedSPUs();
  if (selected.length === 0) {{
    document.getElementById('pd-result').innerHTML = '<div style="color:#636e72;padding:20px;text-align:center;">商品を選択してください</div>';
    if (pdChart) {{ pdChart.destroy(); pdChart = null; }}
    return;
  }}

  const spuKeys = new Set(selected.map(d => d.spu));
  const offlineIds = ['1','2','3','13'];
  const comparing = document.getElementById('pd-compare-check').checked;
  const f2 = document.getElementById('pd-from2').value;
  const days = diffDays(f1, t1);
  const t2 = addDays(f2, days);

  // Aggregate helper
  function aggregateRange(from, to) {{
    const total = {{}};
    const daily = {{}};
    PD_CHANNELS.forEach(c => {{ total[c.id] = 0; daily[c.id] = {{}}; }});
    for (const [k, q] of Object.entries(RK_RAW)) {{
      const [s, d, spu] = k.split('|');
      if (d >= from && d <= to && spuKeys.has(spu) && total[s] !== undefined) {{
        total[s] += q;
        daily[s][d] = (daily[s][d] || 0) + q;
      }}
    }}
    const dates = [...new Set(Object.keys(daily['ec']||{{}}).concat(
      ...offlineIds.map(id => Object.keys(daily[id]||{{}}))
    ))].sort();
    total['all'] = 0; total['offline'] = 0;
    PD_CHANNELS.forEach(c => {{ if (c.id !== 'all' && c.id !== 'offline') total['all'] += total[c.id]; }});
    offlineIds.forEach(id => {{ total['offline'] += total[id]; }});
    dates.forEach(d => {{
      let allV = 0, offV = 0;
      PD_CHANNELS.forEach(c => {{ if (c.id !== 'all' && c.id !== 'offline') allV += (daily[c.id][d] || 0); }});
      offlineIds.forEach(id => {{ offV += (daily[id][d] || 0); }});
      daily['all'][d] = allV;
      daily['offline'][d] = offV;
    }});
    return {{ total, daily, dates }};
  }}

  const cur = aggregateRange(f1, t1);
  const storeTotal = cur.total;
  const storeDaily = cur.daily;
  const allDates = cur.dates;
  const cmp = comparing && f2 ? aggregateRange(f2, t2) : null;

  // Product card - show appropriate level of detail
  const info = selected[0];
  const pdCat = document.getElementById('pd-cat').value;
  const pdName = document.getElementById('pd-name').value;
  const pdColor = document.getElementById('pd-color').value;

  let displayName = '';
  let displaySub = '';
  let displayImg = '';

  if (pdName) {{
    // Specific product selected
    displayName = pdName;
    displayImg = info.img ? '<img src="'+info.img+'" style="width:36px;height:36px;border-radius:6px;object-fit:cover;">' : '';
    const uniqueColors = [...new Set(selected.map(d => d.color).filter(Boolean))];
    displaySub = pdColor ? pdColor : (uniqueColors.length > 1 ? uniqueColors.length + '色' : (uniqueColors[0]||''));
  }} else if (pdCat) {{
    // Category only
    displayName = pdCat;
    const uniqueNames = [...new Set(selected.map(d => d.name).filter(Boolean))];
    displaySub = uniqueNames.length + '商品';
  }} else {{
    displayName = '全商品';
    displaySub = selected.length + ' SPU';
  }}

  const spuLabel = selected.length > 1 ? ' <span style="color:#b2bec3;font-size:10px;">'+selected.length+' SPU</span>' : '';

  let html = '<div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">';
  html += displayImg;
  html += '<span style="font-weight:700;font-size:14px;">'+displayName+' <span style="color:#999;font-size:12px;">'+displaySub+'</span>'+spuLabel+'</span>';
  html += '</div>';

  // Channel cards grid
  html += '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(80px,1fr));gap:6px;margin-bottom:8px;">';
  PD_CHANNELS.forEach(c => {{
    const isAll = c.id === 'all';
    const bg = isAll ? '#0984e3' : '#fff';
    const fg = isAll ? '#fff' : '#2d3436';
    const labelFg = isAll ? 'rgba(255,255,255,.7)' : '#999';
    const curVal = storeTotal[c.id] || 0;
    const cmpVal = cmp ? (cmp.total[c.id] || 0) : 0;
    html += '<div style="background:'+bg+';border-radius:8px;padding:8px 10px;text-align:center;box-shadow:0 1px 3px rgba(0,0,0,.06);">';
    html += '<div style="font-size:9px;color:'+labelFg+';margin-bottom:2px;">'+c.label+'</div>';
    html += '<div style="font-size:18px;font-weight:700;color:'+fg+';">'+curVal+'</div>';
    if (cmp) {{
      const diff = cmpVal > 0 ? ((curVal - cmpVal) / cmpVal * 100).toFixed(1) : '-';
      const diffColor = isAll ? 'rgba(255,255,255,.8)' : (parseFloat(diff) >= 0 ? '#00b894' : '#e74c3c');
      const sign = parseFloat(diff) >= 0 ? '+' : '';
      html += '<div style="font-size:10px;color:'+diffColor+';">'+cmpVal+' → '+(diff!=='-'?sign+diff+'%':'-')+'</div>';
    }}
    html += '</div>';
  }});
  html += '</div>';

  document.getElementById('pd-result').innerHTML = html;

  // Trend chart: only checked channels + comparison
  const checkedIds = new Set();
  document.querySelectorAll('.pd-ch-check:checked').forEach(cb => checkedIds.add(cb.dataset.ch));
  const chartChannels = PD_CHANNELS.filter(c => checkedIds.has(c.id));
  const labels = allDates.map(d => d.slice(5));
  const smallPt = allDates.length > 31;
  const datasets = chartChannels.map(c => ({{
    label: c.label,
    data: allDates.map(d => storeDaily[c.id][d] || 0),
    borderColor: c.color,
    backgroundColor: c.color + '18',
    fill: true,
    tension: 0.4,
    pointRadius: smallPt ? 0 : 4,
    pointHoverRadius: 6,
    pointBackgroundColor: '#fff',
    pointBorderColor: c.color,
    pointBorderWidth: 2,
    borderWidth: 2.5,
  }}));

  // Add comparison dashed lines
  if (cmp && cmp.dates.length) {{
    chartChannels.forEach(c => {{
      datasets.push({{
        label: c.label + '(比較)',
        data: allDates.map((d, i) => cmp.dates[i] ? (cmp.daily[c.id][cmp.dates[i]] || 0) : 0),
        borderColor: c.color + '80',
        backgroundColor: 'transparent',
        fill: false,
        tension: 0.4,
        pointRadius: 0,
        borderWidth: 1.5,
        borderDash: [5, 3],
      }});
    }});
  }}

  const ctx = document.getElementById('pd-chart').getContext('2d');
  if (pdChart) pdChart.destroy();
  pdChart = new Chart(ctx, {{
    type: 'line',
    data: {{ labels, datasets }},
    options: {{
      responsive: true,
      maintainAspectRatio: false,
      interaction: {{ mode: 'index', intersect: false }},
      plugins: {{
        legend: {{ display: false }},
        tooltip: {{
          backgroundColor: 'rgba(45,52,54,.9)',
          titleFont: {{ size: 12 }},
          bodyFont: {{ size: 12 }},
          padding: 10,
          cornerRadius: 8,
          callbacks: {{
            label: item => ' ' + item.dataset.label + ': ' + item.raw + ' 点'
          }}
        }}
      }},
      scales: {{
        y: {{ beginAtZero: true, grid: {{ color: '#f0f0f0' }}, ticks: {{ font: {{ size: 10 }} }} }},
        x: {{ grid: {{ display: false }}, ticks: {{ font: {{ size: 10 }} }} }}
      }}
    }}
  }});
}}

function pdUpdateCompare() {{
  const f1 = document.getElementById('pd-from').value;
  const t1 = document.getElementById('pd-to').value;
  const f2 = document.getElementById('pd-from2').value;
  if (f1 && t1 && f2) {{
    const d = diffDays(f1, t1);
    document.getElementById('pd-to2-label').textContent = '～ ' + addDays(f2, d);
  }}
}}

function initProductPage() {{
  const [f, t] = quickRange('today');
  document.getElementById('pd-from').value = f;
  document.getElementById('pd-to').value = t;

  document.getElementById('pd-from2').value = addDays(f, -365);
  pdUpdateCascade();
  pdUpdateCompare();

  // Filter events
  document.getElementById('pd-cat').addEventListener('change', function() {{
    document.getElementById('pd-name').value='';
    document.getElementById('pd-color').value='';
    pdUpdateCascade(); renderProductPage();
  }});
  document.getElementById('pd-name').addEventListener('change', function() {{
    document.getElementById('pd-color').value='';
    pdUpdateCascade(); renderProductPage();
  }});
  document.getElementById('pd-color').addEventListener('change', function() {{
    renderProductPage();
  }});

  // Quick date buttons
  document.querySelectorAll('[data-pd-range]').forEach(btn => {{
    btn.addEventListener('click', function() {{
      document.querySelectorAll('[data-pd-range]').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const [f, t] = quickRange(btn.dataset.pdRange);
      document.getElementById('pd-from').value = f;
      document.getElementById('pd-to').value = t;
      document.getElementById('pd-from2').value = addDays(f, -365);
      pdUpdateCompare();
      renderProductPage();
    }});
  }});

  ['pd-from','pd-to'].forEach(id => {{
    document.getElementById(id).addEventListener('change', function() {{
      document.querySelectorAll('[data-pd-range]').forEach(b => b.classList.remove('active'));
      pdUpdateCompare();
      renderProductPage();
    }});
  }});

  // Comparison controls
  document.getElementById('pd-compare-check').addEventListener('change', function() {{
    document.getElementById('pd-compare-group').style.display = this.checked ? '' : 'none';
    pdUpdateCompare();
    renderProductPage();
  }});
  document.getElementById('pd-from2').addEventListener('change', function() {{
    pdUpdateCompare();
    renderProductPage();
  }});

  // Channel checkboxes
  const checkContainer = document.getElementById('pd-channel-checks');
  const chartChs = PD_CHANNELS.filter(c => c.id !== 'all' && c.id !== 'offline');
  checkContainer.innerHTML = chartChs.map(c =>
    '<label style="font-size:11px;cursor:pointer;margin-right:8px;"><input type="checkbox" class="pd-ch-check" data-ch="'+c.id+'" checked style="margin-right:2px;accent-color:'+c.color+';">'+c.label+'</label>'
  ).join('');
  checkContainer.querySelectorAll('.pd-ch-check').forEach(cb => cb.addEventListener('change', function() {{
    renderProductPage();
  }}));

  // Don't render until product is selected
  document.getElementById('pd-result').innerHTML = '<div style="color:#b2bec3;padding:30px;text-align:center;">商品を選択してください</div>';
}}

// INVENTORY
// ══════════════════════════════════════════
let INV_DATA=null;

async function loadInventory() {{
  const [invCSV, prodCSV, ecInvCSV] = await Promise.all([
    mbQuery(120, 'csv'), getCachedProductCSV(), mbQuery(137, 'csv')
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
