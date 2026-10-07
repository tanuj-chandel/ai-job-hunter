"""
AI Job Intelligence Agent - Database Models
Defines SQLAlchemy ORM models for jobs, applications, companies, recruiters, etc.
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, JSON, ForeignKey, Table, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import enum
import uuid

Base = declarative_base()

# Association tables for many-to-many relationships
job_skills = Table(
    'job_skills', Base.metadata,
    Column('job_id', String, ForeignKey('jobs.id')),
    Column('skill_id', String, ForeignKey('skills.id'))
)

job_keywords = Table(
    'job_keywords', Base.metadata,
    Column('job_id', String, ForeignKey('jobs.id')),
    Column('keyword_id', String, ForeignKey('keywords.id'))
)

class JobStatus(str, enum.Enum):
    NEW = "new"
    VIEWED = "viewed"
    APPLIED = "applied"
    REJECTED = "rejected"
    SHORTLISTED = "shortlisted"
    INTERVIEW = "interview"
    OFFER = "offer"
    ACCEPTED = "accepted"

class ApplicationStatus(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    REVIEWING = "reviewing"
    SHORTLISTED = "shortlisted"
    INTERVIEW = "interview"
    REJECTED = "rejected"
    OFFER = "offer"
    ACCEPTED = "accepted"

class Job(Base):
    __tablename__ = 'jobs'

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_title = Column(String, nullable=False, index=True)
    company_name = Column(String, nullable=False, index=True)
    location = Column(String, nullable=False, index=True)
    country = Column(String, nullable=False, index=True)
    job_description = Column(Text, nullable=False)
    job_url = Column(String, unique=True, index=True)
    source_portal = Column(String, nullable=False)  # LinkedIn, Naukri, Indeed, etc.

    # Salary
    salary_min = Column(Float)
    salary_max = Column(Float)
    salary_currency = Column(String)

    # Experience
    required_experience_min = Column(Float)
    required_experience_max = Column(Float)
    required_skills = Column(JSON)
    required_education = Column(JSON)

    # Details
    employment_type = Column(String)  # Full-time, Contract, etc.
    industry = Column(String)
    department = Column(String)
    application_deadline = Column(DateTime)
    recruiter_name = Column(String)
    recruiter_email = Column(String)
    recruiter_phone = Column(String)
    company_website = Column(String)

    # AI Matching Scores
    overall_match_score = Column(Float)  # 0-100
    skill_match_score = Column(Float)
    experience_match_score = Column(Float)
    ats_compatibility_score = Column(Float)
    hiring_probability = Column(Float)  # Probability % 0-100
    competition_level = Column(String)  # Low, Medium, High
    salary_match_score = Column(Float)
    growth_opportunity_score = Column(Float)
    location_match_score = Column(Float)
    interview_probability = Column(Float)

    # Status tracking
    status = Column(SQLEnum(JobStatus), default=JobStatus.NEW, index=True)
    is_duplicate = Column(Boolean, default=False)
    is_fake = Column(Boolean, default=False)
    is_expired = Column(Boolean, default=False)
    is_bookmarked = Column(Boolean, default=False)
    is_applied = Column(Boolean, default=False)

    # Timestamps
    posted_date = Column(DateTime)
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # AI Analysis
    ai_analysis = Column(JSON)  # Stores AI analysis results
    recommendation = Column(String)  # ★★★★★, ★★★★, ★★★, ★★, ★

    # Relationships
    skills = relationship('Skill', secondary=job_skills, back_populates='jobs')
    keywords = relationship('Keyword', secondary=job_keywords, back_populates='jobs')
    applications = relationship('Application', back_populates='job')
    company = relationship('Company', back_populates='jobs')

    def __repr__(self):
        return f"<Job(title='{self.job_title}', company='{self.company_name}', match={self.overall_match_score})>"

class Company(Base):
    __tablename__ = 'companies'

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    company_name = Column(String, unique=True, index=True)
    website = Column(String)
    industry = Column(String)
    employee_count = Column(String)
    founded_year = Column(Integer)
    description = Column(Text)

    # Ratings & Reviews
    glassdoor_rating = Column(Float)
    hiring_trend = Column(String)
    recent_news = Column(JSON)
    funding_status = Column(String)
    growth_rate = Column(Float)

    # Recruitment intel
    hiring_frequency = Column(Integer)  # Number of active jobs
    average_hiring_time = Column(Float)  # Days to hire

    # Timestamps
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    jobs = relationship('Job', back_populates='company')

    def __repr__(self):
        return f"<Company(name='{self.company_name}', rating={self.glassdoor_rating})>"

class Skill(Base):
    __tablename__ = 'skills'

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    skill_name = Column(String, unique=True, index=True)
    category = Column(String)  # Technical, Soft, Domain, etc.
    proficiency_level = Column(String)  # Beginner, Intermediate, Advanced, Expert
    endorsement_count = Column(Integer)

    jobs = relationship('Job', secondary=job_skills, back_populates='skills')

    def __repr__(self):
        return f"<Skill(name='{self.skill_name}')>"

class Keyword(Base):
    __tablename__ = 'keywords'

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    keyword = Column(String, unique=True, index=True)
    relevance_score = Column(Float)

    jobs = relationship('Job', secondary=job_keywords, back_populates='keywords')

class Application(Base):
    __tablename__ = 'applications'

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String, ForeignKey('jobs.id'), nullable=False)
    status = Column(SQLEnum(ApplicationStatus), default=ApplicationStatus.DRAFT)

    # Application materials
    resume_file_path = Column(String)
    cover_letter_file_path = Column(String)
    recruiter_message = Column(Text)

    # Application tracking
    application_date = Column(DateTime)
    applied_url = Column(String)
    application_method = Column(String)  # Manual, LinkedIn Easy Apply, Auto-apply

    # Tracking
    email_opened = Column(Boolean, default=False)
    response_received = Column(Boolean, default=False)
    response_date = Column(DateTime)
    response_text = Column(Text)

    # Interview tracking
    interview_scheduled = Column(Boolean, default=False)
    interview_date = Column(DateTime)
    interview_type = Column(String)  # Phone, Video, In-person
    interview_notes = Column(Text)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    job = relationship('Job', back_populates='applications')

    def __repr__(self):
        return f"<Application(job_id='{self.job_id}', status='{self.status}')>"

class Resume(Base):
    __tablename__ = 'resumes'

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String, ForeignKey('jobs.id'))
    resume_type = Column(String)  # Master, Customized, ATS-optimized

    # Content
    professional_summary = Column(Text)
    skills_section = Column(JSON)
    experience_section = Column(JSON)
    education_section = Column(JSON)
    certifications_section = Column(JSON)
    projects_section = Column(JSON)

    # ATS Metrics
    ats_score = Column(Float)
    keyword_coverage = Column(Float)
    formatting_compatibility = Column(Float)
    readability_score = Column(Float)
    missing_keywords = Column(JSON)
    weak_areas = Column(JSON)
    improvement_suggestions = Column(JSON)

    # Files
    pdf_file_path = Column(String)
    docx_file_path = Column(String)
    markdown_file_path = Column(String)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Resume(job_id='{self.job_id}', ats_score={self.ats_score})>"

class CoverLetter(Base):
    __tablename__ = 'cover_letters'

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String, ForeignKey('jobs.id'))

    # Content
    opening_paragraph = Column(Text)
    why_suitable_paragraph = Column(Text)
    experience_alignment = Column(Text)
    skills_highlight = Column(Text)
    closing_paragraph = Column(Text)
    full_text = Column(Text)

    # Files
    pdf_file_path = Column(String)
    docx_file_path = Column(String)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<CoverLetter(job_id='{self.job_id}')>"

class DailyReport(Base):
    __tablename__ = 'daily_reports'

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    report_date = Column(DateTime, default=datetime.utcnow, index=True)

    # Statistics
    jobs_found = Column(Integer)
    duplicate_jobs_filtered = Column(Integer)
    expired_jobs_filtered = Column(Integer)
    fake_jobs_filtered = Column(Integer)
    top_matches_count = Column(Integer)

    # Top job details
    top_matches = Column(JSON)  # List of top 5 job IDs with scores
    highest_salary_job = Column(String)  # Job ID
    best_company = Column(String)  # Company name

    # Scoring metrics
    average_match_score = Column(Float)
    average_ats_score = Column(Float)
    average_hiring_probability = Column(Float)

    # Recommendations
    recommendations = Column(JSON)
    missing_skills = Column(JSON)

    # Files
    pdf_report_path = Column(String)
    excel_report_path = Column(String)

    # Execution
    execution_start_time = Column(DateTime)
    execution_end_time = Column(DateTime)
    execution_status = Column(String)  # Success, Partial, Failed
    error_log = Column(Text)

    def __repr__(self):
        return f"<DailyReport(date='{self.report_date}', jobs_found={self.jobs_found})>"

class ExecutionLog(Base):
    __tablename__ = 'execution_logs'

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    execution_date = Column(DateTime, default=datetime.utcnow, index=True)

    # Task details
    task_name = Column(String)
    task_type = Column(String)  # job_search, resume_gen, cover_letter_gen, etc.
    status = Column(String)  # In-progress, Completed, Failed

    # Details
    items_processed = Column(Integer)
    items_successful = Column(Integer)
    items_failed = Column(Integer)

    # Logging
    log_message = Column(Text)
    error_details = Column(Text)

    execution_time_seconds = Column(Float)

    def __repr__(self):
        return f"<ExecutionLog(task='{self.task_name}', status='{self.status}')>"

# Database initialization
def init_db(database_url: str = "sqlite:///./ai_job_agent.db"):
    """Initialize database with all tables"""
    engine = create_engine(database_url, connect_args={"check_same_thread": False} if "sqlite" in database_url else {})
    Base.metadata.create_all(bind=engine)
    return engine, sessionmaker(bind=engine)
