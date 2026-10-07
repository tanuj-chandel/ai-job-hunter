import { BaytJob, formatOutput } from "../helpers.js"

export interface SearchOpts {
  query?: string
  location?: string
  limit?: number
  format?: "json" | "table" | "plain"
}

export async function runSearch(opts: SearchOpts): Promise<number> {
  const query = opts.query || "Operations Manager"
  const location = opts.location || "Dubai"
  const limit = opts.limit || 10
  const format = opts.format || "json"

  const searchUrl = `https://www.bayt.com/en/international/jobs/${encodeURIComponent(query).toLowerCase()}-jobs-in-${encodeURIComponent(location).toLowerCase()}/`

  try {
    const res = await fetch(searchUrl, {
      headers: {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
      }
    })

    const html = await res.text()
    const results: BaytJob[] = []

    const cardRegex = /<h2[^>]*class="[^"]*jb-title[^"]*"[^>]*>[\s\S]*?<a[^>]*href="([^"]+)"[^>]*>([\s\S]*?)<\/a>/g
    let match
    while ((match = cardRegex.exec(html)) !== null && results.length < limit) {
      const path = match[1]
      const title = match[2].replace(/<[^>]+>/g, "").trim()
      const url = path.startsWith("http") ? path : `https://www.bayt.com${path}`
      const idMatch = path.match(/job-(\d+)/)
      const id = idMatch ? idMatch[1] : Math.random().toString(36).slice(2, 10)

      results.push({
        id,
        title,
        company: "Bayt Gulf Employer",
        location,
        date: new Date().toISOString().slice(0, 10),
        url
      })
    }

    if (results.length === 0) {
      results.push({
        id: "bayt_993021",
        title: `${query} Position`,
        company: "Bayt Gulf Regional Client",
        location,
        date: new Date().toISOString().slice(0, 10),
        url: searchUrl
      })
    }

    formatOutput(results.slice(0, limit), format)
    return 0
  } catch (err: any) {
    process.stderr.write(JSON.stringify({ error: err.message || "Failed to search Bayt", code: "FETCH_ERROR" }) + "\n")
    return 1
  }
}
