export interface BaytJob {
  id: string
  title: string
  company: string
  location: string
  date: string
  url: string
  description?: string
}

export function formatOutput(results: BaytJob[], format: 'json' | 'table' | 'plain') {
  if (format === 'table') {
    if (results.length === 0) {
      console.log('No jobs found.')
      return
    }
    console.log(`ID\tTITLE\tCOMPANY\tLOCATION\tURL`)
    console.log(`--------------------------------------------------------------------------------`)
    results.forEach(j => {
      console.log(`${j.id}\t${j.title.slice(0, 30)}\t${j.company.slice(0, 20)}\t${j.location.slice(0, 20)}\t${j.url}`)
    })
  } else if (format === 'plain') {
    results.forEach(j => {
      console.log(`TITLE: ${j.title}`)
      console.log(`COMPANY: ${j.company}`)
      console.log(`LOCATION: ${j.location}`)
      console.log(`URL: ${j.url}`)
      if (j.description) console.log(`DESCRIPTION:\n${j.description}`)
      console.log(`---\n`)
    })
  } else {
    console.log(JSON.stringify({ meta: { count: results.length, page: 1 }, results }, null, 2))
  }
}
