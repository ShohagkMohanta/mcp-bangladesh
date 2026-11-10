# mcp-bangladesh

Public data in Bangladesh is mostly locked inside scanned PDFs, broken Bijoy tables, or `.gov.bd` portals that time out outside local BDIX networks.

This repo runs Python scrapers on GitHub Actions every 2 hours, cleans the output into static JSON files under `data/`, and serves them through a Cloudflare Worker supporting both MCP (JSON-RPC 2.0 over HTTP) and standard REST endpoints.

Live server: https://mcp.shohag.one

## Endpoints

| Route | MCP Tool | Description |
| :--- | :--- | :--- |
| `/api/health` | `get_dghs_health_stats` | DGHS daily dengue (8 divisions, 64 districts) and measles numbers parsed from HEOC PDF bulletins |
| `/api/rivers` | `get_river_water_levels` | FFWC / BWDB observed water levels and danger thresholds across 44 stations |
| `/api/weather` | `get_bd_weather` | Temperature, humidity, wind speed, and 24h rain across 15 districts |
| `/api/air` | `get_air_quality` | US AQI, PM2.5, PM10, NO2, and ozone across 13 cities |
| `/api/notices` | `get_gov_notices` | Latest circulars from DSHE, SHED, MOF, BPSC, PLANDIV, and DPE |
| `/api/economy` | `get_bd_economy_indicators` | Bangladesh Bank USD/BDT reference rates, CPI inflation, and TCB retail reports |
| `/api/power` | `get_bpdb_power_generation` | BPDB plant-wise day peak and evening peak MW generation |
| `/api/catalog` | `get_bd_geography_catalog` | 8 divisions, 64 districts, and major river profiles |

## MCP Setup

For Claude Desktop, Cursor, or Windsurf, add the remote endpoint to your config:

```json
{
  "mcpServers": {
    "mcp-bangladesh": {
      "url": "https://mcp.shohag.one/mcp"
    }
  }
}
```
