---
name: naukri-search
version: 1.0.0
description: >
  Use this skill to search live job listings across Naukri.com (India's largest job portal).
  Ideal for searching operations, supply chain, warehousing, and corporate sales roles in Kanpur,
  Delhi NCR, Mumbai, Bengaluru, and across India. Trigger phrases: search naukri, naukri jobs,
  find jobs on naukri, naukri vacancies in India.
context: fork
allowed-tools: Bash(bun run .agents/skills/naukri-search/cli/src/cli.ts *)
---

# Naukri.com Job Search Skill

Search live job listings from Naukri.com — India's #1 job portal for mid-to-senior operations, logistics, supply chain, and management positions.

## Commands

```bash
bun run .agents/skills/naukri-search/cli/src/cli.ts search -q "Operations Manager" -l "Kanpur" --format table
bun run .agents/skills/naukri-search/cli/src/cli.ts detail <id|url> --format plain
```
