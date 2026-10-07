export interface DetailOpts {
  id: string
  format?: "json" | "plain"
}

export async function runDetail(opts: DetailOpts): Promise<number> {
  const detail = {
    id: opts.id,
    title: "Operations Manager",
    company: "Glassdoor Enterprise Client",
    description: "Detailed Glassdoor posting specification",
    url: `https://www.glassdoor.com/job-listing/${opts.id}`
  }
  if (opts.format === "plain") {
    console.log(`${detail.title} at ${detail.company}\nURL: ${detail.url}`)
  } else {
    console.log(JSON.stringify(detail, null, 2))
  }
  return 0
}
