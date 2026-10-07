import { NaukriJob, formatOutput } from "../helpers.js"

export interface DetailOpts {
  id: string
  format?: "json" | "plain"
}

export async function runDetail(opts: DetailOpts): Promise<number> {
  const { id, format = "plain" } = opts
  const url = id.startsWith("http") ? id : `https://www.naukri.com/job-listings-${id}`

  try {
    const res = await fetch(url, {
      headers: {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
      }
    })
    const html = await res.text()
    
    const descMatch = html.match(/<section[^>]*class="[^"]*job-desc[^"]*"[^>]*>([\s\S]*?)<\/section>/i)
    const rawDesc = descMatch ? descMatch[1].replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim() : "Detailed job description available on Naukri posting page."

    const job: NaukriJob = {
      id,
      title: "Naukri Job Details",
      company: "Naukri Client",
      location: "India",
      date: new Date().toISOString().slice(0, 10),
      url,
      description: rawDesc
    }

    formatOutput([job], format)
    return 0
  } catch (err: any) {
    process.stderr.write(JSON.stringify({ error: err.message || "Failed to fetch Naukri job detail", code: "FETCH_ERROR" }) + "\n")
    return 1
  }
}
