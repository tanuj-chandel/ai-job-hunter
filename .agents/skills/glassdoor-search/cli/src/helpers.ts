export interface GlassdoorJob {
  id: string
  title: string
  company: string
  location: string
  date: string
  url: string
}

export function formatOutput(jobs: GlassdoorJob[], format: "json" | "table" | "plain"): void {
  if (format === "json") {
    process.stdout.write(JSON.stringify({ count: jobs.length, results: jobs }, null, 2) + "\n")
    return
  }
  if (format === "table") {
    console.table(jobs)
    return
  }
  for (const j of jobs) {
    console.log(`[${j.id}] ${j.title} — ${j.company} (${j.location}) -> ${j.url}`)
  }
}
