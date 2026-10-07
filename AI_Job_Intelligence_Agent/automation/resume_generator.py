"""
ATS Resume Generator
Generates ATS-optimized customized resumes for each job
"""

import json
from typing import Dict, List, Any
from datetime import datetime
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ATSResumeGenerator:
    """Generate ATS-friendly customized resumes for job applications"""

    def __init__(self, profile_path: str = "database/master_profile.json"):
        """Initialize resume generator with candidate profile"""
        self.profile = self.load_profile(profile_path)

    def load_profile(self, profile_path: str) -> Dict[str, Any]:
        """Load master profile"""
        try:
            with open(profile_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Profile not found: {profile_path}")
            return {}

    def generate_resume_for_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Generate customized ATS resume for specific job"""

        job_title = job.get('title', '')
        job_description = job.get('description', '')
        company = job.get('company', '')
        required_skills = job.get('required_skills', [])

        # Extract relevant keywords from job description
        keywords = self.extract_keywords(job_description)

        # Customize resume sections
        professional_summary = self.generate_professional_summary(job_title, keywords)
        skills_section = self.customize_skills_section(required_skills, keywords)
        experience_section = self.customize_experience_section(job_description, keywords)
        projects_section = self.customize_projects_section(job_description)

        # Calculate ATS score
        ats_score = self.calculate_ats_score(
            professional_summary + skills_section + experience_section
        )

        # Find missing keywords
        missing_keywords = self.find_missing_keywords(required_skills, experience_section)

        resume_data = {
            'job_id': job.get('id', ''),
            'job_title': job_title,
            'company': company,
            'professional_summary': professional_summary,
            'skills_section': skills_section,
            'experience_section': experience_section,
            'education_section': self.profile.get('education', []),
            'certifications_section': self.profile.get('certifications', []),
            'projects_section': projects_section,
            'ats_score': ats_score,
            'keyword_coverage': self.calculate_keyword_coverage(keywords, experience_section),
            'missing_keywords': missing_keywords,
            'generated_at': datetime.utcnow().isoformat()
        }

        return resume_data

    def generate_professional_summary(self, job_title: str, keywords: List[str]) -> str:
        """Generate customized professional summary"""

        candidate_name = self.profile.get('candidate', {}).get('full_name', 'Tanuj Chandel')
        current_role = self.profile.get('experience', [{}])[0].get('title', 'Operations Manager')

        # Tailor summary to job title
        summary = f"""
        Results-driven {current_role} with {self.get_years_of_experience()} years of proven expertise in {', '.join(keywords[:3])}.
        Specialized in {job_title.split('-')[0].strip()} with demonstrated success in building and scaling operations from ground zero.
        Expert in {', '.join(keywords[3:6]) if len(keywords) > 3 else 'operations management and cost optimization'}.
        AI-enabled business operator proficient in automation, data analytics, and process optimization.
        Seeking a challenging {job_title} role to leverage operational excellence and drive organizational growth.
        """

        return summary.strip()

    def customize_skills_section(self, required_skills: List[str], keywords: List[str]) -> str:
        """Customize skills section based on job requirements"""

        candidate_skills = self.profile.get('skills', {})
        all_skills = (
            candidate_skills.get('primary', []) +
            candidate_skills.get('secondary', []) +
            candidate_skills.get('technical', [])
        )

        # Prioritize skills that match job requirements
        matched_skills = []
        for req_skill in required_skills:
            for candidate_skill in all_skills:
                if req_skill.lower() in candidate_skill.lower() or candidate_skill.lower() in req_skill.lower():
                    matched_skills.append(candidate_skill)
                    break

        # Add additional relevant skills
        for keyword in keywords:
            if keyword not in matched_skills and keyword in all_skills:
                matched_skills.append(keyword)

        # Format for ATS (bullet list)
        skills_text = "• " + "\n• ".join(matched_skills[:20])
        return skills_text

    def customize_experience_section(self, job_description: str, keywords: List[str]) -> str:
        """Customize experience section to match job requirements"""

        experience = self.profile.get('experience', [])
        customized_exp = []

        for exp in experience:
            title = exp.get('title', '')
            company = exp.get('company', '')
            responsibilities = exp.get('responsibilities', [])

            # Filter responsibilities that match job keywords
            relevant_responsibilities = [
                resp for resp in responsibilities
                if any(keyword.lower() in resp.lower() for keyword in keywords)
            ]

            # If not enough matches, add all responsibilities
            if not relevant_responsibilities:
                relevant_responsibilities = responsibilities[:3]

            exp_text = f"""
            {title} | {company} | {exp.get('years', '')}
            {chr(10).join('• ' + resp for resp in relevant_responsibilities[:5])}
            """
            customized_exp.append(exp_text.strip())

        return "\n\n".join(customized_exp)

    def customize_projects_section(self, job_description: str) -> str:
        """Customize projects section based on job relevance"""

        projects = self.profile.get('projects', [])
        relevant_projects = []

        ai_keywords = ['ai', 'automation', 'dashboard', 'rag', 'ml', 'analytics']
        job_has_ai = any(keyword in job_description.lower() for keyword in ai_keywords)

        for project in projects:
            if job_has_ai:
                # Prioritize AI projects
                if any(keyword in project.get('description', '').lower() for keyword in ai_keywords):
                    relevant_projects.append(project)

        if not relevant_projects:
            relevant_projects = projects[:2]

        projects_text = []
        for project in relevant_projects:
            projects_text.append(f"• {project.get('name', '')}: {project.get('description', '')}")

        return "\n".join(projects_text)

    def extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords from job description"""

        keywords = []
        common_keywords = [
            'operations', 'warehouse', 'inventory', 'supply chain', 'logistics',
            'cash management', 'cold chain', 'leadership', 'vendor', 'quality',
            'retail', 'sales', 'administration', 'procurement', 'distribution',
            'erp', 'sap', 'crm', 'excel', 'analytics', 'bi', 'reporting'
        ]

        text_lower = text.lower()
        for keyword in common_keywords:
            if keyword in text_lower:
                keywords.append(keyword)

        return list(set(keywords))[:10]  # Return top 10 unique keywords

    def calculate_ats_score(self, text: str) -> float:
        """Calculate ATS compatibility score"""

        score = 0

        # Check formatting (simple heuristics)
        if '\n' in text:
            score += 10
        if '•' in text:
            score += 10
        if any(char in text for char in ['|', '-', ':']):
            score += 10

        # Check keyword density
        keywords = self.extract_keywords(text)
        keyword_count = sum(1 for keyword in keywords if keyword in text.lower())
        keyword_score = (keyword_count / len(keywords) * 30) if keywords else 0
        score += keyword_score

        # Check for common ATS-compatible sections
        sections = ['experience', 'education', 'skills', 'certification', 'project']
        section_score = sum(5 for section in sections if section in text.lower())
        score += section_score

        # Check text length (not too long, not too short)
        text_length = len(text)
        if 2000 < text_length < 4000:
            score += 15
        elif 1500 < text_length < 5000:
            score += 10

        return min(score, 100.0)

    def calculate_keyword_coverage(self, required_keywords: List[str], text: str) -> float:
        """Calculate percentage of required keywords present"""

        if not required_keywords:
            return 100.0

        found = sum(1 for keyword in required_keywords if keyword.lower() in text.lower())
        coverage = (found / len(required_keywords)) * 100

        return min(coverage, 100.0)

    def find_missing_keywords(self, required_skills: List[str], text: str) -> List[str]:
        """Find required skills missing from resume text"""

        missing = []
        text_lower = text.lower()

        for skill in required_skills:
            if skill.lower() not in text_lower:
                missing.append(skill)

        return missing

    def get_years_of_experience(self) -> int:
        """Calculate total years of experience"""

        experience = self.profile.get('experience', [])
        total_years = 0

        for exp in experience:
            years_str = exp.get('years', '2020-2025')
            try:
                start, end = map(int, years_str.split('-'))
                total_years += (end - start)
            except:
                total_years += 1

        return max(total_years, 10)


class ResumeFormatter:
    """Format resume into different output formats"""

    @staticmethod
    def to_markdown(resume_data: Dict[str, Any]) -> str:
        """Convert resume to markdown format"""

        md = f"""
# {resume_data.get('professional_summary', '').split()[0] if resume_data.get('professional_summary') else 'Resume'}

## Professional Summary
{resume_data.get('professional_summary', '')}

## Skills
{resume_data.get('skills_section', '')}

## Experience
{resume_data.get('experience_section', '')}

## Education
{chr(10).join(f"- {edu.get('degree', '')}, {edu.get('institution', '')} ({edu.get('years', '')})" for edu in resume_data.get('education_section', []))}

## Certifications
{chr(10).join(f"- {cert.get('name', '')} ({cert.get('issuer', '')})" for cert in resume_data.get('certifications_section', []))}

## Projects
{resume_data.get('projects_section', '')}
"""
        return md.strip()

    @staticmethod
    def to_json(resume_data: Dict[str, Any]) -> str:
        """Convert resume to JSON format"""
        return json.dumps(resume_data, indent=2)

# Example usage
if __name__ == "__main__":
    generator = ATSResumeGenerator()

    sample_job = {
        'id': 'job_001',
        'title': 'Operations Manager - Cold Storage',
        'company': 'Cold Chain Logistics',
        'description': 'Experienced Operations Manager needed for cold storage facility. Must have warehouse management, inventory control, supply chain expertise.',
        'required_skills': ['operations', 'warehouse', 'inventory', 'supply chain']
    }

    resume = generator.generate_resume_for_job(sample_job)
    print("\nGenerated Resume:")
    print(json.dumps(resume, indent=2))

    # Format to markdown
    md_resume = ResumeFormatter.to_markdown(resume)
    print("\n\nMarkdown Format:")
    print(md_resume)
