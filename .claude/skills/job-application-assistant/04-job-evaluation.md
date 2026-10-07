# Job Evaluation Framework

## Scoring Dimensions

Evaluate each job posting against these five dimensions:

### 1. Technical Skills Match (0-100)
How well do the required/preferred skills align with the candidate's capabilities?

| Score | Meaning |
|-------|---------|
| 80-100 | Core requirements are primary skills |
| 60-79 | Most requirements match, 1-2 gaps that are learnable |
| 40-59 | Partial match, significant upskilling needed |
| 0-39 | Fundamental mismatch |

**Strong match areas:** Operations Management, Warehouse & Inventory Management, Supply Chain Coordination, Cash Handling & Reconciliation, Cost Control, B2B Corporate Sales, Budgeting & P&L Management.
**Moderate match areas:** Logistics Scheduling, Procurement & Purchasing, Vendor & Contract Negotiation, CRM platforms, AI Workflow Automation (n8n/Make), Prompt Engineering, Data Analysis (Microsoft Excel/Google Sheets).
**Weak match areas:** Production-grade software development (e.g. Java, C++ backend development), specialized enterprise ERP platforms like SAP (though easily adaptable to local WMS/ERP platforms).

### 2. Experience Match (0-100)
Does work history align with what they're looking for?

| Score | Meaning |
|-------|---------|
| 80-100 | Direct experience in the same domain and role type (10+ years) |
| 60-79 | Related experience, transferable skills clear |
| 40-59 | Adjacent experience, would need to make the case |
| 0-39 | Unrelated experience |

**Strong:** Cold Chain & Cold Storage Operations, Franchise Operations Management, B2B Corporate Fleet/Automotive Sales.
**Moderate:** FMCG logistics, 3PL distribution, food processing operations, retail warehousing, and general agricultural supply chain.
**Entry-level / Weak:** Full-stack software engineering or pure technical coding positions.

### 3. Behavioral/Culture Fit (0-100)
Does the role and company culture match the behavioral profile?

| Score | Meaning |
|-------|---------|
| 80-100 | Culture strongly matches behavioral preferences (high ownership, builder mode) |
| 60-79 | Mixed signals but mostly compatible |
| 40-59 | Some friction areas (heavy bureaucracy, micro-management) |
| 0-39 | Significant culture mismatch |

**Red flags to research:** Extreme bureaucracy, departments with high turnover, micromanagement cultures, lack of authority to optimize processes, or environments hostile to digital/AI adoption.

### 4. Location & Logistics (Pass/Fail + Notes)
- Within commute range (Kanpur/NCR): PASS (ideal)
- Relocation within India (Bengaluru, Mumbai, Pune, etc.): PASS
- Gulf countries (UAE, KSA, Qatar, Oman, etc.) with visa/relocation support: PASS
- Requires daily commute beyond reasonable range without relocation: FAIL

### 5. Career Alignment & Motivation (0-100)
Does this role advance career goals and contain tasks that energize?

| Score | Meaning |
|-------|---------|
| 80-100 | Strongly aligned with career direction, clear growth path |
| 60-79 | Good role but only partially aligned with long-term goals |
| 40-59 | Decent job but doesn't build toward career goals |
| 0-39 | Dead end or backwards step |

**Career goals:**
- Transition to senior corporate leadership roles (e.g., Operations Manager, Plant Head, Supply Chain Director) in logistics, cold chain, or agri-business.
- Apply AI and automation tools directly to business operations to eliminate manual work and improve decision-making.
- Expand footprints into high-growth regions (India nationwide or the Gulf).

**Motivation filter:** Evaluate not just whether you *can* do the tasks, but whether the tasks will *energize* you. Consider:
- Tasks that energize: Greenfield setup, optimizing warehouses to reduce cost/wastage, negotiating major vendor/supplier contracts, implementing BI dashboards and AI reporting, leading cross-functional teams.
- Tasks that drain: Repetitive manual data entry, processing invoices without system optimization, micromanaging staff on routine tasks, attending endless meetings with no decision-making power.

**Life situation alignment:**
- **Security**: Seeking stable, growth-oriented corporate roles with solid compensation structures.
- **Flexibility**: Open to domestic and international relocation for the right leadership opportunity.
- **Professional development**: Highly motivated to lead digital transformations in legacy supply chains.

### 6. Salary Benchmark (Optional)

If the salary lookup tool is configured (`salary_data.json` exists), look up the company:
```
python salary_lookup.py "<Company Name>" --json
```

If a city is known from the posting, add `--city "<City>"` to narrow results.

If the salary tool is not configured, skip this section.

---

## Output Format

Present the evaluation as:

```
## Job Fit Evaluation: [Role] at [Company]

| Dimension | Score | Notes |
|-----------|-------|-------|
| Technical Skills | XX/100 | [brief note] |
| Experience Match | XX/100 | [brief note] |
| Behavioral Fit | XX/100 | [brief note] |
| Location | PASS/FAIL | [brief note] |
| Career Alignment | XX/100 | [brief note] |

**Overall Score: XX/100** (weighted average of scored dimensions)

### Verdict: [Strong Fit / Good Fit / Moderate Fit / Weak Fit / Poor Fit]

### Key Strengths for This Role
- [bullet points]

### Gaps to Address
- [bullet points]

### Recommendation
[1-2 sentences: apply/skip/apply with caveats]

### Company Research Checklist
- [ ] Checked company website (mission, values, recent news)
- [ ] Checked review sites (Glassdoor, AmbitionBox, etc.)
- [ ] Checked LinkedIn for team size, recent hires, connections
- [ ] Checked media for restructuring, growth, or workplace issues
- [ ] Identified network contacts who may know the team/manager
```

## Weighting
- Technical Skills: 30%
- Experience Match: 25%
- Behavioral Fit: 15%
- Career Alignment: 30%

(Location is pass/fail, not weighted)

## Thresholds
- **Strong Fit** (75+): Definitely apply, tailor everything
- **Good Fit** (60-74): Apply, address gaps in cover letter
- **Moderate Fit** (45-59): Consider carefully, discuss with user
- **Weak Fit** (30-44): Probably skip unless strategic reasons
- **Poor Fit** (<30): Skip
