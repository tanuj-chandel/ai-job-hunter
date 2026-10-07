---
name: bayt-search
version: 1.0.0
description: >
  Use this skill to search live job listings across Bayt.com (the leading job site in the Middle East & Gulf).
  Ideal for finding operations, supply chain, logistics, and warehouse management positions in Dubai, Abu Dhabi,
  Riyadh, Jeddah, Qatar, and Gulf region. Trigger phrases: search bayt, bayt jobs, bayt vacancies in Dubai, bayt jobs in Saudi Arabia.
context: fork
allowed-tools: Bash(bun run .agents/skills/bayt-search/cli/src/cli.ts *)
---

# Bayt.com Job Search Skill

Search live job listings from Bayt.com — the Middle East & Gulf region's #1 job portal for senior operations, supply chain, and logistics positions.

## Commands

```bash
bun run .agents/skills/bayt-search/cli/src/cli.ts search -q "Operations Manager" -l "Dubai" --format table
bun run .agents/skills/bayt-search/cli/src/cli.ts detail <id|url> --format plain
```
