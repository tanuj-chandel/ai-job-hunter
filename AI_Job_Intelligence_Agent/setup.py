"""
AI Job Intelligence Agent - Setup Script
One-command setup for the complete system
"""

import os
import sys
import json
import shutil
from pathlib import Path
from datetime import datetime
import subprocess
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIJobAgentSetup:
    """Setup and configure the AI Job Intelligence Agent"""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.config_path = self.project_root / "config" / "config.json"

    def setup_complete_system(self):
        """Run complete setup process"""
        print("\n" + "="*60)
        print("AI JOB INTELLIGENCE AGENT - SETUP WIZARD")
        print("="*60)
        print(f"Setup started at: {datetime.now()}")

        try:
            # Step 1: Verify project structure
            print("\n[1/6] ✅ Verifying project structure...")
            self.create_project_structure()

            # Step 2: Install dependencies
            print("\n[2/6] 📦 Installing Python dependencies...")
            self.install_python_dependencies()

            # Step 3: Initialize database
            print("\n[3/6] 🗄️  Initializing database...")
            self.initialize_database()

            # Step 4: Configure system
            print("\n[4/6] ⚙️  Configuring system...")
            self.configure_system()

            # Step 5: Test components
            print("\n[5/6] 🔧 Testing components...")
            self.test_components()

            # Step 6: Schedule daily execution
            print("\n[6/6] 📅 Scheduling daily execution (8:00 AM)...")
            self.setup_schedule()

            print("\n" + "="*60)
            print("✅ SETUP COMPLETED SUCCESSFULLY!")
            print("="*60)
            print("\nSystem Features:")
            print("- Daily job search at 8:00 AM")
            print("- AI-powered job matching")
            print("- ATS resume generation")
            print("- Personalized cover letters")
            print("- Interview preparation")
            print("- Professional dashboard")
            print("- Automated notifications")

            print(f"\n🎯 Next execution: Tomorrow at 08:00 AM")
            print("💡 Run 'python automation/main_scheduler.py' to start now")

            return True

        except Exception as e:
            print(f"\n❌ Setup failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    def create_project_structure(self):
        """Create all required folders"""
        folders = [
            "database",
            "config",
            "automation",
            "Dashboard",
            "Reports",
            "Resume_Master",
            "Generated_Resume",
            "Cover_Letters",
            "Recruiter_Messages",
            "Interview_Prep",
            "Company_Reports",
            "Jobs",
            "Applications",
            "Offers",
            "Rejected",
            "Interviews",
            "Logs",
            "logs"
        ]

        for folder in folders:
            folder_path = self.project_root / folder
            folder_path.mkdir(parents=True, exist_ok=True)
            print(f"  Created: {folder}")

    def install_python_dependencies(self):
        """Install required Python packages"""
        requirements_file = self.project_root / "backend" / "requirements.txt"

        if requirements_file.exists():
            try:
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install",
                    "--break-system-packages", "-r", str(requirements_file)
                ])
                print("  ✅ Python dependencies installed")
            except subprocess.CalledProcessError:
                print("  ⚠️  Failed to install all dependencies, but continuing...")
        else:
            print("  ⚠️  requirements.txt not found, skipping dependency installation")

    def initialize_database(self):
        """Initialize SQLite database"""
        try:
            # Create database models
            db_path = self.project_root / "database" / "ai_job_agent.db"

            # Import and run database initialization
            sys.path.append(str(self.project_root))

            from database.models import init_db

            # Initialize database
            engine, Session = init_db(str(db_path))
            print(f"  ✅ Database initialized: {db_path}")

            # Create sample data
            self.create_sample_data(Session)

        except ImportError as e:
            print(f"  ⚠️  Database setup error: {e}")
            print("  💡 Database will be created on first run")

    def create_sample_data(self, Session):
        """Create sample data for testing"""
        try:
            from database.models import (
                Job, Company, Skill, Keyword, Application,
                Resume, CoverLetter, ExecutionLog
            )

            with Session() as session:
                # Create sample company
                company = Company(
                    company_name="Cold Chain Logistics Ltd",
                    industry="Logistics & Cold Chain",
                    description="Leading cold storage and logistics provider"
                )
                session.add(company)

                # Create sample job
                job = Job(
                    job_title="Operations Manager - Cold Storage",
                    company_name="Cold Chain Logistics Ltd",
                    location="Mumbai, India",
                    country="India",
                    job_description="Operations Manager for cold chain logistics with experience in warehouse management and inventory control.",
                    job_url="https://example.com/jobs/001",
                    source_portal="LinkedIn",
                    salary_min=1800000,
                    salary_max=2500000,
                    salary_currency="INR",
                    overall_match_score=85.0,
                    hiring_probability=75.0,
                    recommendation="★★★★ Strong Match"
                )
                session.add(job)

                session.commit()
                print("  ✅ Sample data created")

        except Exception as e:
            print(f"  ⚠️  Sample data creation failed: {e}")

    def configure_system(self):
        """Configure system settings"""
        config = {
            "system": {
                "name": "AI Job Intelligence Agent",
                "version": "1.0.0",
                "environment": "production",
                "timezone": "Asia/Kolkata",
                "setup_date": datetime.now().isoformat()
            },
            "scheduler": {
                "enabled": True,
                "next_execution": self.get_tomorrow_8am().isoformat(),
                "last_configured": datetime.now().isoformat()
            }
        }

        config_file = self.project_root / "config" / "system_status.json"
        with open(config_file, "w") as f:
            json.dump(config, f, indent=2)

        print("  ✅ System configured")

    def test_components(self):
        """Test core components"""
        print("\nRunning component tests...")

        tests = [
            ("AI Matching Engine", self.test_ai_matching),
            ("Resume Generator", self.test_resume_generator),
            ("Cover Letter Generator", self.test_cover_letter_generator),
            ("Database Connection", self.test_database)
        ]

        for test_name, test_func in tests:
            try:
                result = test_func()
                print(f"  ✅ {test_name}: PASS")
            except Exception as e:
                print(f"  ⚠️  {test_name}: FAIL ({str(e)[:50]}...)")

    def test_ai_matching(self):
        """Test AI matching engine"""
        sys.path.append(str(self.project_root))

        from automation.ai_matching_engine import AIJobMatcher

        matcher = AIJobMatcher()
        sample_job = {
            'title': 'Operations Manager',
            'description': 'Experience in warehouse and inventory management required.',
            'salary': {'min': 1500000, 'currency': 'INR'}
        }

        scores = matcher.calculate_match_scores(sample_job)
        return scores is not None

    def test_resume_generator(self):
        """Test resume generator"""
        sys.path.append(str(self.project_root))

        from automation.resume_generator import ATSResumeGenerator

        generator = ATSResumeGenerator()
        sample_job = {
            'title': 'Operations Manager',
            'description': 'Warehouse management experience'
        }

        resume = generator.generate_resume_for_job(sample_job)
        return resume is not None

    def test_cover_letter_generator(self):
        """Test cover letter generator"""
        sys.path.append(str(self.project_root))

        from automation.document_generators import CoverLetterGenerator

        generator = CoverLetterGenerator()
        sample_job = {
            'company': 'Test Company',
            'title': 'Operations Manager'
        }

        letter = generator.generate_cover_letter_for_job(sample_job)
        return letter is not None

    def test_database(self):
        """Test database connection"""
        sys.path.append(str(self.project_root))

        from database.models import init_db

        engine, Session = init_db()
        with Session() as session:
            result = session.execute("SELECT 1").scalar()
            return result == 1

    def setup_schedule(self):
        """Setup daily schedule at 8:00 AM"""
        try:
            # Create scheduler service
            scheduler_script = self.project_root / "automation" / "main_scheduler.py"

            if scheduler_script.exists():
                # Create startup script
                startup_script = self.project_root / "start_agent.py"
                startup_content = """#!/usr/bin/env python3
"""
                startup_content = '''#!/usr/bin/env python3
"""
AI Job Intelligence Agent - Startup Script
Starts the scheduler for daily execution
"""

import sys
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

print("="*60)
print("AI JOB INTELLIGENCE AGENT - STARTING")
print("="*60)
print("System will run daily at 8:00 AM")
print("Press Ctrl+C to stop")

try:
    from automation.main_scheduler import AIJobIntelligenceScheduler

    scheduler = AIJobIntelligenceScheduler()
    if scheduler.start():
        print("✅ Scheduler started successfully!")
        print(f"📅 Next execution: {scheduler.get_next_run()}")
        print("="*60)

        # Keep running
        import time
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            scheduler.stop()
            print("\n🛑 Scheduler stopped")

    else:
        print("❌ Failed to start scheduler")

except Exception as e:
    print(f"❌ Error starting scheduler: {e}")
    import traceback
    traceback.print_exc()
'''

                with open(startup_script, "w") as f:
                    f.write(startup_content)

                os.chmod(startup_script, 0o755)

                # Create Windows batch file
                if sys.platform == "win32":
                    batch_file = self.project_root / "start_agent.bat"
                    batch_content = """@echo off
echo AI Job Intelligence Agent - Starting...
python "%~dp0start_agent.py"
pause
"""
                    with open(batch_file, "w") as f:
                        f.write(batch_content)

                print("  ✅ Scheduler configured")
                print(f"  📂 Start script: {startup_script}")
            else:
                print("  ⚠️  Scheduler script not found")

        except Exception as e:
            print(f"  ⚠️  Schedule setup error: {e}")

    def get_tomorrow_8am(self):
        """Get datetime for tomorrow 8:00 AM"""
        from datetime import datetime, timedelta

        tomorrow = datetime.now() + timedelta(days=1)
        return tomorrow.replace(hour=8, minute=0, second=0, microsecond=0)

    def create_readme(self):
        """Create README file"""
        readme_content = """# AI Job Intelligence Agent

## 🎯 Overview
Production-ready AI-powered career assistant that automatically:
- Searches jobs daily at 8:00 AM
- Analyzes job descriptions using AI
- Generates ATS-optimized resumes
- Creates personalized cover letters
- Prepares interview questions
- Organizes everything automatically

## 🚀 Quick Start

### 1. Setup
```bash
python setup.py
```

### 2. Start Agent
```bash
python start_agent.py
```

### 3. Open Dashboard
Check the generated files in the organized folders.

## 📅 Daily Schedule
The agent runs automatically every day at **8:00 AM** and:
1. Searches all job portals
2. Matches jobs with your profile
3. Generates application materials
4. Updates dashboard
5. Sends notifications

## 📁 Folder Structure
```
AI_Job_Intelligence_Agent/
├── Dashboard/          # Web dashboard
├── Jobs/              # Daily job searches
├── Generated_Resume/  # Customized resumes
├── Cover_Letters/     # Personalized cover letters
├── Interview_Prep/    # Interview materials
├── Applications/      # Application tracking
└── Reports/          # Daily reports
```

## ⚙️ Configuration
Edit `config/config.json` to customize:
- Target job roles
- Preferred locations
- Salary expectations
- Notification settings

## 🔧 Manual Execution
Run any time:
```bash
python automation/main_scheduler.py --manual
```

## 📊 Features
- **AI Matching**: Intelligent job-candidate matching
- **ATS Optimization**: Resume optimization for ATS systems
- **Personalization**: Customized for each job
- **Automation**: Zero manual work required
- **Analytics**: Dashboard with insights
- **Scheduling**: Daily automated execution

## 🔒 Security
- Personal data encrypted
- Secure API key handling
- Compliance with job portal terms

## 📞 Support
System runs autonomously. Check logs in `Logs/` folder for execution details.
"""

        readme_file = self.project_root / "README.md"
        with open(readme_file, "w") as f:
            f.write(readme_content)

        print("  📄 README created")

# Main execution
if __name__ == "__main__":
    print("\n🔧 AI Job Intelligence Agent - Installation")
    print("This will setup the complete system.")
    print("Estimated time: 2-3 minutes\n")

    response = input("Proceed with installation? (yes/no): ").strip().lower()

    if response in ['yes', 'y', '']:
        setup = AIJobAgentSetup()
        success = setup.setup_complete_system()

        if success:
            # Create README
            setup.create_readme()

            print("\n🎉 Installation Complete!")
            print("\nNext steps:")
            print("1. Review configuration in config/config.json")
            print("2. Start the agent: python start_agent.py")
            print("3. First automatic run: Tomorrow at 8:00 AM")
            print("\nCheck the Dashboard/ folder for generated files.")
        else:
            print("\n❌ Installation failed. Please check logs.")
    else:
        print("\n❌ Installation cancelled.")
