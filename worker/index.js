const REPO_RAW_BASE = "https://raw.githubusercontent.com/ShohagkMohanta/mcp-bangladesh/main/data";

const FILES = {
  health: "dengue_live.json",
  rivers: "rivers_live.json",
  weather: "weather_live.json",
  air: "air_quality.json",
  notices: "gov_notices.json",
  economy: "economy_live.json",
  power: "power_grid.json",
  catalog: "bd_catalog.json"
};

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, Authorization, Mcp-Session-Id"
};

const SPELLING_ALIASES = {
  "bogra": "bogura",
  "chittagong": "chattogram",
  "comilla": "cumilla",
  "barisal": "barishal",
  "jessore": "jashore",
  "chapai nawabganj": "chapainawabganj",
  "nawabganj": "chapainawabganj",
  "coxs bazar": "cox's bazar",
  "coxsbazar": "cox's bazar",
  "maulvibazar": "moulvibazar",
  "brahmanbaria": "brahmanbaria",
  "bbaria": "brahmanbaria",
  "netrakona": "netrokona",
  "jhalokathi": "jhalokati",
  "khagrachari": "khagrachhari",
  "laxmipur": "lakshmipur"
};

function normQuery(raw) {
  let q = (raw || "").toLowerCase().trim();
  if (!q) return "";
  for (const [oldName, newName] of Object.entries(SPELLING_ALIASES)) {
    if (q === oldName || q.includes(oldName)) {
      q = q.replace(oldName, newName);
    }
  }
  return q;
}

async function fetchDataset(key, env) {
  const base = (env && env.DATA_BASE_URL) ? env.DATA_BASE_URL : REPO_RAW_BASE;
  const url = `${base}/${FILES[key]}`;
  const headers = { "User-Agent": "mcp-bangladesh" };

  if (env && env.GITHUB_TOKEN) {
    headers["Authorization"] = `Bearer ${env.GITHUB_TOKEN}`;
  }

  const res = await fetch(url, {
    headers,
    cf: { cacheTtl: 900, cacheEverything: true }
  });

  if (!res.ok) {
    throw new Error(`upstream ${key} returned ${res.status}`);
  }
  return await res.json();
}

const TOOL_ANNOTATIONS = {
  readOnlyHint: true,
  destructiveHint: false,
  idempotentHint: true,
  openWorldHint: false
};

const TOOLS = [
  {
    name: "get_dghs_health_stats",
    description: "Retrieve Bangladesh DGHS dengue (8 divisions, 64 districts) and measles surveillance metrics parsed from official HEOC PDF bulletins. Use when asked about dengue cases, hospitalizations, deaths, or measles outbreaks in Bangladesh. Read-only, no authentication required, updated every 2 hours. Returns report_date, 24h new cases/deaths, currently admitted patients, and cumulative totals.",
    annotations: TOOL_ANNOTATIONS,
    inputSchema: {
      type: "object",
      additionalProperties: false,
      properties: {
        location: {
          type: "string",
          description: "Optional division or district name filter (case-insensitive substring match; supports legacy spellings such as 'Bogra' or 'Chittagong'). Omit to return all 8 divisions and 64 districts."
        }
      }
    }
  },
  {
    name: "get_river_water_levels",
    description: "Retrieve observed water levels, danger thresholds, flood margins, and flood status across 44 Bangladesh river stations from FFWC/BWDB. Use for live hydrology, flood monitoring, or river danger checks. For static river lengths and origins without live water levels, use get_bd_geography_catalog instead. Read-only, updated every 2 hours. Returns station name, river, basin, district, water_level_m, danger_level_m, margin_m, and status (NORMAL, WARNING, ABOVE_DANGER).",
    annotations: TOOL_ANNOTATIONS,
    inputSchema: {
      type: "object",
      additionalProperties: false,
      properties: {
        query: {
          type: "string",
          description: "Optional filter matching river name, monitoring station, basin (Brahmaputra, Ganges, Meghna, South Eastern Hill), or district. Omit to return all 44 stations."
        }
      }
    }
  },
  {
    name: "get_bd_weather",
    description: "Retrieve current temperature, relative humidity, wind speed, and 24-hour precipitation across 15 Bangladesh districts. Use for meteorological conditions, rain forecasts, or heat checks. For air pollution and PM2.5 readings, use get_air_quality instead. Read-only, updated every 2 hours. Returns temp_c, humidity_pct, current_rain_mm, wind_kmh, today_max_c, today_min_c, and today_rain_sum_mm.",
    annotations: TOOL_ANNOTATIONS,
    inputSchema: {
      type: "object",
      additionalProperties: false,
      properties: {
        district: {
          type: "string",
          description: "Optional district or division name (case-insensitive; supports legacy spellings like 'Bogra' or 'Comilla'). Omit to return all 15 monitored districts."
        }
      }
    }
  },
  {
    name: "get_air_quality",
    description: "Retrieve US AQI scores, health categories, PM2.5, PM10, NO2, and ozone concentrations across 13 Bangladeshi cities. Use for air pollution, smog, or particulate matter queries. For temperature and rainfall, use get_bd_weather instead. Read-only, updated every 2 hours. Returns us_aqi, category (Good to Hazardous), pm2_5_ugm3, pm10_ugm3, no2_ugm3, and o3_ugm3.",
    annotations: TOOL_ANNOTATIONS,
    inputSchema: {
      type: "object",
      additionalProperties: false,
      properties: {
        city: {
          type: "string",
          description: "Optional city or division name filter (e.g. 'Dhaka', 'Narayanganj', 'Gazipur', 'Chattogram', 'Bogura'). Omit to return all 13 cities."
        }
      }
    }
  },
  {
    name: "get_gov_notices",
    description: "Search recent official circulars, press releases, and administrative notices from 6 Bangladesh ministries and directorates (DSHE, SHED, MOF, BPSC, PLANDIV, DPE). Use when tracking education ministry orders, BCS civil service circulars, or finance notifications. Read-only, updated every 2 hours. Returns agency_code, agency_name, Bengali/English notice title, published_date, and direct PDF/page URL.",
    annotations: TOOL_ANNOTATIONS,
    inputSchema: {
      type: "object",
      additionalProperties: false,
      properties: {
        agency: {
          type: "string",
          description: "Optional agency code ('DSHE', 'SHED', 'MOF', 'BPSC', 'PLANDIV', 'DPE') or title keyword filter. Omit to return all 48 latest notices across all 6 agencies."
        }
      }
    }
  },
  {
    name: "get_bd_economy_indicators",
    description: "Retrieve national macroeconomic indicators from Bangladesh Bank and the Trading Corporation of Bangladesh (TCB): interbank USD/BDT exchange rates (11 AM and 5 PM), point-to-point and 12-month average CPI inflation, and TCB Dhaka daily retail market price bulletin links. Use for currency exchange, inflation, or commodity market queries. Read-only, takes no parameters, and returns the complete national snapshot.",
    annotations: TOOL_ANNOTATIONS,
    inputSchema: {
      type: "object",
      additionalProperties: false,
      properties: {}
    }
  },
  {
    name: "get_bpdb_power_generation",
    description: "Retrieve daily electricity generation (installed/derated capacity MW, day-peak MW, and evening-peak MW) across 40 Bangladesh Power Development Board (BPDB) power plants. Use for national grid load, power plant output, or energy sector queries. Read-only, updated every 2 hours. Returns aggregate peak MW totals and plant-level generation records.",
    annotations: TOOL_ANNOTATIONS,
    inputSchema: {
      type: "object",
      additionalProperties: false,
      properties: {
        plant: {
          type: "string",
          description: "Optional power plant name substring filter (e.g. 'Payra', 'Rampal', 'Ashuganj', 'Kaptai'). Omit to return all 40 power plants and aggregate MW totals."
        }
      }
    }
  },
  {
    name: "get_bd_geography_catalog",
    description: "Lookup static reference profiles for Bangladesh's 8 administrative divisions, 64 districts, and 15 major transboundary/internal rivers (including Bengali script names, length in km, origin, outfall, and districts traversed). Use for administrative hierarchy or river geography reference. For live river water and flood danger levels, use get_river_water_levels instead. Read-only reference dataset.",
    annotations: TOOL_ANNOTATIONS,
    inputSchema: {
      type: "object",
      additionalProperties: false,
      properties: {
        search: {
          type: "string",
          description: "Optional district, division, or river name filter (supports legacy district spellings). Omit to return the full catalog of 8 divisions, 64 districts, and 15 river profiles."
        }
      }
    }
  }
];

async function callTool(name, args, env) {
  const p = args || {};

  if (name === "get_dghs_health_stats") {
    const data = await fetchDataset("health", env);
    const q = normQuery(p.location);
    if (!q) return data;
    return {
      updated_at: data.updated_at,
      dengue_report_date: data.dengue ? data.dengue.report_date : "",
      dengue_divisions: ((data.dengue && data.dengue.divisions) || []).filter(d => (d.division || "").toLowerCase().includes(q)),
      dengue_districts: ((data.dengue && data.dengue.districts) || []).filter(d => (d.district || "").toLowerCase().includes(q) || (d.division || "").toLowerCase().includes(q)),
      measles_divisions: ((data.measles && data.measles.divisions) || []).filter(d => (d.division || "").toLowerCase().includes(q))
    };
  }

  if (name === "get_river_water_levels") {
    const data = await fetchDataset("rivers", env);
    const rawQ = (p.query || "").toLowerCase().trim();
    const q = normQuery(p.query);
    if (!q) return data;
    const list = (data.stations || []).filter(s => {
      const hay = `${s.river || ""} ${s.station || ""} ${s.district || ""} ${s.basin || ""}`.toLowerCase();
      return hay.includes(q) || (rawQ && hay.includes(rawQ));
    });
    return { updated_at: data.updated_at, count: list.length, stations: list };
  }

  if (name === "get_bd_weather") {
    const data = await fetchDataset("weather", env);
    const q = normQuery(p.district);
    if (!q) return data;
    const list = (data.districts || []).filter(d =>
      (d.district || "").toLowerCase().includes(q) || (d.division || "").toLowerCase().includes(q)
    );
    return { updated_at: data.updated_at, districts: list };
  }

  if (name === "get_air_quality") {
    const data = await fetchDataset("air", env);
    const q = normQuery(p.city);
    if (!q) return data;
    const list = (data.cities || []).filter(c =>
      (c.city || "").toLowerCase().includes(q) || (c.division || "").toLowerCase().includes(q)
    );
    return { updated_at: data.updated_at, cities: list };
  }

  if (name === "get_gov_notices") {
    const data = await fetchDataset("notices", env);
    const q = (p.agency || "").toLowerCase().trim();
    if (!q) return data;
    const list = (data.notices || []).filter(n =>
      (n.agency_code || "").toLowerCase().includes(q) ||
      (n.agency_name || "").toLowerCase().includes(q) ||
      (n.title || "").toLowerCase().includes(q)
    );
    return { updated_at: data.updated_at, count: list.length, notices: list };
  }

  if (name === "get_bd_economy_indicators") {
    return await fetchDataset("economy", env);
  }

  if (name === "get_bpdb_power_generation") {
    const data = await fetchDataset("power", env);
    const q = (p.plant || "").toLowerCase().trim();
    if (!q) return data;
    const list = (data.plants || []).filter(x => (x.plant_name || "").toLowerCase().includes(q));
    return {
      updated_at: data.updated_at,
      sampled_day_peak_mw: data.sampled_day_peak_mw,
      sampled_evening_peak_mw: data.sampled_evening_peak_mw,
      plants: list
    };
  }

  if (name === "get_bd_geography_catalog") {
    const data = await fetchDataset("catalog", env);
    const q = normQuery(p.search);
    if (!q) return data;
    return {
      districts: (data.districts || []).filter(d => (d.district || "").toLowerCase().includes(q) || (d.division || "").toLowerCase().includes(q)),
      rivers: (data.major_rivers || []).filter(r => (r.name || "").toLowerCase().includes(q) || (r.key_districts || []).some(k => k.toLowerCase().includes(q)))
    };
  }

  throw new Error(`unknown tool: ${name}`);
}

function renderLlmsTxt(origin) {
  return `# mcp-bangladesh: Bangladesh's First National Public Data MCP Server & REST API

mcp-bangladesh (${origin}/mcp) is Bangladesh's first national public data Model Context Protocol (MCP) server and open REST API. It combines 8 live national government datasets into a single free, zero-auth endpoint for Claude, ChatGPT, Cursor, Windsurf, and AI agents.

MCP Endpoint (Streamable HTTP / JSON-RPC 2.0): ${origin}/mcp
One-Line CLI Install: npx add-mcp '${origin}/mcp'
GitHub Repository: https://github.com/ShohagkMohanta/mcp-bangladesh

REST Endpoints (GET):
- ${origin}/api/health  (DGHS dengue 8 divisions, 64 districts & measles)
- ${origin}/api/rivers  (FFWC/BWDB 44 river stations water & danger levels)
- ${origin}/api/weather (15 districts temperature, humidity, wind, rain)
- ${origin}/api/air     (13 cities US AQI, PM2.5, PM10, NO2, ozone)
- ${origin}/api/notices (48 latest circulars from DSHE, SHED, MOF, BPSC, PLANDIV, DPE)
- ${origin}/api/economy (Bangladesh Bank USD/BDT rates, CPI inflation, TCB reports)
- ${origin}/api/power   (BPDB 40 power plants day/evening peak MW)
- ${origin}/api/catalog (8 divisions, 64 districts, major river profiles)
`;
}

function renderRobotsTxt(origin) {
  return `User-agent: *
Allow: /

Sitemap: ${origin}/sitemap.xml
`;
}

function renderSitemapXml(origin) {
  return `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>${origin}/</loc><changefreq>hourly</changefreq><priority>1.0</priority></url>
  <url><loc>${origin}/llms.txt</loc><changefreq>daily</changefreq><priority>0.9</priority></url>
  <url><loc>${origin}/api/health</loc><changefreq>hourly</changefreq><priority>0.8</priority></url>
  <url><loc>${origin}/api/rivers</loc><changefreq>hourly</changefreq><priority>0.8</priority></url>
  <url><loc>${origin}/api/weather</loc><changefreq>hourly</changefreq><priority>0.8</priority></url>
  <url><loc>${origin}/api/air</loc><changefreq>hourly</changefreq><priority>0.8</priority></url>
  <url><loc>${origin}/api/notices</loc><changefreq>hourly</changefreq><priority>0.8</priority></url>
  <url><loc>${origin}/api/economy</loc><changefreq>hourly</changefreq><priority>0.8</priority></url>
  <url><loc>${origin}/api/power</loc><changefreq>hourly</changefreq><priority>0.8</priority></url>
  <url><loc>${origin}/api/catalog</loc><changefreq>weekly</changefreq><priority>0.7</priority></url>
</urlset>`;
}

function indexPage(origin) {
  const schema = {
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type": "WebSite",
        "@id": "https://mcp.shohag.one/#website",
        "url": origin,
        "name": "mcp-bangladesh",
        "publisher": {
          "@id": "https://shohag.one/#person"
        }
      },
      {
        "@type": [
          "SoftwareApplication",
          "WebAPI",
          "SoftwareSourceCode"
        ],
        "@id": "https://mcp.shohag.one/#api",
        "name": "mcp-bangladesh: Bangladesh's First National Public Data MCP Server",
        "alternateName": [
          "mcp-bangladesh",
          "Bangladesh National Public Data MCP Server & REST API",
          "Bangladesh MCP Server",
          "Bangladesh Public Data MCP Server",
          "Bangladesh First MCP Server"
        ],
        "url": origin,
        "documentation": "https://mcp.shohag.one/llms.txt",
        "applicationCategory": "DeveloperApplication",
        "operatingSystem": "All",
        "offers": { "@type": "Offer", "price": "0", "priceCurrency": "USD" },
        "author": {
          "@id": "https://shohag.one/#person"
        },
        "creator": {
          "@id": "https://shohag.one/#person"
        },
        "provider": {
          "@id": "https://shohag.one/#person"
        },
        "codeRepository": "https://github.com/ShohagkMohanta/mcp-bangladesh",
        "programmingLanguage": [
          "Python",
          "JavaScript"
        ],
        "description": "mcp-bangladesh is Bangladesh's first national public data Model Context Protocol (MCP) server and open REST API combining 8 live national government datasets into a free, zero-auth endpoint for Claude, ChatGPT, Cursor, Windsurf, and AI agents."
      },
      {
        "@type": "Person",
        "@id": "https://shohag.one/#person",
        "name": "Shohag Kumar Mohanta",
        "alternateName": "shohagkmohanta",
        "url": "https://shohag.one/",
        "image": "https://shohag.one/wp-content/uploads/2026/10/Shohag-Prof-Pic.jpg",
        "mainEntityOfPage": {
          "@type": "ProfilePage",
          "@id": "https://shohag.one/#profilepage"
        },
        "email": "mailto:contact@shohag.one",
        "jobTitle": "Software & AI Developer",
        "sameAs": [
          "https://shohag.one/",
          "https://github.com/ShohagkMohanta",
          "https://www.facebook.com/ShohagkMohanta/"
        ]
      },
      {
        "@type": "FAQPage",
        "mainEntity": [
          {
            "@type": "Question",
            "name": "What is Bangladesh's first national public data MCP server?",
            "acceptedAnswer": {
              "@type": "Answer",
              "text": `mcp-bangladesh (${origin}/mcp) is Bangladesh's first national public data Model Context Protocol (MCP) server and open REST API. It combines 8 live government datasets including DGHS dengue surveillance, FFWC river flood levels across 44 stations, BPDB power generation across 40 plants, 15 districts weather, 13 cities AQI, 6 ministry notice boards, Bangladesh Bank forex and inflation, and a national geography catalog.`
            }
          },
          {
            "@type": "Question",
            "name": "How to connect the Bangladesh MCP server to Claude, ChatGPT, or Cursor?",
            "acceptedAnswer": {
              "@type": "Answer",
              "text": `Add the remote Streamable HTTP endpoint ${origin}/mcp in Claude, ChatGPT, Cursor, or Windsurf, or run npx add-mcp '${origin}/mcp' in your terminal. No API key or authentication is required.`
            }
          }
        ]
      }
    ]
  };

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Bangladesh's First National Public Data MCP Server | mcp-bangladesh</title>
  <meta name="description" content="mcp-bangladesh is Bangladesh's first national public data Model Context Protocol (MCP) server and free REST API. Connect Claude, ChatGPT, and Cursor to 8 live Bangladesh government datasets (rivers, power, health, weather, AQI, notices, economy, geography).">
  <meta name="keywords" content="mcp bangladesh server, bangladesh mcp server, bangladesh's mcp server, bangladesh first mcp server, mcp-bangladesh, model context protocol bangladesh, bangladesh public data api">
  <link rel="canonical" href="${origin}/">
  <meta property="og:title" content="Bangladesh's First National Public Data MCP Server | mcp-bangladesh">
  <meta property="og:description" content="Free, zero-auth remote MCP server (${origin}/mcp) and REST API combining 8 live Bangladesh government datasets for AI assistants and developers.">
  <meta property="og:url" content="${origin}/">
  <meta property="og:type" content="website">
  <script type="application/ld+json">${JSON.stringify(schema)}</script>
  <style>
    body { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; max-width: 820px; margin: 36px auto; padding: 0 16px; color: #111; line-height: 1.5; font-size: 14px; }
    h1 { font-size: 20px; margin-bottom: 6px; }
    h2 { font-size: 15px; margin-top: 28px; border-bottom: 1px solid #ddd; padding-bottom: 4px; }
    p { margin: 6px 0 14px; color: #444; }
    table { width: 100%; border-collapse: collapse; margin: 10px 0; }
    th, td { border: 1px solid #ccc; padding: 7px 10px; text-align: left; }
    th { background: #f5f5f5; }
    pre { background: #f5f5f5; border: 1px solid #ccc; padding: 12px; overflow-x: auto; }
    a { color: #0055cc; text-decoration: none; }
    a:hover { text-decoration: underline; }
  </style>
</head>
<body>
  <h1>mcp-bangladesh: Bangladesh's First National Public Data MCP Server &amp; REST API</h1>
  <p><strong>mcp-bangladesh</strong> (<a href="${origin}/mcp">${origin}/mcp</a>) is Bangladesh's first national public data Model Context Protocol (MCP) server and open REST API, combining 8 live government datasets into a single free, zero-auth endpoint for Claude, ChatGPT, Cursor, Windsurf, and AI agents. (<a href="/llms.txt">/llms.txt</a> | <a href="https://github.com/ShohagkMohanta/mcp-bangladesh">GitHub</a>)</p>

  <h2>REST API Endpoints (8 Live National Datasets)</h2>
  <table>
    <tr><th>Route</th><th>Dataset</th><th>Source</th></tr>
    <tr><td><a href="/api/health">/api/health</a></td><td>Dengue (8 divs, 64 districts) &amp; Measles</td><td>DGHS Bulletins</td></tr>
    <tr><td><a href="/api/rivers">/api/rivers</a></td><td>River station water &amp; danger levels (44 stations)</td><td>FFWC / BWDB</td></tr>
    <tr><td><a href="/api/weather">/api/weather</a></td><td>District temperature, wind, rainfall (15 districts)</td><td>Open-Meteo / BMD Grid</td></tr>
    <tr><td><a href="/api/air">/api/air</a></td><td>City US AQI, PM2.5, PM10, NO2 (13 cities)</td><td>Open-Meteo CAMS</td></tr>
    <tr><td><a href="/api/notices">/api/notices</a></td><td>Ministry &amp; directorate circulars (48 notices)</td><td>DSHE, SHED, MOF, BPSC, PLANDIV, DPE</td></tr>
    <tr><td><a href="/api/economy">/api/economy</a></td><td>USD/BDT rates, CPI inflation, TCB reports</td><td>Bangladesh Bank &amp; TCB</td></tr>
    <tr><td><a href="/api/power">/api/power</a></td><td>Plant-wise MW generation (40 power plants)</td><td>BPDB</td></tr>
    <tr><td><a href="/api/catalog">/api/catalog</a></td><td>8 divisions, 64 districts, 15 major rivers</td><td>NRCC / BD Geo</td></tr>
  </table>

  <h2>MCP Client Config</h2>
  <pre>{
  "mcpServers": {
    "mcp-bangladesh": {
      "url": "${origin}/mcp"
    }
  }
}</pre>
  <p>CLI install: <code>npx add-mcp '${origin}/mcp'</code></p>

  <h2>MCP Tools (${TOOLS.length})</h2>
  <table>
    <tr><th>Tool Name</th><th>Argument</th></tr>
    <tr><td>get_dghs_health_stats</td><td>location (optional)</td></tr>
    <tr><td>get_river_water_levels</td><td>query (optional)</td></tr>
    <tr><td>get_bd_weather</td><td>district (optional)</td></tr>
    <tr><td>get_air_quality</td><td>city (optional)</td></tr>
    <tr><td>get_gov_notices</td><td>agency (optional)</td></tr>
    <tr><td>get_bd_economy_indicators</td><td>none</td></tr>
    <tr><td>get_bpdb_power_generation</td><td>plant (optional)</td></tr>
    <tr><td>get_bd_geography_catalog</td><td>search (optional)</td></tr>
  </table>
</body>
</html>`;
}

export default {
  async fetch(request, env) {
    if (request.method === "OPTIONS") {
      return new Response(null, { headers: CORS });
    }

    const url = new URL(request.url);
    const path = url.pathname.replace(/\/+$/, "") || "/";

    if (path === "/favicon.ico") {
      return new Response(null, { status: 204 });
    }

    if (path === "/robots.txt" && request.method === "GET") {
      return new Response(renderRobotsTxt(url.origin), {
        headers: { "Content-Type": "text/plain; charset=utf-8", ...CORS }
      });
    }

    if (path === "/sitemap.xml" && request.method === "GET") {
      return new Response(renderSitemapXml(url.origin), {
        headers: { "Content-Type": "application/xml; charset=utf-8", ...CORS }
      });
    }

    if ((path === "/llms.txt" || path === "/AGENTS.md") && request.method === "GET") {
      return new Response(renderLlmsTxt(url.origin), {
        headers: { "Content-Type": "text/plain; charset=utf-8", ...CORS }
      });
    }

    if (path === "/" && request.method === "GET") {
      return new Response(indexPage(url.origin), {
        headers: { "Content-Type": "text/html; charset=utf-8", ...CORS }
      });
    }

    if (path.startsWith("/api/") && request.method === "GET") {
      const key = path.replace("/api/", "");
      if (!FILES[key]) {
        return Response.json({ error: "not found" }, { status: 404, headers: CORS });
      }
      try {
        const data = await fetchDataset(key, env);
        return Response.json(data, {
          headers: { "Cache-Control": "public, max-age=900", ...CORS }
        });
      } catch (e) {
        return Response.json({ error: e.message }, { status: 502, headers: CORS });
      }
    }

    if (path === "/mcp") {
      if (request.method === "GET") {
        return Response.json({
          name: "mcp-bangladesh",
          version: "1.0.0",
          protocol: "mcp-streamable-http",
          tools: TOOLS.map(t => t.name)
        }, { headers: CORS });
      }

      if (request.method === "POST") {
        let body;
        try {
          body = await request.json();
        } catch {
          return Response.json({
            jsonrpc: "2.0",
            id: null,
            error: { code: -32700, message: "Parse error" }
          }, { status: 400, headers: CORS });
        }

        const { id, method, params } = body;

        if (method && method.startsWith("notifications/")) {
          return new Response(null, { status: 202, headers: CORS });
        }

        if (method === "initialize") {
          return Response.json({
            jsonrpc: "2.0",
            id,
            result: {
              protocolVersion: (params && params.protocolVersion) ? params.protocolVersion : "2024-11-05",
              capabilities: { tools: {}, resources: {}, prompts: {} },
              serverInfo: { name: "mcp-bangladesh", version: "1.0.0" }
            }
          }, { headers: CORS });
        }

        if (method === "ping") {
          return Response.json({ jsonrpc: "2.0", id, result: {} }, { headers: CORS });
        }

        if (method === "tools/list") {
          return Response.json({
            jsonrpc: "2.0",
            id,
            result: { tools: TOOLS }
          }, { headers: CORS });
        }

        if (method === "resources/list") {
      return Response.json({
        jsonrpc: "2.0",
        id,
        result: {
          resources: [
            { uri: `${url.origin}/api/health`, name: "dghs_health", description: "DGHS dengue cases, deaths, and measles division totals", mimeType: "application/json" },
            { uri: `${url.origin}/api/rivers`, name: "ffwc_rivers", description: "FFWC water levels and danger thresholds across 44 stations", mimeType: "application/json" },
            { uri: `${url.origin}/api/weather`, name: "bd_weather", description: "Temperature, humidity, wind, and daily rain across 15 districts", mimeType: "application/json" },
            { uri: `${url.origin}/api/air`, name: "bd_air_quality", description: "US AQI, PM2.5, PM10, NO2, and ozone across 13 cities", mimeType: "application/json" },
            { uri: `${url.origin}/api/notices`, name: "gov_notices", description: "Recent circulars from DSHE, SHED, MOF, BPSC, PLANDIV, and DPE", mimeType: "application/json" },
            { uri: `${url.origin}/api/economy`, name: "bd_economy", description: "Bangladesh Bank USD/BDT rates, CPI inflation, and TCB prices", mimeType: "application/json" },
            { uri: `${url.origin}/api/power`, name: "bpdb_power", description: "BPDB daily plant MW output for day peak and evening peak", mimeType: "application/json" },
            { uri: `${url.origin}/api/catalog`, name: "bd_catalog", description: "Static catalog of 8 divisions, 64 districts, and 15 rivers", mimeType: "application/json" }
          ]
        }
      }, { headers: CORS });
    }

    if (method === "resources/templates/list") {
      return Response.json({
        jsonrpc: "2.0",
        id,
        result: { resourceTemplates: [] }
      }, { headers: CORS });
    }

    if (method === "prompts/list") {
      return Response.json({
        jsonrpc: "2.0",
        id,
        result: {
          prompts: [
            {
              name: "bd_daily_briefing",
              description: "Summarize current dengue stats, river flood status, weather, AQI, and power output in Bangladesh",
              arguments: [
                { name: "location", description: "Optional division or district name (e.g. Dhaka, Bogura)", required: false }
              ]
            },
            {
              name: "bd_flood_check",
              description: "Check FFWC river danger levels and recent rainfall for a river basin or district",
              arguments: [
                { name: "query", description: "River, station, or district name (e.g. Jamuna, Sylhet)", required: false }
              ]
            }
          ]
        }
      }, { headers: CORS });
    }

    if (method === "prompts/get") {
      const name = params && params.name;
      const arg = (params && params.arguments && (params.arguments.location || params.arguments.query)) || "Bangladesh";
      return Response.json({
        jsonrpc: "2.0",
        id,
        result: {
          description: `Live public data check for ${arg}`,
          messages: [
            {
              role: "user",
              content: {
                type: "text",
                text: name === "bd_flood_check"
                  ? `Check FFWC river water levels and weather for ${arg} using get_river_water_levels and get_bd_weather, and highlight any stations near or above danger level.`
                  : `Give a concise public data briefing for ${arg} using the mcp-bangladesh tools covering dengue cases, river levels, weather, air quality, and power generation.`
              }
            }
          ]
        }
      }, { headers: CORS });
    }

        if (method === "tools/call") {
          try {
            const name = params && params.name;
            const args = (params && params.arguments) || {};
            const out = await callTool(name, args, env);
            return Response.json({
              jsonrpc: "2.0",
              id,
              result: {
                content: [{ type: "text", text: JSON.stringify(out, null, 2) }],
                isError: false
              }
            }, { headers: CORS });
          } catch (e) {
            return Response.json({
              jsonrpc: "2.0",
              id,
              result: {
                content: [{ type: "text", text: `Error: ${e.message}` }],
                isError: true
              }
            }, { headers: CORS });
          }
        }

        return Response.json({
          jsonrpc: "2.0",
          id: id ?? null,
          error: { code: -32601, message: `Method not found: ${method}` }
        }, { status: 404, headers: CORS });
      }
    }

    return Response.json({ error: "not found" }, { status: 404, headers: CORS });
  }
};