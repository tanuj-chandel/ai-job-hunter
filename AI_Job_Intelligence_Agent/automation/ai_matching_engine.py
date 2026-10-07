"""
AI Job Matching Engine
Analyzes job descriptions and matches them against candidate profile
Calculates comprehensive matching scores
"""

import json
import re
from typing import Dict, List, Any, Tuple
from datetime import datetime
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIJobMatcher:
    """Intelligent job-candidate matching engine using AI-powered analysis"""

    def __init__(self, profile_path: str = "database/master_profile.json"):
        """Initialize matcher with candidate profile"""
        self.profile = self.load_profile(profile_path)
        self.skills_mapping = self.build_skills_mapping()

    def load_profile(self, profile_path: str) -> Dict[str, Any]:
        """Load candidate master profile"""
        try:
            with open(profile_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Profile not found: {profile_path}")
            return {}

    def build_skills_mapping(self) -> Dict[str, List[str]]:
        """Build skill aliases and synonyms for better matching"""
        return {
            'operations': ['operations', 'ops', 'operations management', 'operational', 'process management'],
            'warehouse': ['warehouse', 'warehousing', 'warehouse management', 'wms'],
            'inventory': ['inventory', 'inventory management', 'stock management', 'inventory control'],
            'supply_chain': ['supply chain', 'supply chain management', 'scm', 'logistics', 'distribution'],
            'cash_management': ['cash management', 'cash flow', 'financial management', 'working capital'],
            'cold_chain': ['cold chain', 'cold storage', 'temperature control', 'perishables'],
            'leadership': ['leadership', 'team management', 'supervision', 'management', 'people management'],
            'vendor': ['vendor', 'supplier', 'vendor management', 'procurement', 'sourcing'],
            'quality': ['quality', 'quality control', 'qc', 'quality assurance', 'qa'],
            'retail': ['retail', 'retail operations', 'store operations', 'retail management'],
            'sales': ['sales', 'b2b sales', 'corporate sales', 'account management'],
        }

    def calculate_match_scores(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate all matching scores for a job"""

        # Extract job components
        job_title = job.get('title', '').lower()
        job_description = job.get('description', '').lower()
        required_skills = job.get('required_skills', [])
        required_experience = job.get('required_experience', 0)
        salary = job.get('salary', {})
        location = job.get('location', '')
        company = job.get('company', '')

        # Calculate individual scores
        skill_match_score = self.calculate_skill_match(required_skills, job_description)
        experience_match_score = self.calculate_experience_match(required_experience)
        role_match_score = self.calculate_role_match(job_title)
        salary_match_score = self.calculate_salary_match(salary)
        location_match_score = self.calculate_location_match(location)
        ats_score = self.calculate_ats_score(job_description)

        # Calculate overall match score (weighted average)
        overall_match_score = (
            skill_match_score * 0.30 +
            experience_match_score * 0.25 +
            role_match_score * 0.20 +
            salary_match_score * 0.15 +
            location_match_score * 0.10
        )

        # Estimate hiring probability
        hiring_probability = self.estimate_hiring_probability(
            overall_match_score,
            ats_score,
            skill_match_score,
            experience_match_score
        )

        # Determine competition level
        competition_level = self.assess_competition(job_title, location)

        # Generate recommendation
        recommendation = self.generate_recommendation(overall_match_score)

        return {
            'skill_match_score': round(skill_match_score, 2),
            'experience_match_score': round(experience_match_score, 2),
            'role_match_score': round(role_match_score, 2),
            'salary_match_score': round(salary_match_score, 2),
            'location_match_score': round(location_match_score, 2),
            'ats_compatibility_score': round(ats_score, 2),
            'overall_match_score': round(overall_match_score, 2),
            'hiring_probability': round(hiring_probability, 2),
            'competition_level': competition_level,
            'recommendation': recommendation,
            'analysis_timestamp': datetime.utcnow().isoformat()
        }

    def calculate_skill_match(self, required_skills: List[str], job_description: str) -> float:
        """Calculate skill match percentage (0-100)"""
        candidate_skills = self.profile.get('skills', {})

        # Combine all candidate skills
        all_candidate_skills = (
            candidate_skills.get('primary', []) +
            candidate_skills.get('secondary', []) +
            candidate_skills.get('technical', [])
        )

        if not required_skills:
            # Extract skills from job description
            required_skills = self.extract_skills_from_description(job_description)

        if not required_skills:
            return 70.0  # Default if no skills specified

        # Calculate matching skills
        matched_skills = 0
        for required_skill in required_skills:
            required_skill_lower = required_skill.lower()

            # Check direct matches
            for candidate_skill in all_candidate_skills:
                if self.skills_match(required_skill_lower, candidate_skill.lower()):
                    matched_skills += 1
                    break

        # Calculate percentage
        skill_match_percentage = (matched_skills / len(required_skills)) * 100 if required_skills else 0

        # Cap at 100
        return min(skill_match_percentage, 100.0)

    def calculate_experience_match(self, required_experience: float) -> float:
        """Calculate experience match percentage (0-100)"""
        # Extract candidate's total experience
        experience = self.profile.get('experience', [])
        candidate_experience_years = len(experience)  # Simplified: count positions

        # More sophisticated: calculate total years
        total_years = 0
        for exp in experience:
            try:
                start_year = int(exp.get('years', '2020-2025').split('-')[0])
                end_year = int(exp.get('years', '2020-2025').split('-')[1])
                total_years += (end_year - start_year)
            except:
                pass

        if total_years == 0:
            total_years = candidate_experience_years

        # Calculate match
        if required_experience == 0:
            return 100.0

        if total_years >= required_experience:
            return 100.0

        # Partial credit for some experience
        match_percentage = (total_years / required_experience) * 100
        return min(match_percentage, 100.0)

    def calculate_role_match(self, job_title: str) -> float:
        """Calculate how well the job role matches candidate's target roles"""
        target_roles = self.profile.get('candidate', {}).get('preferred_roles', [])

        if not target_roles:
            return 50.0

        # Check if job title contains any target role
        for role in target_roles:
            if role.lower() in job_title:
                return 100.0

        # Check for partial matches
        for role in target_roles:
            words = role.lower().split()
            matching_words = sum(1 for word in words if word in job_title)
            if matching_words > 0:
                return 75.0

        return 40.0

    def calculate_salary_match(self, salary: Dict[str, Any]) -> float:
        """Calculate salary match (0-100)"""
        expected_salary = self.profile.get('candidate', {}).get('salary_expectations', {})

        salary_min = salary.get('min', 0)
        salary_max = salary.get('max', 0)
        currency = salary.get('currency', 'INR')

        # Get expected salary for the currency
        if currency == 'INR':
            expected_min = expected_salary.get('india', {}).get('min', 0)
        elif currency == 'AED':
            expected_min = expected_salary.get('gulf', {}).get('min', 0)
        else:
            expected_min = expected_salary.get('remote_worldwide', {}).get('min', 0)

        if not salary_min or expected_min == 0:
            return 70.0

        # Calculate match
        if salary_min >= expected_min:
            return 100.0

        match_percentage = (salary_min / expected_min) * 100
        return min(match_percentage, 100.0)

    def calculate_location_match(self, location: str) -> float:
        """Calculate location match (0-100)"""
        preferred_locations = self.profile.get('candidate', {}).get('preferred_locations', [])
        location_lower = location.lower()

        # Check exact matches
        for pref_location in preferred_locations:
            if pref_location.lower() in location_lower:
                return 100.0

        # Check country matches
        country_keywords = {
            'India': ['india', 'bangalore', 'mumbai', 'delhi', 'hyderabad'],
            'United Arab Emirates': ['uae', 'dubai', 'abu dhabi'],
            'Saudi Arabia': ['saudi', 'riyadh'],
            'Qatar': ['qatar', 'doha'],
            'Remote': ['remote', 'work from home']
        }

        for country, keywords in country_keywords.items():
            if country.lower() in preferred_locations:
                for keyword in keywords:
                    if keyword in location_lower:
                        return 100.0

        # Remote is always acceptable
        if 'remote' in location_lower and 'Remote Worldwide' in preferred_locations:
            return 100.0

        return 40.0

    def calculate_ats_score(self, job_description: str) -> float:
        """Calculate ATS (Applicant Tracking System) compatibility score"""

        # Check for common ATS-friendly keywords
        candidate_skills = self.profile.get('skills', {})
        all_skills = (
            candidate_skills.get('primary', []) +
            candidate_skills.get('secondary', []) +
            candidate_skills.get('technical', [])
        )

        matched_keywords = 0
        total_keywords = len(all_skills)

        for skill in all_skills:
            if skill.lower() in job_description.lower():
                matched_keywords += 1

        ats_score = (matched_keywords / total_keywords * 100) if total_keywords > 0 else 50.0

        # Bonus for specific technical terms
        technical_terms = ['ai', 'automation', 'analytics', 'dashboard', 'bi', 'erp', 'crm']
        for term in technical_terms:
            if term in job_description.lower():
                ats_score = min(ats_score + 5, 100.0)

        return ats_score

    def estimate_hiring_probability(
        self,
        overall_match: float,
        ats_score: float,
        skill_match: float,
        experience_match: float
    ) -> float:
        """Estimate probability of getting hired for this job"""

        # Weighted formula for hiring probability
        hiring_prob = (
            overall_match * 0.35 +
            skill_match * 0.30 +
            experience_match * 0.20 +
            ats_score * 0.15
        )

        # Apply confidence multiplier based on match quality
        if overall_match >= 90:
            multiplier = 1.1
        elif overall_match >= 80:
            multiplier = 1.0
        elif overall_match >= 70:
            multiplier = 0.9
        elif overall_match >= 60:
            multiplier = 0.8
        else:
            multiplier = 0.7

        final_probability = hiring_prob * multiplier
        return min(final_probability, 99.0)  # Cap at 99%

    def assess_competition(self, job_title: str, location: str) -> str:
        """Assess competition level for the job"""

        # High competition keywords
        high_competition_titles = ['manager', 'senior', 'director', 'executive']
        high_competition_locations = ['bangalore', 'mumbai', 'delhi', 'dubai']

        competition_score = 0

        for keyword in high_competition_titles:
            if keyword in job_title.lower():
                competition_score += 3

        for keyword in high_competition_locations:
            if keyword in location.lower():
                competition_score += 2

        if competition_score >= 5:
            return "High"
        elif competition_score >= 2:
            return "Medium"
        else:
            return "Low"

    def generate_recommendation(self, overall_match_score: float) -> str:
        """Generate recommendation based on match score"""

        if overall_match_score >= 90:
            return "★★★★★ Apply Immediately"
        elif overall_match_score >= 80:
            return "★★★★ Strong Match"
        elif overall_match_score >= 70:
            return "★★★ Good Match"
        elif overall_match_score >= 60:
            return "★★ Average"
        else:
            return "★ Ignore"

    def skills_match(self, required_skill: str, candidate_skill: str) -> bool:
        """Check if skills match (considering aliases and synonyms)"""

        # Exact match
        if required_skill == candidate_skill:
            return True

        # Check skill mappings
        for skill_group, aliases in self.skills_mapping.items():
            if required_skill in aliases and candidate_skill in aliases:
                return True

        # Check if one contains the other
        if required_skill in candidate_skill or candidate_skill in required_skill:
            return True

        return False

    def extract_skills_from_description(self, description: str) -> List[str]:
        """Extract required skills from job description"""

        common_skills = [
            'operations', 'warehouse', 'inventory', 'supply chain', 'logistics',
            'cash management', 'cold chain', 'leadership', 'vendor management',
            'quality control', 'retail', 'sales', 'administration', 'crm',
            'excel', 'erp', 'sap', 'oracle', 'python', 'sql', 'analytics',
            'bi', 'dashboard', 'reporting', 'compliance', 'compliance'
        ]

        found_skills = []
        description_lower = description.lower()

        for skill in common_skills:
            if skill in description_lower:
                found_skills.append(skill)

        return found_skills

# Example usage
if __name__ == "__main__":
    matcher = AIJobMatcher()

    # Sample job
    sample_job = {
        'title': 'Operations Manager - Cold Storage',
        'company': 'Cold Chain Logistics',
        'location': 'Mumbai, India',
        'description': 'We are looking for an experienced Operations Manager with expertise in warehouse management, inventory control, and supply chain optimization. Must have experience with cold chain operations.',
        'required_skills': ['operations', 'warehouse', 'inventory', 'supply chain'],
        'required_experience': 5,
        'salary': {'min': 1800000, 'max': 2500000, 'currency': 'INR'}
    }

    scores = matcher.calculate_match_scores(sample_job)
    print("\nJob Matching Analysis:")
    print(json.dumps(scores, indent=2))
