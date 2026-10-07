---
name: indeed-search
version: 1.0.0
description: >
  Use this skill to search live job listings across Indeed (India, Gulf, US, UK, Remote)
  or look up a specific Indeed posting. Trigger phrases: find job on indeed, indeed job search,
  indeed vacancies, indeed jobs in India, indeed jobs in Dubai.
context: fork
allowed-tools: Bash(bun run .agents/skills/indeed-search/cli/src/cli.ts *)
---

# Indeed Job Search Skill

Search live job listings from Indeed's public job boards across **India, Gulf region, Europe, US**, and remote.

## Commands

### Search job listings

```bash
bun run .agents/skills/indeed-search/cli/src/cli.ts search --location "<place>" [flags]
```

Flags:
- `--location <text>` / `-l <text>` — Location (e.g. `"Kanpur, UP"`, `"Dubai"`, `"India"`).
- `--query <text>` / `-q <text>` — Keywords (e.g. `"Operations Manager"`, `"Supply Chain"`).
- `--limit <n>` / `-n <n>` — Result cap.
- `--format json|table|plain` — Output format.

### Fetch job detail

```bash
bun run .agents/skills/indeed-search/cli/src/cli.ts detail <id|url> [--format json|plain]
```

## Usage examples

```bash
bun run .agents/skills/indeed-search/cli/src/cli.ts search -q "Operations Manager" -l "Kanpur, UP" --format table
bun run .agents/skills/indeed-search/cli/src/cli.ts search -q "Warehouse Manager" -l "Dubai" --format table
```
