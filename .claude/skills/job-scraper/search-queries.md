# Search Queries for Job Scraper — Tanuj Chandel

## Search Sites

Primary:
- **linkedin.com/jobs** — via the `linkedin-search` CLI skill (`.agents/skills/linkedin-search`), country-agnostic, run once per target location below
- **naukri.com**, **shine.com**, **timesjobs.com** — via WebSearch `site:` filters (India job boards; no CLI skill shipped yet — candidates for `/add-portal`)
- **gulftalent.com**, **bayt.com**, **naukrigulf.com** — via WebSearch `site:` filters (Gulf job boards; candidates for `/add-portal`)

## Target Locations

Run the `linkedin-search` CLI once per location (or the top 4-5 most relevant per run to keep volume low per ToS):

**India:**
- "Kanpur, Uttar Pradesh, India" (home base)
- "Delhi NCR, India"
- "Mumbai, Maharashtra, India"
- "Bengaluru, Karnataka, India"
- "Pune, Maharashtra, India"

**Gulf:**
- "Dubai, United Arab Emirates"
- "Abu Dhabi, United Arab Emirates"
- "Riyadh, Saudi Arabia"
- "Doha, Qatar"
- "Muscat, Oman"

## Query Categories

### Priority 1: Operations & Supply Chain Leadership

Core role — direct match to 10+ years running operations end-to-end.

```
bun run .agents/skills/linkedin-search/cli/src/cli.ts search -q "Operations Manager" -l "<location>" --jobage 14
bun run .agents/skills/linkedin-search/cli/src/cli.ts search -q "Operations Head" -l "<location>" --jobage 14
bun run .agents/skills/linkedin-search/cli/src/cli.ts search -q "Supply Chain Manager" -l "<location>" --jobage 14
bun run .agents/skills/linkedin-search/cli/src/cli.ts search -q "Warehouse Manager" -l "<location>" --jobage 14
bun run .agents/skills/linkedin-search/cli/src/cli.ts search -q "General Manager Operations" -l "<location>" --jobage 14
```

### Priority 2: Cold Chain / Agri-Business

Direct domain expertise from Pitambara Cold Storage.

```
bun run .agents/skills/linkedin-search/cli/src/cli.ts search -q "Cold Chain Manager" -l "<location>" --jobage 30
bun run .agents/skills/linkedin-search/cli/src/cli.ts search -q "Cold Storage Operations" -l "<location>" --jobage 30
bun run .agents/skills/linkedin-search/cli/src/cli.ts search -q "Agri-business Manager" -l "<location>" --jobage 30
bun run .agents/skills/linkedin-search/cli/src/cli.ts search -q "Logistics Manager FMCG" -l "<location>" --jobage 30
```

### Priority 3: AI-Enabled Business Operations

Emerging pivot — operations leadership blended with AI/automation adoption (per ATS resume positioning).

```
bun run .agents/skills/linkedin-search/cli/src/cli.ts search -q "Business Operations AI" -l "<location>" --jobage 30
bun run .agents/skills/linkedin-search/cli/src/cli.ts search -q "Operations Transformation Manager" -l "<location>" --jobage 30
```

### Priority 4: Corporate / B2B Sales (secondary path)

Adjacent role from Mahindra & Mahindra experience — wider net.

```
bun run .agents/skills/linkedin-search/cli/src/cli.ts search -q "B2B Sales Manager" -l "<location>" --jobage 30
bun run .agents/skills/linkedin-search/cli/src/cli.ts search -q "Key Account Manager" -l "<location>" --jobage 30
```

## Location Filter

Since the target is deliberately broad (India nationwide + Gulf), do not filter out results by commute distance. Instead tag each result with:
- **India — home region** (Kanpur/UP/NCR): no relocation needed
- **India — relocation**: other Indian cities
- **Gulf — relocation + visa**: flag that these roles typically require employer visa sponsorship; note in the fit assessment whether the posting mentions sponsorship/relocation support

## Date Filter

Only include jobs posted within the last 14 days for Priority 1, last 30 days for Priority 2-4. If a posting date cannot be determined, include it but flag as "date unknown".

## Adapting Queries

If Tanuj specifies a focus area (e.g. "/scrape gulf" or "/scrape cold chain"), select the matching category/location subset and generate 2-3 custom queries for that focus rather than running the full matrix every time.
