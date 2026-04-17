// Secrets are injected as Worker secret_text bindings (see deploy.sh + local secrets.md):
//   MB_API_KEY, PREWARM_SECRET, SM_CLIENT_ID, SM_CLIENT_SECRET, SM_CONTRACT
// Public (non-secret) constants stay here.

const MB_BASE = "https://bi.vivaia.jp";
const ALLOWED_ORIGINS = ["https://setsu0081.github.io", "https://vivaia-sales-dashboard.vercel.app", "http://localhost:8787", "http://localhost:3000"];

const SM_ID_BASE = "https://id.smaregi.jp";
const SM_API_BASE = "https://api.smaregi.jp";
const SM_SCOPES = "pos.orders:read pos.stores:read pos.suppliers:read pos.products:read pos.stock:read";

function corsHeaders(request) {
  const origin = request.headers.get("Origin") || "";
  const allowed = ALLOWED_ORIGINS.includes(origin) ? origin : ALLOWED_ORIGINS[0];
  return {
    "Access-Control-Allow-Origin": allowed,
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Max-Age": "86400",
  };
}

async function mbCardCSV(cardId) {
  const r = await fetch(`${MB_BASE}/api/card/${cardId}/query/csv`, {
    method: "POST",
    headers: { "X-Api-Key": MB_API_KEY, "Content-Type": "application/json" },
    body: "{}",
  });
  if (!r.ok) throw new Error(`card ${cardId} HTTP ${r.status}`);
  return await r.text();
}

async function mbSQL(sql) {
  const r = await fetch(`${MB_BASE}/api/dataset`, {
    method: "POST",
    headers: { "X-Api-Key": MB_API_KEY, "Content-Type": "application/json" },
    body: JSON.stringify({ type: "native", native: { query: sql }, database: 2 }),
  });
  if (!r.ok) throw new Error(`mbSQL HTTP ${r.status}`);
  return await r.text();
}

async function smaregiAllProducts() {
  const token = await smaregiToken();
  const pages = await Promise.all(
    Array.from({ length: 15 }, (_, i) => i + 1).map(async page => {
      const r = await fetch(`${SM_API_BASE}/${SM_CONTRACT}/pos/products?limit=1000&page=${page}`, {
        headers: { "Authorization": `Bearer ${token}` },
      });
      if (!r.ok) return [];
      const arr = await r.json();
      return Array.isArray(arr) ? arr : [];
    })
  );
  const dict = {};
  for (const arr of pages) {
    for (const p of arr) {
      dict[p.productId] = {
        productCode: p.productCode,
        productName: p.productName,
        size: p.size,
        color: p.color,
        categoryId: p.categoryId,
        groupCode: p.groupCode,
      };
    }
  }
  return JSON.stringify(dict);
}

async function smaregiAllCategories() {
  const token = await smaregiToken();
  const r = await fetch(`${SM_API_BASE}/${SM_CONTRACT}/pos/categories?limit=1000`, {
    headers: { "Authorization": `Bearer ${token}` },
  });
  if (!r.ok) throw new Error(`categories HTTP ${r.status}`);
  const arr = await r.json();
  const dict = {};
  if (Array.isArray(arr)) {
    for (const c of arr) dict[c.categoryId] = c.categoryName || c.categoryAbbr || "";
  }
  return JSON.stringify(dict);
}

async function smaregiAllSuppliers() {
  const token = await smaregiToken();
  const r = await fetch(`${SM_API_BASE}/${SM_CONTRACT}/pos/suppliers?limit=1000`, {
    headers: { "Authorization": `Bearer ${token}` },
  });
  if (!r.ok) throw new Error(`suppliers HTTP ${r.status}`);
  const arr = await r.json();
  const dict = {};
  if (Array.isArray(arr)) {
    for (const s of arr) dict[s.supplierId] = s.supplierName || s.name || "";
  }
  return JSON.stringify(dict);
}

const PREWARM_JOBS = {
  prod_info: {
    contentType: "text/csv",
    fetch: () => mbCardCSV(90),
  },
  hist_qty: {
    contentType: "application/json",
    fetch: () => mbSQL(
      "SELECT (t.transaction_date_time AT TIME ZONE 'Asia/Tokyo')::date AS d, t.store_id, SUM(CAST(ti.quantity AS numeric)) AS q FROM transactions t JOIN transaction_items ti ON ti.transaction_head_id = t.transaction_head_id WHERE (t.transaction_date_time AT TIME ZONE 'Asia/Tokyo')::date < '2025-09-01' GROUP BY 1,2"
    ),
  },
  sm_products: {
    contentType: "application/json",
    fetch: () => smaregiAllProducts(),
  },
  sm_categories: {
    contentType: "application/json",
    fetch: () => smaregiAllCategories(),
  },
  sm_suppliers: {
    contentType: "application/json",
    fetch: () => smaregiAllSuppliers(),
  },
};

async function runPrewarm() {
  const results = {};
  for (const [key, job] of Object.entries(PREWARM_JOBS)) {
    try {
      const t0 = Date.now();
      const data = await job.fetch();
      const ts = Date.now();
      await DASHBOARD_CACHE.put(key, data, {
        metadata: { ts, contentType: job.contentType, bytes: data.length },
      });
      results[key] = { ok: true, ts, bytes: data.length, ms: ts - t0 };
    } catch (e) {
      results[key] = { ok: false, ts: Date.now(), err: String(e) };
    }
  }
  await DASHBOARD_CACHE.put("prewarm_status", JSON.stringify({ runAt: Date.now(), results }));
  return results;
}

async function smaregiToken() {
  const cached = await DASHBOARD_CACHE.getWithMetadata("sm_token");
  if (cached.value && cached.metadata && cached.metadata.exp && Date.now() < cached.metadata.exp - 60000) {
    return cached.value;
  }
  const resp = await fetch(`${SM_ID_BASE}/app/${SM_CONTRACT}/token`, {
    method: "POST",
    headers: {
      "Authorization": "Basic " + btoa(`${SM_CLIENT_ID}:${SM_CLIENT_SECRET}`),
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: `grant_type=client_credentials&scope=${encodeURIComponent(SM_SCOPES)}`,
  });
  if (!resp.ok) throw new Error(`smaregi token HTTP ${resp.status}: ${await resp.text()}`);
  const data = await resp.json();
  const exp = Date.now() + data.expires_in * 1000;
  await DASHBOARD_CACHE.put("sm_token", data.access_token, {
    metadata: { exp },
    expirationTtl: Math.max(60, data.expires_in - 30),
  });
  return data.access_token;
}

async function smaregiProxy(subPath, search) {
  const token = await smaregiToken();
  const url = `${SM_API_BASE}/${SM_CONTRACT}/pos/${subPath}${search || ""}`;
  const resp = await fetch(url, { headers: { "Authorization": `Bearer ${token}` } });
  return {
    status: resp.status,
    body: await resp.text(),
    contentType: resp.headers.get("Content-Type") || "application/json",
  };
}

addEventListener("scheduled", event => {
  event.waitUntil(runPrewarm());
});

addEventListener("fetch", event => {
  event.respondWith(handleRequest(event.request));
});

async function handleRequest(request) {
  if (request.method === "OPTIONS") {
    return new Response(null, { status: 204, headers: corsHeaders(request) });
  }

  const url = new URL(request.url);
  const path = url.pathname;

  if (path.startsWith("/cache/")) {
    const key = path.slice(7);
    const { value, metadata } = await DASHBOARD_CACHE.getWithMetadata(key);
    if (value === null) {
      return new Response(`Not cached: ${key}`, { status: 404, headers: corsHeaders(request) });
    }
    return new Response(value, {
      status: 200,
      headers: {
        "Content-Type": (metadata && metadata.contentType) || "text/plain",
        "X-Cache-Ts": String((metadata && metadata.ts) || 0),
        ...corsHeaders(request),
      },
    });
  }

  if (path === "/cache-status") {
    const v = await DASHBOARD_CACHE.get("prewarm_status");
    return new Response(v || '{"runAt":0,"results":{}}', {
      status: 200,
      headers: { "Content-Type": "application/json", ...corsHeaders(request) },
    });
  }

  if (path === "/admin/prewarm" && url.searchParams.get("secret") === PREWARM_SECRET) {
    const results = await runPrewarm();
    return new Response(JSON.stringify(results, null, 2), {
      status: 200,
      headers: { "Content-Type": "application/json", ...corsHeaders(request) },
    });
  }

  if (path.startsWith("/smaregi/")) {
    const subPath = path.slice(9);
    try {
      const { status, body, contentType } = await smaregiProxy(subPath, url.search);
      return new Response(body, {
        status,
        headers: { "Content-Type": contentType, ...corsHeaders(request) },
      });
    } catch (e) {
      return new Response(JSON.stringify({ error: String(e) }), {
        status: 502,
        headers: { "Content-Type": "application/json", ...corsHeaders(request) },
      });
    }
  }

  if (!path.startsWith("/api/")) {
    return new Response("Not found", { status: 404 });
  }

  const mbUrl = MB_BASE + path + url.search;
  const body = request.method === "POST" ? (await request.text() || "{}") : null;
  const mbResp = await fetch(mbUrl, {
    method: request.method,
    headers: { "X-Api-Key": MB_API_KEY, "Content-Type": "application/json" },
    body: body,
  });

  const respBody = await mbResp.text();
  return new Response(respBody, {
    status: mbResp.status,
    headers: {
      "Content-Type": mbResp.headers.get("Content-Type") || "application/json",
      ...corsHeaders(request),
    },
  });
}
