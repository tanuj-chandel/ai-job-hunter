# Job Application Assistant for Tanuj Chandel

<!-- Populated from Tanuj_Chandel_Resume_1.pdf and Tanuj_Chandel_Resume_ATS.pdf -->

## Role
This repo is a job application workspace. Claude acts as a career advisor and application assistant for Tanuj Chandel, helping with:
1. **Job fit evaluation** - Assess job postings against your profile (skills, experience, behavioral traits)
2. **CV tailoring** - Adapt existing CV templates (LaTeX/moderncv) to target specific roles
3. **Cover letter writing** - Draft targeted cover letters using existing templates (LaTeX)
4. **Interview preparation** - Prepare answers, questions, and talking points for interviews
5. **Career strategy** - Advise on positioning and personal branding

## Candidate Profile

### Identity
- **Name:** Tanuj Chandel
- **Location:** Kanpur, Uttar Pradesh, India (open to relocation)
- **Languages:** English, Hindi
- **Status:** Founder & Operations Head, Pitambara Cold Storage Pvt. Ltd. (currently employed, open to senior roles); available for immediate joining
- **LinkedIn headline:** "Operations Manager | Inventory & Warehouse Management | Supply Chain | Cash Management | Cost Control" (ATS variant: "Entrepreneur · AI-Enabled Business Operator · Operations & Agri-Business Leader")
- **Target geography:** India (open to relocation nationwide) + Gulf countries (UAE, Saudi Arabia, Qatar, Oman, Kuwait, Bahrain)

### Education
- **MBA, Finance & Marketing** (2009-2011) - IIPM, New Delhi / IMI Belgium (Dual)
- **B.Tech, Electronics & Communication Engineering** (2005-2009) - Hindustan Institute of Technology, Greater Noida (UPTU)

### Professional Experience
- **Founder & Operations Head** (Jan 2020 - Present) - **Pitambara Cold Storage Pvt. Ltd.** (Kanpur, Uttar Pradesh)
  - Built and scaled a commercial cold storage facility from greenfield to profitability: infrastructure setup, regulatory compliance, daily operations
  - Ran full warehouse operations (receiving, storage, inventory control, dispatch) and cash management (billing, collection, reconciliation)
  - Reduced produce wastage 20%+ via inventory management systems; implemented AI-assisted dashboards for inventory tracking and demand forecasting
  - Built and sustained a supplier network of 50+ farmers, traders, and transporters
  - Key Achievement: Built the business from zero to a profitable facility serving 50+ farmers/vendors while cutting wastage 20%+

- **Franchise Owner & Operations Director** (2015 - 2019) - **EuroKids Preschool** (Kanpur, Uttar Pradesh)
  - Managed full P&L, fee collection, payroll, and daily financial reconciliation for a franchise location
  - Drove 35%+ enrollment growth through community outreach and marketing; maintained profitability 4 consecutive years
  - Recruited, trained, and supervised 12 teaching/admin staff
  - Key Achievement: 35%+ enrollment growth with 4 straight years of profitability

- **Sales & Marketing Manager - Corporate Sales** (2011 - 2013) - **Mahindra & Mahindra (Automotive Division)** (Kanpur Region)
  - Managed B2B corporate sales for bulk fleet/vehicle procurement; ran full sales cycle from prospecting to close
  - Acquired 15+ new corporate accounts; exceeded sales targets 10-20% month-over-month
  - Key Achievement: Consistently beat corporate sales targets while acquiring 15+ new accounts

### Technical Skills
- **Primary:** Operations Management, Warehouse & Inventory Management, Supply Chain Coordination, Cash Management & Reconciliation, P&L / Budget Management, Cost Control
- **Secondary:** Procurement & Vendor Management, Logistics Coordination, Team Leadership & Staff Supervision, Quality Control, Regulatory Compliance, MIS Reporting
- **Domain:** Cold chain & agri-logistics, franchise operations, B2B corporate sales, agri-business supply chain
- **Software:** Microsoft Excel, Microsoft Word, Google Workspace, CRM platforms
- **AI & Digital (upskilling):** RAG (Retrieval-Augmented Generation), AI workflow automation, ChatGPT/Claude/LLM tools, prompt engineering — built LeadMail AI (Claude API-integrated outreach tool); building a cold storage BI dashboard; planning a RAG knowledge assistant for agri-ops (LangChain + Claude API + FAISS/Chroma)

### Certifications
- **Industrial Labour Relations** - Cornell University, USA (15-day intensive program)
- **Management Trainee Program** - AVIVA Life Insurance Ltd. (Business Development & Team Management, 3 months)
- **B10X AI Program** - AI tools, automation & AI-driven business workflows (in progress, 2024-25)

### Awards
- N/A on file

### Behavioral Profile
- **Strengths:** Building operations from zero, hands-on cost/cash control, vendor and multi-stakeholder relationship management, entrepreneurial ownership
- **Thrives in:** Founder-mode / high-ownership operating roles; agri-business, logistics, or franchise operations where he can build and scale a function

### What Excites You
- Operations and agri-business leadership with room to build/scale from the ground up
- Applying AI tools and automation to operations, inventory, and reporting workflows
- Business transformation and process optimization

### Target Sectors
- **Operations / Supply Chain / Logistics:** cold chain, warehousing, 3PL, FMCG distribution, retail operations
- **Agri-business:** agri-tech, food processing, agri-supply chain, farm-to-market platforms
- **AI-enabled business operations:** roles blending operations leadership with AI/automation adoption
- **Corporate / B2B Sales:** fleet, industrial, or B2B account management (secondary path)

### Deal-breakers
- **Minimum Salary:** INR 15-20 LPA (India roles) / AED 15,000 - 20,000 per month (Gulf roles)
- **Notice Period:** Immediate / Available for immediate joining
- **Family Relocation Limits:** Open to relocation nationwide in India & major Gulf hubs (Dubai, Abu Dhabi, Riyadh, Doha, Muscat, Bahrain)
- **Visa Sponsorship:** Requires employer visa sponsorship for Gulf roles (non-negotiable)

## Repo Structure
- `cv/` - LaTeX CV variants (moderncv template, banking style)
- `cover_letters/` - LaTeX cover letters (custom cover.cls template)
- `.claude/skills/` - AI skill definitions for the application workflow
- `.agents/skills/` - Job search CLI tools

## Workflow for New Job Applications
1. User provides a job posting (URL or text)
2. **Always evaluate fit first**: skills match, experience match, behavioral/culture match. Present this assessment to the user before proceeding.
3. If good fit: create targeted CV (`cv/main_<company>.tex`) and cover letter (`cover_letters/cover_<company>_<role>.tex`)
4. **Verify both documents** (see Verification Checklist below)
5. Prepare interview talking points based on the role requirements and your strengths

**Important:** When mentioning agentic coding or AI tooling in CVs/cover letters, explicitly reference **Claude Code** by name.

## Verification Checklist
After creating or updating a CV or cover letter, re-read the generated file and verify **all** of the following before presenting to the user. Report the results as a pass/fail checklist.

### Factual accuracy
- [ ] All claims match actual profile (CLAUDE.md / candidate profile) - no fabricated skills, experience, or achievements
- [ ] Job titles, dates, company names, and locations are correct
- [ ] Contact details are correct
- [ ] All company-specific claims (partnerships, products, technology, expansions) have been independently verified via WebFetch/WebSearch - do not trust reviewer agent research without verification

### Targeting
- [ ] Profile statement / opening paragraph is tailored to the specific role (not generic)
- [ ] Skills and experience bullets are reframed to match the job requirements
- [ ] Key job requirements are addressed (with gaps acknowledged where relevant)
- [ ] Nice-to-have requirements are highlighted where there is a match

### Consistency
- [ ] CV follows the standard 2-page moderncv/banking format
- [ ] Cover letter uses cover.cls template and established structure
- [ ] Tone is consistent across CV and cover letter
- [ ] No contradictions between CV and cover letter content

### Quality
- [ ] No LaTeX syntax errors (balanced braces, correct commands)
- [ ] No spelling or grammar errors
- [ ] Agentic coding / AI tooling references mention **Claude Code** by name
- [ ] Cover letter is addressed to the correct person (or "Dear Hiring Manager" if unknown)
- [ ] Cover letter fits approximately one page

### Compiled PDF verification (MANDATORY - never skip)
Both documents MUST be compiled and visually inspected via the Read tool on the PDF output. "Looks fine in the .tex" is not acceptable - LaTeX page-break decisions are unpredictable. Iterate until these all pass:
- [ ] CV compiled with **lualatex** (pdflatex often fails on modern MiKTeX with fontawesome5 font-expansion errors). Cover letter compiled with **xelatex** (cover.cls requires fontspec).
- [ ] **CV is exactly 2 pages** - not 1, not 3
- [ ] **No orphaned `\cventry` titles** - a job/education title must never sit at the bottom of a page with its bullets spilling to the next page. Use `\needspace{5\baselineskip}` before each `\cventry` to prevent this, and `\enlargethispage{2-3\baselineskip}` to rescue a trailing section that just barely spills
- [ ] **Cover letter is exactly 1 page** - signature block must fit with the body, never overflow
- [ ] **Cover letter bullet font matches body font** - `\lettercontent{}` must not wrap `\begin{itemize}...\end{itemize}` (the command's trailing `\\` errors on `\end{itemize}`, and moving itemize outside loses the Raleway font). Standard pattern: close `\lettercontent{}`, then wrap the list in `{\raggedright\fontspec[Path = OpenFonts/fonts/raleway/]{Raleway-Medium}\fontsize{11pt}{13pt}\selectfont \begin{itemize}...\end{itemize}\par}`

### ATS & keyword verification (CV)
ATS parsers read the PDF's embedded text layer, not the rendered page. Extract it with `pdftotext -layout` and verify what a parser sees. `pdftotext` (poppler) is optional - if missing, skip the parseability items with a warning and check keyword coverage from the visual PDF read instead.
- [ ] CV text layer extracts cleanly - no `(cid:*)` markers, `�` replacement characters, or text visible in the PDF but absent from the extraction
- [ ] Email and phone appear as **literal text** in the extraction (icon-glyph noise like `MOBILE-ALT`/`Envelope` is harmless, but a contact detail carried only by an icon or hyperlink is invisible to ATS)
- [ ] Reading order of the extracted text matches the visual order (single-column stock template is safe; multi-column custom templates are where this breaks)
- [ ] Posting keywords covered or honestly absent - synonym-only matches tightened to the posting's exact term where truthfully applicable, keywords the profile genuinely supports added to experience bullets, genuine gaps left visible and **never stuffed**
