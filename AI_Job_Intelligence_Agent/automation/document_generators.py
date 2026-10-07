"""
Cover Letter Generator
Generates personalized cover letters for each job application
"""

import json
from typing import Dict, List, Any
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CoverLetterGenerator:
    """Generate personalized cover letters for job applications"""

    def __init__(self, profile_path: str = "database/master_profile.json"):
        """Initialize cover letter generator"""
        self.profile = self.load_profile(profile_path)

    def load_profile(self, profile_path: str) -> Dict[str, Any]:
        """Load master profile"""
        try:
            with open(profile_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Profile not found: {profile_path}")
            return {}

    def generate_cover_letter_for_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Generate customized cover letter for job"""

        company = job.get('company', '')
        job_title = job.get('title', '')
        job_description = job.get('description', '')
        location = job.get('location', '')

        # Extract key responsibilities from job description
        key_responsibilities = self.extract_responsibilities(job_description)

        # Generate cover letter sections
        salutation = self.generate_salutation(company)
        opening = self.generate_opening_paragraph(company, job_title)
        body = self.generate_body_paragraph(job_title, key_responsibilities, job_description)
        closing = self.generate_closing_paragraph()

        full_letter = f"{salutation}\n\n{opening}\n\n{body}\n\n{closing}"

        return {
            'job_id': job.get('id', ''),
            'company': company,
            'job_title': job_title,
            'salutation': salutation,
            'opening_paragraph': opening,
            'body_paragraph': body,
            'closing_paragraph': closing,
            'full_text': full_letter,
            'generated_at': datetime.utcnow().isoformat()
        }

    def generate_salutation(self, company: str) -> str:
        """Generate appropriate salutation"""
        return "Dear Hiring Manager,"

    def generate_opening_paragraph(self, company: str, job_title: str) -> str:
        """Generate opening paragraph"""

        candidate_name = self.profile.get('candidate', {}).get('full_name', 'Tanuj Chandel')

        opening = f"""I am writing to express my strong interest in the {job_title} position at {company}.
With over {self.get_years_experience()}+ years of progressive experience in operations management,
supply chain optimization, and business operations, I am confident in my ability to contribute
significantly to your team and drive operational excellence."""

        return opening.strip()

    def generate_body_paragraph(self, job_title: str, responsibilities: List[str], job_desc: str) -> str:
        """Generate main body paragraph"""

        candidate_skills = self.profile.get('skills', {})
        primary_skills = candidate_skills.get('primary', [])

        body = f"""In my current role as Founder & Operations Head at Pitambara Cold Storage,
I have successfully built and scaled a commercial cold storage facility from greenfield to profitability.
This experience has honed my expertise in {', '.join(primary_skills[:3])},
which directly align with your requirements for this {job_title} position.

My key achievements include:
• Reduced operational costs and wastage by 20%+ through systematic inventory management and process optimization
• Built and managed a supplier network of 50+ vendors, ensuring seamless supply chain coordination
• Implemented AI-assisted dashboards for real-time inventory tracking and demand forecasting
• Achieved consistent profitability while managing full P&L and cash operations

Your emphasis on {responsibilities[0] if responsibilities else 'operational excellence'}
resonates strongly with my professional philosophy of building scalable, efficient operations.
I am particularly drawn to {job_title} because it offers the opportunity to leverage my
founder-mode operational expertise and drive meaningful business impact."""

        return body.strip()

    def generate_closing_paragraph(self) -> str:
        """Generate closing paragraph"""

        candidate_email = self.profile.get('candidate', {}).get('email', 'tanuj@example.com')
        candidate_phone = self.profile.get('candidate', {}).get('phone', '+91-XXXXXXXXXX')

        closing = f"""I am excited about the opportunity to bring my operational expertise,
entrepreneurial mindset, and commitment to excellence to your organization.
I would welcome the opportunity to discuss how I can contribute to your team's success.

Thank you for considering my application. I look forward to hearing from you soon.

Best regards,
Tanuj Chandel
{candidate_phone}
{candidate_email}"""

        return closing.strip()

    def extract_responsibilities(self, job_description: str) -> List[str]:
        """Extract key responsibilities from job description"""

        responsibilities = []

        # Common responsibility keywords
        keywords = [
            'manage', 'coordinate', 'oversee', 'develop', 'implement',
            'optimize', 'ensure', 'monitor', 'maintain', 'improve'
        ]

        lines = job_description.split('\n')
        for line in lines:
            line_lower = line.lower()
            for keyword in keywords:
                if keyword in line_lower:
                    responsibilities.append(line.strip())
                    break

        return responsibilities[:5]

    def get_years_experience(self) -> int:
        """Get years of experience"""
        experience = self.profile.get('experience', [])
        total = 0
        for exp in experience:
            try:
                years = exp.get('years', '2020-2025')
                start, end = map(int, years.split('-'))
                total += (end - start)
            except:
                total += 1
        return max(total, 10)


class RecruiterMessageGenerator:
    """Generate recruiter outreach messages"""

    def __init__(self, profile_path: str = "database/master_profile.json"):
        """Initialize message generator"""
        self.profile = self.load_profile(profile_path)

    def load_profile(self, profile_path: str) -> Dict[str, Any]:
        """Load master profile"""
        try:
            with open(profile_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def generate_all_messages(self, job: Dict[str, Any]) -> Dict[str, str]:
        """Generate all types of recruiter messages"""

        return {
            'linkedin_message': self.generate_linkedin_message(job),
            'email_message': self.generate_email_message(job),
            'cold_outreach': self.generate_cold_outreach(job),
            'whatsapp_message': self.generate_whatsapp_message(job),
            'follow_up_message': self.generate_follow_up_message(job)
        }

    def generate_linkedin_message(self, job: Dict[str, Any]) -> str:
        """Generate LinkedIn message"""

        company = job.get('company', '')
        job_title = job.get('title', '')

        return f"""Hi there! I came across the {job_title} opening at {company} and I'm genuinely excited about the opportunity.

With 10+ years of operations management experience, including building a cold storage facility from zero to profitability, I believe I can add significant value to your team.

I'd love to discuss how my background in operations, supply chain optimization, and AI-enabled process automation aligns with your needs.

Looking forward to connecting!

Best regards,
Tanuj Chandel"""

    def generate_email_message(self, job: Dict[str, Any]) -> str:
        """Generate professional email"""

        company = job.get('company', '')
        job_title = job.get('title', '')
        recruiter_email = job.get('recruiter_email', 'hiring@company.com')

        return f"""Subject: Application for {job_title} at {company}

Dear Hiring Team,

I am writing to express my strong interest in the {job_title} position at {company}.

With over 10 years of proven expertise in operations management, warehouse optimization, and supply chain coordination, I am confident in my ability to drive operational excellence for your organization.

In my current role, I have:
• Built and scaled operations from greenfield to profitability
• Implemented AI-driven inventory and demand forecasting systems
• Reduced operational costs by 20%+ through process optimization
• Managed complex vendor networks and stakeholder relationships

I would welcome the opportunity to discuss how my background and expertise can contribute to your team's success.

Best regards,
Tanuj Chandel
Phone: +91-XXXXXXXXXX
Email: tanuj@example.com"""

    def generate_cold_outreach(self, job: Dict[str, Any]) -> str:
        """Generate cold outreach message"""

        company = job.get('company', '')

        return f"""Hi,

I've been following {company}'s growth in the operations and logistics space, and I'm impressed by your company's focus on innovation and excellence.

I'm an Operations Manager with 10+ years of experience building and scaling high-performance operations. Recently, I successfully built a cold storage facility from scratch, resulting in 20%+ cost savings and a strong vendor network.

I'd love to explore how I can contribute to {company}'s continued growth and success.

Would you be open to a quick call next week?

Best regards,
Tanuj Chandel"""

    def generate_whatsapp_message(self, job: Dict[str, Any]) -> str:
        """Generate WhatsApp message"""

        job_title = job.get('title', '')
        company = job.get('company', '')

        return f"""Hi! 👋 I saw the {job_title} opening at {company} and I'm very interested.

10+ years operations experience ✓
Cold storage & logistics background ✓
AI automation expertise ✓

Would love to chat about the role. When can we connect? 📞"""

    def generate_follow_up_message(self, job: Dict[str, Any]) -> str:
        """Generate follow-up message"""

        company = job.get('company', '')
        job_title = job.get('title', '')

        return f"""Hi,

Following up on my application for the {job_title} position at {company}.

I remain very interested in this opportunity and would welcome the chance to discuss my qualifications and how I can contribute to your team.

Please let me know if you need any additional information.

Best regards,
Tanuj Chandel"""


class InterviewPreparer:
    """Generate interview preparation materials"""

    def __init__(self, profile_path: str = "database/master_profile.json"):
        """Initialize interview preparer"""
        self.profile = self.load_profile(profile_path)

    def load_profile(self, profile_path: str) -> Dict[str, Any]:
        """Load master profile"""
        try:
            with open(profile_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def generate_interview_preparation(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Generate complete interview preparation package"""

        return {
            'company': job.get('company', ''),
            'job_title': job.get('title', ''),
            'hr_questions': self.generate_hr_questions(),
            'technical_questions': self.generate_technical_questions(job),
            'behavioral_questions': self.generate_behavioral_questions(),
            'star_answers': self.generate_star_answers(),
            'questions_to_ask': self.generate_questions_to_ask(job),
            'interview_tips': self.generate_interview_tips(),
            'generated_at': datetime.utcnow().isoformat()
        }

    def generate_hr_questions(self) -> List[Dict[str, str]]:
        """Generate typical HR interview questions"""

        return [
            {
                'question': 'Tell me about yourself.',
                'sample_answer': 'I am Tanuj Chandel, an accomplished Operations Manager with 10+ years of experience in building and scaling high-performance operations. Currently, I founded and am Operations Head of Pitambara Cold Storage, where I transformed a greenfield project into a profitable facility serving 50+ vendors. My expertise spans warehouse management, inventory optimization, supply chain coordination, and AI-enabled process automation.'
            },
            {
                'question': 'Why are you interested in this role?',
                'sample_answer': 'This Operations Manager role aligns perfectly with my career goals. I am drawn to the opportunity to leverage my founder-mode operational expertise, drive process optimization, and scale operations. The company\'s focus on efficiency and innovation resonates with my professional philosophy.'
            },
            {
                'question': 'What are your strengths?',
                'sample_answer': 'Building operations from zero, hands-on cost/cash control, vendor relationship management, process optimization, and entrepreneurial mindset. I excel at identifying inefficiencies and implementing AI-driven solutions for continuous improvement.'
            },
            {
                'question': 'What are your weaknesses?',
                'sample_answer': 'I am always eager to learn and grow. While my technical background is strong, I continuously upskill in emerging technologies. I am currently completing a B10X AI program to deepen my expertise in AI automation and business applications.'
            },
            {
                'question': 'Where do you see yourself in 5 years?',
                'sample_answer': 'I see myself leading large-scale operations at a fast-growing company, driving digital transformation through AI and automation. I aim to build systems and teams that consistently deliver operational excellence while scaling profitably.'
            }
        ]

    def generate_technical_questions(self, job: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate role-specific technical questions"""

        return [
            {
                'question': 'How would you optimize inventory management in a cold storage facility?',
                'sample_answer': 'I would implement a multi-layered approach: (1) Deploy RFID/barcode systems for real-time tracking, (2) Use AI-powered demand forecasting to optimize stock levels, (3) Implement ABC analysis for inventory prioritization, (4) Set up automated alerts for expiration dates, (5) Establish vendor scorecards for performance monitoring. In my current role, this approach reduced wastage by 20%.'
            },
            {
                'question': 'Describe your experience with supply chain management.',
                'sample_answer': 'I have managed complex supply chains with 50+ vendors across farmers, traders, and logistics providers. I implemented vendor performance dashboards, negotiated favorable terms, reduced lead times by 15%, and established backup suppliers for critical items. I use data-driven insights to make procurement decisions.'
            },
            {
                'question': 'How do you handle cost reduction while maintaining quality?',
                'sample_answer': 'Cost reduction and quality are not mutually exclusive. I focus on process optimization, eliminating waste, and negotiating better supplier terms without compromising standards. I implemented waste reduction initiatives that cut costs by 20% while improving service levels.'
            }
        ]

    def generate_behavioral_questions(self) -> List[Dict[str, str]]:
        """Generate behavioral interview questions with STAR answers"""

        return [
            {
                'question': 'Tell me about a time you solved a complex operational problem.',
                'star_answer': {
                    'situation': 'As Operations Head at Pitambara Cold Storage, I faced 25% product wastage due to poor inventory tracking and manual processes.',
                    'task': 'I needed to reduce wastage, improve inventory accuracy, and maintain service levels without additional headcount.',
                    'action': 'I implemented an AI-powered inventory management system with real-time tracking, automated demand forecasting, and predictive alerts. I trained the team and established new operational procedures.',
                    'result': 'Reduced wastage to 5%, improved inventory accuracy to 99%, and achieved these results in 3 months with zero additional costs.'
                }
            },
            {
                'question': 'Describe a time you led a team through significant change.',
                'star_answer': {
                    'situation': 'At EuroKids Preschool, enrollment was stagnant and profitability was declining.',
                    'task': 'I needed to reverse the downtrend and drive growth.',
                    'action': 'I implemented targeted marketing initiatives, reorganized operations for efficiency, trained and motivated the 12-person team, and established new quality benchmarks.',
                    'result': 'Achieved 35%+ enrollment growth with 4 consecutive years of profitability.'
                }
            }
        ]

    def generate_star_answers(self) -> List[Dict[str, Any]]:
        """Generate STAR format answers for common questions"""

        return [
            {
                'question': 'Tell me about your biggest achievement.',
                'story': {
                    'situation': 'Started Pitambara Cold Storage from greenfield with zero operations.',
                    'task': 'Build a profitable, sustainable cold storage facility serving the agri-supply chain.',
                    'action': 'Built infrastructure, established regulatory compliance, recruited team, created vendor network of 50+, implemented AI dashboards, optimized inventory.',
                    'result': 'Achieved profitability in 18 months, serving 50+ vendors, reducing wastage 20%+, establishing a strong market position.'
                }
            }
        ]

    def generate_questions_to_ask(self, job: Dict[str, Any]) -> List[str]:
        """Generate smart questions to ask interviewer"""

        return [
            'What are the key performance metrics for this role in the first 90 days?',
            'Can you describe the team structure and reporting hierarchy?',
            'What are the biggest operational challenges your organization is facing?',
            'How does the company approach process optimization and automation?',
            'What opportunities exist for professional development and growth?',
            'How is success measured for someone in this position?',
            'What is the company\'s vision for the next 2-3 years?',
            'How does the organization support innovation and continuous improvement?'
        ]

    def generate_interview_tips(self) -> List[str]:
        """Generate interview preparation tips"""

        return [
            '✓ Research the company thoroughly - products, markets, competitors, recent news',
            '✓ Practice your STAR answers - be specific with metrics and outcomes',
            '✓ Prepare 3-5 success stories highlighting relevant skills',
            '✓ Discuss your AI and automation expertise - a key differentiator',
            '✓ Emphasize your founder experience and operational building',
            '✓ Come with thoughtful questions about the role and company',
            '✓ Dress professionally and arrive 10 minutes early',
            '✓ Listen actively and answer questions directly',
            '✓ Follow up with a thank-you email within 24 hours'
        ]


# Example usage
if __name__ == "__main__":
    sample_job = {
        'id': 'job_001',
        'title': 'Operations Manager',
        'company': 'Cold Chain Logistics Ltd',
        'description': 'We seek an experienced Operations Manager for our cold storage division.',
        'recruiter_email': 'hiring@coldchain.com'
    }

    # Generate cover letter
    cl_gen = CoverLetterGenerator()
    cover_letter = cl_gen.generate_cover_letter_for_job(sample_job)
    print("Cover Letter Generated")
    print(json.dumps(cover_letter, indent=2))

    # Generate recruiter messages
    msg_gen = RecruiterMessageGenerator()
    messages = msg_gen.generate_all_messages(sample_job)
    print("\nRecruiter Messages Generated")
    print(json.dumps(messages, indent=2))

    # Generate interview prep
    interview_prep = InterviewPreparer().generate_interview_preparation(sample_job)
    print("\nInterview Preparation Generated")
    print(json.dumps(interview_prep, indent=2))
