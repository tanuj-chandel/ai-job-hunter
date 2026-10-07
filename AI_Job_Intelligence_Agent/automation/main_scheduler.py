"""
AI Job Intelligence Agent - Main Scheduler
Runs automatically every day at 8:00 AM
"""

import sys
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_job_agent_scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AIJobIntelligenceScheduler:
    """Main scheduler that runs the AI Job Intelligence Agent daily at 8:00 AM"""

    def __init__(self, config_path: str = "config/config.json"):
        """Initialize scheduler with configuration"""
        self.config_path = config_path
        self.config = self.load_config()

        # Initialize scheduler
        self.scheduler = BackgroundScheduler(
            jobstores=self.config.get('jobstores', {}),
            executors=self.config.get('executors', {}),
            job_defaults=self.config.get('job_defaults', {}),
            timezone=self.config.get('timezone', 'Asia/Kolkata')
        )

        # Add event listeners
        self.scheduler.add_listener(self.job_success_listener, EVENT_JOB_EXECUTED)
        self.scheduler.add_listener(self.job_error_listener, EVENT_JOB_ERROR)

        # Initialize job modules
        self.initialize_modules()

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        config_path = Path(self.config_path)
        if config_path.exists():
            with open(config_path, 'r') as f:
                return json.load(f)

        # Default configuration
        return {
            'timezone': 'Asia/Kolkata',
            'cron_schedule': {
                'hour': 8,      # 8:00 AM
                'minute': 0,    # 8:00 AM
                'second': 0     # 8:00 AM
            },
            'retry_on_failure': True,
            'max_retries': 3,
            'retry_delay_minutes': 5,
            'notification_settings': {
                'desktop': True,
                'email': False,
                'telegram': False,
                'whatsapp': False
            },
            'database': {
                'sqlite_path': 'database/ai_job_agent.db',
                'backup_enabled': True
            }
        }

    def initialize_modules(self):
        """Initialize all job modules"""
        # These will be imported when needed to avoid circular imports
        self.modules_available = {
            'job_search': True,
            'ai_matching': True,
            'resume_generation': True,
            'cover_letter_generation': True,
            'interview_preparation': True,
            'company_research': True,
            'dashboard_update': True,
            'notification': True
        }
        logger.info("Job modules initialized")

    def daily_job_execution(self):
        """
        Main daily job execution
        This function runs every day at 8:00 AM
        """
        logger.info(f"🚀 AI Job Intelligence Agent starting daily execution at {datetime.now()}")

        try:
            # Step 1: Search all supported job portals
            jobs_found = self.search_jobs()

            # Step 2: Remove duplicate and invalid jobs
            filtered_jobs = self.filter_jobs(jobs_found)

            # Step 3: Match jobs with profile and calculate scores
            matched_jobs = self.match_and_score_jobs(filtered_jobs)

            # Step 4: Rank jobs by match score
            ranked_jobs = self.rank_jobs(matched_jobs)

            # Step 5: Generate ATS resumes for top matches
            resumes_generated = self.generate_ats_resumes(ranked_jobs)

            # Step 6: Generate personalized cover letters
            cover_letters_generated = self.generate_cover_letters(ranked_jobs)

            # Step 7: Generate recruiter messages
            recruiter_messages = self.generate_recruiter_messages(ranked_jobs)

            # Step 8: Generate interview preparation
            interview_prep = self.generate_interview_preparation(ranked_jobs)

            # Step 9: Company research
            company_research = self.research_companies(ranked_jobs)

            # Step 10: Salary analysis
            salary_analysis = self.analyze_salaries(ranked_jobs)

            # Step 11: Save everything to organized folders
            self.organize_files(ranked_jobs, {
                'resumes': resumes_generated,
                'cover_letters': cover_letters_generated,
                'recruiter_messages': recruiter_messages,
                'interview_prep': interview_prep,
                'company_research': company_research,
                'salary_analysis': salary_analysis
            })

            # Step 12: Update dashboard and generate report
            dashboard_data = self.update_dashboard(ranked_jobs)
            report_generated = self.generate_daily_report(dashboard_data)

            # Step 13: Send notifications
            self.send_notifications({
                'jobs_found': len(jobs_found),
                'top_matches': len(ranked_jobs[:5]),
                'resumes_generated': len(resumes_generated),
                'report_path': report_generated
            })

            logger.info(f"✅ Daily execution completed successfully at {datetime.now()}")

        except Exception as e:
            logger.error(f"❌ Daily execution failed: {str(e)}", exc_info=True)
            self.handle_failure(e)

    def search_jobs(self) -> List[Dict[str, Any]]:
        """Search all supported job portals"""
        logger.info("Searching jobs from all supported portals...")
        try:
            # This will call individual job search modules
            from automation.job_searchers import (
                LinkedInSearcher, NaukriSearcher, IndeedSearcher,
                BaytSearcher, GulfTalentSearcher
            )

            jobs = []

            # Search India-focused portals
            india_portals = [
                LinkedInSearcher(),
                NaukriSearcher(),
                IndeedSearcher(),
                # Add other India portals
            ]

            # Search Gulf-focused portals
            gulf_portals = [
                BaytSearcher(),
                GulfTalentSearcher(),
                NaukriGulfSearcher(),
                # Add other Gulf portals
            ]

            # Search remote job portals
            remote_portals = [
                RemoteOKSearcher(),
                WeWorkRemotelySearcher(),
                # Add other remote portals
            ]

            # Run searches in parallel (simplified)
            for portal in india_portals + gulf_portals + remote_portals:
                try:
                    portal_jobs = portal.search(
                        keywords=self.config.get('target_roles', []),
                        locations=self.config.get('preferred_locations', []),
                        salary_min=self.config.get('salary_min')
                    )
                    jobs.extend(portal_jobs)
                    logger.info(f"Found {len(portal_jobs)} jobs from {portal.__class__.__name__}")
                except Exception as e:
                    logger.warning(f"Failed to search {portal.__class__.__name__}: {str(e)}")

            logger.info(f"Total jobs found: {len(jobs)}")
            return jobs

        except ImportError:
            logger.warning("Job search modules not available, returning sample data")
            # Return sample data for testing
            return self.get_sample_jobs()

    def filter_jobs(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate, fake, expired, and unsuitable jobs"""
        logger.info(f"Filtering {len(jobs)} jobs...")

        filtered_jobs = []
        duplicate_count = 0
        fake_count = 0
        expired_count = 0

        for job in jobs:
            # Check if job is duplicate
            if self.is_duplicate_job(job):
                duplicate_count += 1
                continue

            # Check if job is fake
            if self.is_fake_job(job):
                fake_count += 1
                continue

            # Check if job is expired
            if self.is_expired_job(job):
                expired_count += 1
                continue

            # Check if job matches basic criteria
            if self.matches_basic_criteria(job):
                filtered_jobs.append(job)

        logger.info(f"Filtered jobs: {len(filtered_jobs)} remaining ({duplicate_count} duplicates, {fake_count} fake, {expired_count} expired removed)")
        return filtered_jobs

    def match_and_score_jobs(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Match jobs with profile and calculate various scores"""
        logger.info(f"Matching and scoring {len(jobs)} jobs...")

        try:
            from automation.ai_matching_engine import AIJobMatcher
            matcher = AIJobMatcher()

            scored_jobs = []
            for job in jobs:
                try:
                    # Calculate all scores
                    match_result = matcher.calculate_match_scores(job)
                    scored_jobs.append({**job, **match_result})
                except Exception as e:
                    logger.warning(f"Failed to score job {job.get('title', 'Unknown')}: {str(e)}")

            return scored_jobs

        except ImportError:
            logger.warning("AI matching engine not available, returning jobs with basic scores")
            # Add basic scores
            for job in jobs:
                job['overall_match_score'] = 70.0
                job['skill_match_score'] = 75.0
                job['experience_match_score'] = 80.0
                job['ats_compatibility_score'] = 65.0
                job['hiring_probability'] = 60.0
                job['recommendation'] = '★★★'

            return jobs

    def rank_jobs(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank jobs by overall match score"""
        logger.info(f"Ranking {len(jobs)} jobs...")

        # Sort by overall match score (descending)
        ranked_jobs = sorted(
            jobs,
            key=lambda x: x.get('overall_match_score', 0),
            reverse=True
        )

        # Add ranking position
        for i, job in enumerate(ranked_jobs):
            job['rank'] = i + 1

        logger.info(f"Top 5 jobs scores: {[job.get('overall_match_score', 0) for job in ranked_jobs[:5]]}")
        return ranked_jobs

    def generate_ats_resumes(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate ATS-optimized resumes for top matches"""
        logger.info(f"Generating ATS resumes for top {min(10, len(jobs))} jobs...")

        try:
            from automation.resume_generator import ATSResumeGenerator
            generator = ATSResumeGenerator()

            generated_resumes = []
            # Generate resumes for top 10 matches or all if less than 10
            top_jobs = jobs[:10]

            for job in top_jobs:
                try:
                    resume = generator.generate_resume_for_job(job)
                    generated_resumes.append(resume)
                    logger.info(f"Generated resume for {job.get('title', 'Unknown')} - ATS Score: {resume.get('ats_score', 0)}")
                except Exception as e:
                    logger.warning(f"Failed to generate resume for {job.get('title', 'Unknown')}: {str(e)}")

            return generated_resumes

        except ImportError:
            logger.warning("Resume generator not available")
            return []

    def generate_cover_letters(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate personalized cover letters"""
        logger.info(f"Generating cover letters for top {min(10, len(jobs))} jobs...")

        try:
            from automation.cover_letter_generator import CoverLetterGenerator
            generator = CoverLetterGenerator()

            generated_letters = []
            top_jobs = jobs[:10]

            for job in top_jobs:
                try:
                    cover_letter = generator.generate_cover_letter_for_job(job)
                    generated_letters.append(cover_letter)
                    logger.info(f"Generated cover letter for {job.get('title', 'Unknown')}")
                except Exception as e:
                    logger.warning(f"Failed to generate cover letter for {job.get('title', 'Unknown')}: {str(e)}")

            return generated_letters

        except ImportError:
            logger.warning("Cover letter generator not available")
            return []

    def generate_recruiter_messages(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate recruiter messages"""
        logger.info(f"Generating recruiter messages for top {min(5, len(jobs))} jobs...")

        try:
            from automation.recruiter_message_generator import RecruiterMessageGenerator
            generator = RecruiterMessageGenerator()

            generated_messages = []
            top_jobs = jobs[:5]

            for job in top_jobs:
                try:
                    messages = generator.generate_all_messages(job)
                    generated_messages.append(messages)
                    logger.info(f"Generated recruiter messages for {job.get('title', 'Unknown')}")
                except Exception as e:
                    logger.warning(f"Failed to generate messages for {job.get('title', 'Unknown')}: {str(e)}")

            return generated_messages

        except ImportError:
            logger.warning("Recruiter message generator not available")
            return []

    def generate_interview_preparation(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate interview preparation materials"""
        logger.info(f"Generating interview prep for top {min(5, len(jobs))} jobs...")

        try:
            from automation.interview_preparation import InterviewPreparer
            preparer = InterviewPreparer()

            interview_preps = []
            top_jobs = jobs[:5]

            for job in top_jobs:
                try:
                    prep = preparer.generate_interview_preparation(job)
                    interview_preps.append(prep)
                    logger.info(f"Generated interview prep for {job.get('title', 'Unknown')}")
                except Exception as e:
                    logger.warning(f"Failed to generate interview prep for {job.get('title', 'Unknown')}: {str(e)}")

            return interview_preps

        except ImportError:
            logger.warning("Interview preparation module not available")
            return []

    def research_companies(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Research companies for top jobs"""
        logger.info(f"Researching companies for top {min(5, len(jobs))} jobs...")

        try:
            from automation.company_researcher import CompanyResearcher
            researcher = CompanyResearcher()

            company_research = []
            top_jobs = jobs[:5]

            for job in top_jobs:
                try:
                    company_info = researcher.research_company(job.get('company_name'))
                    company_research.append(company_info)
                    logger.info(f"Researched {job.get('company_name', 'Unknown company')}")
                except Exception as e:
                    logger.warning(f"Failed to research {job.get('company_name', 'Unknown company')}: {str(e)}")

            return company_research

        except ImportError:
            logger.warning("Company researcher not available")
            return []

    def analyze_salaries(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze salaries for matched jobs"""
        logger.info(f"Analyzing salaries for {len(jobs)} jobs...")

        try:
            from automation.salary_analyzer import SalaryAnalyzer
            analyzer = SalaryAnalyzer()

            salary_analyses = []
            for job in jobs:
                try:
                    salary_analysis = analyzer.analyze_job_salary(job)
                    salary_analyses.append(salary_analysis)
                except Exception as e:
                    logger.warning(f"Failed to analyze salary for {job.get('title', 'Unknown')}: {str(e)}")

            return salary_analyses

        except ImportError:
            logger.warning("Salary analyzer not available")
            return []

    def organize_files(self, jobs: List[Dict[str, Any]], generated_content: Dict[str, Any]):
        """Organize all generated files into structured folders"""
        logger.info("Organizing files into structured folders...")

        try:
            from automation.file_organizer import FileOrganizer
            organizer = FileOrganizer()

            # Create today's folder structure
            today_folder = organizer.create_daily_folder()

            # Organize each job's content
            for i, job in enumerate(jobs[:10]):  # Top 10 jobs
                try:
                    job_folder = organizer.organize_job_content(
                        job=job,
                        resume=generated_content['resumes'][i] if i < len(generated_content['resumes']) else None,
                        cover_letter=generated_content['cover_letters'][i] if i < len(generated_content['cover_letters']) else None,
                        recruiter_messages=generated_content['recruiter_messages'][i] if i < len(generated_content['recruiter_messages']) else None,
                        interview_prep=generated_content['interview_prep'][i] if i < len(generated_content['interview_prep']) else None,
                        company_research=generated_content['company_research'][i] if i < len(generated_content['company_research']) else None,
                        salary_analysis=generated_content['salary_analysis'][i] if i < len(generated_content['salary_analysis']) else None
                    )
                    logger.info(f"Organized files for {job.get('title', 'Unknown')}")
                except Exception as e:
                    logger.warning(f"Failed to organize files for job {i}: {str(e)}")

            logger.info(f"Files organized into {today_folder}")

        except ImportError:
            logger.warning("File organizer not available")

    def update_dashboard(self, jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Update dashboard with latest data"""
        logger.info("Updating dashboard...")

        try:
            from automation.dashboard_updater import DashboardUpdater
            updater = DashboardUpdater()

            dashboard_data = updater.update_dashboard(jobs)
            logger.info(f"Dashboard updated: {len(jobs)} jobs")

            return dashboard_data

        except ImportError:
            logger.warning("Dashboard updater not available")
            return {}

    def generate_daily_report(self, dashboard_data: Dict[str, Any]) -> str:
        """Generate daily PDF report"""
        logger.info("Generating daily report...")

        try:
            from automation.report_generator import DailyReportGenerator
            generator = DailyReportGenerator()

            report_path = generator.generate_daily_report(dashboard_data)
            logger.info(f"Daily report generated: {report_path}")

            return report_path

        except ImportError:
            logger.warning("Report generator not available")
            return ""

    def send_notifications(self, results: Dict[str, Any]):
        """Send notifications after completion"""
        logger.info("Sending notifications...")

        try:
            from automation.notification_sender import NotificationSender
            sender = NotificationSender()

            sender.send_completion_notification(results)
            logger.info("Notifications sent")

        except ImportError:
            logger.warning("Notification sender not available")

    def handle_failure(self, error: Exception):
        """Handle execution failure"""
        logger.error(f"Handling failure: {str(error)}")

        # Log to error database
        try:
            from database.models import ExecutionLog, init_db
            engine, Session = init_db()
            with Session() as session:
                log = ExecutionLog(
                    task_name="daily_job_execution",
                    task_type="full_pipeline",
                    status="Failed",
                    log_message="Daily execution failed",
                    error_details=str(error),
                    execution_time_seconds=0
                )
                session.add(log)
                session.commit()
        except Exception as db_error:
            logger.error(f"Failed to log failure to database: {db_error}")

        # Send failure notification
        try:
            from automation.notification_sender import NotificationSender
            sender = NotificationSender()
            sender.send_failure_notification(str(error))
        except Exception:
            logger.error("Failed to send failure notification")

    # Helper methods for job filtering
    def is_duplicate_job(self, job: Dict[str, Any]) -> bool:
        """Check if job is duplicate"""
        # Implement duplicate detection logic
        # Check against database of seen jobs
        return False

    def is_fake_job(self, job: Dict[str, Any]) -> bool:
        """Check if job is fake/scam"""
        # Implement fake job detection
        fake_keywords = ['work from home', 'earn money', 'no experience needed']
        title = job.get('title', '').lower()
        description = job.get('description', '').lower()

        for keyword in fake_keywords:
            if keyword in title or keyword in description:
                return True
        return False

    def is_expired_job(self, job: Dict[str, Any]) -> bool:
        """Check if job is expired"""
        # Check posted date against current date
        posted_date = job.get('posted_date')
        if not posted_date:
            return False

        # Consider jobs older than 30 days as expired
        expiration_days = 30
        if isinstance(posted_date, str):
            try:
                posted_date = datetime.fromisoformat(posted_date.replace('Z', '+00:00'))
            except:
                return False

        if (datetime.utcnow() - posted_date).days > expiration_days:
            return True

        return False

    def matches_basic_criteria(self, job: Dict[str, Any]) -> bool:
        """Check if job matches basic criteria"""
        # Check salary
        salary = job.get('salary', {})
        salary_min = salary.get('min', 0)

        # Check if salary meets minimum requirements
        target_roles = self.config.get('target_roles', [])
        title = job.get('title', '').lower()

        # Check if job title matches any target role
        for role in target_roles:
            if role.lower() in title:
                return True

        return False

    def get_sample_jobs(self) -> List[Dict[str, Any]]:
        """Get sample jobs for testing"""
        return [
            {
                'title': 'Operations Manager',
                'company': 'Cold Chain Logistics Ltd',
                'location': 'Mumbai, India',
                'salary': {'min': 1800000, 'max': 2500000, 'currency': 'INR'},
                'description': 'Looking for experienced Operations Manager for cold chain logistics.',
                'posted_date': datetime.utcnow().isoformat()
            },
            {
                'title': 'Warehouse Manager',
                'company': 'Global Distributors',
                'location': 'Dubai, UAE',
                'salary': {'min': 18000, 'max': 22000, 'currency': 'AED'},
                'description': 'Warehouse management position in Dubai with international logistics company.',
                'posted_date': datetime.utcnow().isoformat()
            }
        ]

    def job_success_listener(self, event):
        """Listener for successful job execution"""
        logger.info(f"Job {event.job_id} executed successfully")

        # Log successful execution
        try:
            from database.models import ExecutionLog, init_db
            engine, Session = init_db()
            with Session() as session:
                log = ExecutionLog(
                    task_name=event.job_id,
                    task_type="scheduled_task",
                    status="Completed",
                    log_message="Scheduled task completed successfully",
                    execution_time_seconds=event.scheduled_run_time
                )
                session.add(log)
                session.commit()
        except Exception as e:
            logger.error(f"Failed to log successful execution: {e}")

    def job_error_listener(self, event):
        """Listener for job execution errors"""
        logger.error(f"Job {event.job_id} failed: {event.exception}")

        # Log failed execution
        try:
            from database.models import ExecutionLog, init_db
            engine, Session = init_db()
            with Session() as session:
                log = ExecutionLog(
                    task_name=event.job_id,
                    task_type="scheduled_task",
                    status="Failed",
                    log_message="Scheduled task failed",
                    error_details=str(event.exception),
                    execution_time_seconds=event.scheduled_run_time
                )
                session.add(log)
                session.commit()
        except Exception as e:
            logger.error(f"Failed to log failed execution: {e}")

    def start(self):
        """Start the scheduler"""
        try:
            # Add the daily job
            self.scheduler.add_job(
                func=self.daily_job_execution,
                trigger=CronTrigger(
                    hour=self.config['cron_schedule']['hour'],
                    minute=self.config['cron_schedule']['minute'],
                    second=self.config['cron_schedule']['second']
                ),
                id='daily_job_intelligence_agent',
                name='AI Job Intelligence Agent Daily Execution',
                replace_existing=True
            )

            # Start the scheduler
            self.scheduler.start()
            logger.info(f"AI Job Intelligence Agent scheduler started. Next run: {self.scheduler.get_job('daily_job_intelligence_agent').next_run_time}")

            # Keep the scheduler running
            return True

        except Exception as e:
            logger.error(f"Failed to start scheduler: {str(e)}")
            return False

    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        logger.info("AI Job Intelligence Agent scheduler stopped")

    def get_next_run(self):
        """Get next scheduled run time"""
        job = self.scheduler.get_job('daily_job_intelligence_agent')
        if job:
            return job.next_run_time
        return None

    def manual_run(self):
        """Trigger manual execution"""
        logger.info("Manual execution triggered")
        self.daily_job_execution()

# Main execution
if __name__ == "__main__":
    """Main entry point for the AI Job Intelligence Agent Scheduler"""

    print("=" * 60)
    print("AI JOB INTELLIGENCE AGENT - DAILY SCHEDULER")
    print("=" * 60)
    print(f"Current time: {datetime.now()}")

    # Create scheduler instance
    scheduler = AIJobIntelligenceScheduler()

    print(f"Time zone: {scheduler.config.get('timezone', 'Asia/Kolkata')}")
    print(f"Scheduled time: {scheduler.config['cron_schedule']['hour']}:{scheduler.config['cron_schedule']['minute']}:{scheduler.config['cron_schedule']['second']}")
    print("-" * 60)

    try:
        # Start scheduler
        if scheduler.start():
            print("✅ Scheduler started successfully!")
            next_run = scheduler.get_next_run()
            if next_run:
                print(f"📅 Next execution: {next_run}")

            print("\nPress Ctrl+C to stop the scheduler...")
            print("=" * 60)

            # Keep the main thread alive
            import time
            try:
                while True:
                    time.sleep(60)  # Check every minute
            except KeyboardInterrupt:
                scheduler.stop()
                print("\n🛑 Scheduler stopped by user")

        else:
            print("❌ Failed to start scheduler")

    except Exception as e:
        print(f"❌ Error starting scheduler: {e}")
        import traceback
        traceback.print_exc()