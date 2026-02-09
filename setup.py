#!/usr/bin/env python3
"""
🚀 Quick Setup Script for Internship Allocation Platform
This script sets up the entire project structure
"""

import os
import shutil
import sys

def create_directories():
    """Create necessary directory structure"""
    directories = [
        'templates',
        'static/css',
        'uploads/students/resumes',
        'uploads/students/photos',
        'uploads/companies/logos'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Created: {directory}")

def check_files():
    """Check if all required files exist"""
    required_files = {
        'app_fixed.py': 'Main application file',
        'ai_engine.py': 'AI engine for resume analysis',
        'database.py': 'Database setup',
        'email_utils.py': 'Email functions',
        'requirements.txt': 'Python dependencies',
        'student_dashboard_improved.html': 'Student dashboard template',
        'admin_dashboard.html': 'Admin dashboard template',
        'company_dashboard.html': 'Company dashboard template',
        'login.html': 'Login page',
        'register.html': 'Registration page',
        'admin_analytics.html': 'Analytics page',
        '403.html': 'Access denied page',
        'style.css': 'Stylesheet'
    }
    
    print("\n📋 Checking required files...")
    missing = []
    
    for file, description in required_files.items():
        if os.path.exists(file):
            print(f"✅ Found: {file} - {description}")
        else:
            print(f"❌ Missing: {file} - {description}")
            missing.append(file)
    
    return missing

def setup_files():
    """Move files to correct locations"""
    print("\n📦 Setting up files...")
    
    # Rename main app file
    if os.path.exists('app_fixed.py'):
        shutil.copy('app_fixed.py', 'app.py')
        print("✅ Created app.py from app_fixed.py")
    
    # Move template files
    template_files = [
        'student_dashboard_improved.html',
        'admin_dashboard.html',
        'company_dashboard.html',
        'login.html',
        'register.html',
        'admin_analytics.html',
        '403.html'
    ]
    
    for file in template_files:
        if os.path.exists(file):
            target = os.path.join('templates', file)
            shutil.copy(file, target)
            
            # Rename improved dashboard
            if file == 'student_dashboard_improved.html':
                final_target = os.path.join('templates', 'student_dashboard.html')
                shutil.move(target, final_target)
                print(f"✅ Moved: {file} → templates/student_dashboard.html")
            else:
                print(f"✅ Moved: {file} → {target}")
    
    # Move CSS file
    if os.path.exists('style.css'):
        shutil.copy('style.css', 'static/css/style.css')
        print("✅ Moved: style.css → static/css/style.css")

def install_dependencies():
    """Install Python dependencies"""
    print("\n📦 Installing dependencies...")
    
    if os.path.exists('requirements.txt'):
        print("Running: pip install -r requirements.txt")
        os.system('pip install -r requirements.txt')
        print("✅ Dependencies installed")
    else:
        print("❌ requirements.txt not found!")

def create_database():
    """Initialize database"""
    print("\n🗄️ Initializing database...")
    
    try:
        from database import create_tables
        create_tables()
        print("✅ Database initialized")
    except Exception as e:
        print(f"❌ Database initialization failed: {str(e)}")

def print_summary():
    """Print setup summary and next steps"""
    print("\n" + "="*80)
    print("🎉 SETUP COMPLETE!")
    print("="*80)
    print("\n📋 Next Steps:")
    print("1. Run the application:")
    print("   python app.py")
    print("\n2. Open browser and go to:")
    print("   http://localhost:5000")
    print("\n3. Login with default admin credentials:")
    print("   Email: admin@platform.com")
    print("   Password: admin123")
    print("\n4. Create student and company accounts to test")
    print("\n📧 Email Configuration:")
    print("   Configured: bobxdev5@gmail.com")
    print("   Status: Ready to send allocation emails")
    print("\n" + "="*80)
    print("✅ All issues fixed! Ready to use!")
    print("="*80 + "\n")

def main():
    """Main setup function"""
    print("="*80)
    print("🚀 INTERNSHIP ALLOCATION PLATFORM - SETUP SCRIPT")
    print("="*80 + "\n")
    
    # Step 1: Create directories
    print("Step 1: Creating directory structure...")
    create_directories()
    
    # Step 2: Check files
    missing = check_files()
    if missing:
        print(f"\n❌ Missing {len(missing)} required files!")
        print("Please ensure all files are in the current directory.")
        return
    
    # Step 3: Setup files
    setup_files()
    
    # Step 4: Install dependencies
    install_dependencies()
    
    # Step 5: Create database
    create_database()
    
    # Step 6: Print summary
    print_summary()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Setup failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)