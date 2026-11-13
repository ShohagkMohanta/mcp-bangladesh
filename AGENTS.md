# AGENTS.md: mcp-bangladesh (Bangladesh's First National Public Data MCP Server)

Reference guide for AI coding agents and LLM crawlers working with `mcp-bangladesh`, Bangladesh's first national public data Model Context Protocol (MCP) server and open REST API combining 8 live government datasets.

Base URL: `https://mcp.shohag.one`
MCP Endpoint (JSON-RPC 2.0 over HTTP): `https://mcp.shohag.one/mcp`
LLMs Text Index: `https://mcp.shohag.one/llms.txt`
GitHub Repository: `https://github.com/ShohagkMohanta/mcp-bangladesh`

## REST Routes (GET, No Auth)

- `/api/health` : DGHS dengue cases and deaths (8 divisions, 64 districts) and measles division totals parsed from HEOC PDF bulletins.
- `/api/rivers` : FFWC / BWDB water levels, danger thresholds, and flood status across 44 stations.
- `/api/weather` : Current temperature, humidity, wind speed, and daily rain across 15 districts.
- `/api/air` : US AQI, PM2.5, PM10, NO2, and ozone readings across 13 cities.
- `/api/notices` : 48 latest notices and circulars from DSHE, SHED, MOF, BPSC, PLANDIV, and DPE.
- `/api/economy` : Bangladesh Bank USD/BDT exchange rates, CPI inflation, and TCB retail price reports.
- `/api/power` : BPDB daily power plant MW output (day peak and evening peak) across 40 plants.
- `/api/catalog` : Static directory of 8 divisions, 64 districts, and 15 major rivers.

## MCP Tools

1. `get_dghs_health_stats`
   - Optional arg: `location` (string, division or district name, e.g. "Dhaka", "Bogura")
2. `get_river_water_levels`
   - Optional arg: `query` (string, river, station, basin, or district name)
3. `get_bd_weather`
   - Optional arg: `district` (string, district or division name)
4. `get_air_quality`
   - Optional arg: `city` (string, city or division name)
5. `get_gov_notices`
   - Optional arg: `agency` (string, agency code like "DSHE", "BPSC", "MOF" or search keyword)
6. `get_bd_economy_indicators`
   - Args: none
7. `get_bpdb_power_generation`
   - Optional arg: `plant` (string, power plant name)
8. `get_bd_geography_catalog`
   - Optional arg: `search` (string, river or district name)
