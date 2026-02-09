# 🎓 Enhanced Internship Allocation Platform

## 🆕 New Features

### 1. **ATS-Powered Resume Scanning**
- Resume scoring is now **primarily based on actual resume content**, not just profile skills
- Advanced analysis against specific job descriptions
- Comprehensive skill extraction from resume text
- Fair scoring based on:
  - Resume quality and structure
  - Job-specific keywords matching
  - Technical skills alignment with requirements
  - Experience and quantifiable achievements

### 2. **Email Notification System**
- Automatic email notifications to selected candidates
- Professional HTML email templates with:
  - Company details
  - Domain/role information
  - Stipend and location
  - Student's rank and ATS match score
  - Next steps and instructions
- Bulk email sending capability
- Email delivery status tracking

### 3. **Improved Matching Algorithm**
- 60% weight on resume content analysis (ATS scoring)
- 20% weight on CGPA
- 10% weight on experience
- 10% bonus for extracted skills matching job requirements
- Domain must match and CGPA must meet minimum requirements

## 📋 Setup Instructions

### Prerequisites
- Python 3.8 or higher
- Gmail account with App Password (for email functionality)

### Installation

1. **Install Required Packages**
```bash
pip install -r requirements.txt
```

2. **Configure Email Settings**

For Gmail, you need to create an App Password:
- Go to Google Account Settings
- Security → 2-Step Verification → App Passwords
- Generate a new app password for "Mail"
- Copy the 16-character password

Set environment variables:

**Linux/Mac:**
```bash
export MAIL_USERNAME="your-email@gmail.com"
export MAIL_PASSWORD="your-16-char-app-password"
```

**Windows (Command Prompt):**
```cmd
set MAIL_USERNAME=your-email@gmail.com
set MAIL_PASSWORD=your-16-char-app-password
```

**Windows (PowerShell):**
```powershell
$env:MAIL_USERNAME="your-email@gmail.com"
$env:MAIL_PASSWORD="your-16-char-app-password"
```

Alternatively, you can hardcode them in `app_enhanced.py` (lines 30-31):
```python
app.config['MAIL_USERNAME'] = 'your-email@gmail.com'
app.config['MAIL_PASSWORD'] = 'your-16-char-app-password'
```

3. **File Structure**
```
project/
├── app_enhanced.py              # Main application file (enhanced)
├── ai_engine_enhanced.py        # Enhanced AI engine with ATS
├── email_utils.py               # Email notification utilities
├── database.py                  # Database operations
├── requirements.txt             # Python dependencies
├── uploads/                     # File uploads directory
│   ├── students/
│   │   ├── resumes/            # Student resumes
│   │   └── photos/             # Student photos
│   └── companies/
│       └── logos/              # Company logos
├── templates/                   # HTML templates
│   ├── admin_dashboard_enhanced.html
│   ├── student_dashboard.html
│   ├── company_dashboard.html
│   ├── login.html
│   ├── register.html
│   └── 403.html
└── static/
    └── css/
        └── style.css
```

4. **Run the Application**
```bash
python app_enhanced.py
```

The application will start on `http://localhost:5000`

### Default Admin Login
- **Email:** admin@platform.com
- **Password:** admin123

## 🎯 How to Use

### For Admin

1. **Login** with admin credentials
2. **Monitor** registered students and companies
3. **Configure Email** (if sending notifications):
   - Check the "Send allocation emails" checkbox before running allocation
   - Ensure MAIL_USERNAME and MAIL_PASSWORD are set
4. **Run Allocation**:
   - Click "Run Smart Allocation Now"
   - System will analyze resumes against job descriptions
   - ATS scores are calculated for each student-position pair
   - Emails are sent to allocated students (if enabled)

### For Students

1. **Register** as a student
2. **Complete Profile**:
   - Add skills (comma-separated)
   - Enter CGPA, domain, experience
   - **Upload Resume** (PDF) - Most Important!
3. **Resume Analysis**:
   - System extracts skills automatically from resume
   - Resume is scored (must be ≥50/100 to save)
   - Get detailed feedback on resume quality
4. **Wait for Allocation**
5. **Check Email** for allocation notification

### For Companies

1. **Register** as a company
2. **Update Profile**:
   - Company name, location, contact details
   - Upload company logo
3. **Add Job Positions**:
   - Select domain
   - List required skills (comma-separated)
   - Set minimum CGPA
   - Specify number of openings and stipend
4. **View Allocated Students** after allocation

## 🔍 ATS Scoring Breakdown

The enhanced system scores resumes based on:

1. **Resume Quality (25 points)**
   - Word count (200-600 words optimal)
   - Section structure (Education, Experience, Skills, Projects, etc.)

2. **Job-Specific Keywords (30 points)**
   - Domain-relevant keywords (AI, Web Dev, Cybersecurity, etc.)
   - Industry-standard terminology

3. **Technical Skills Match (25 points)**
   - Exact match with required skills from job description
   - Comprehensive skill detection

4. **Experience & Impact (20 points)**
   - Achievement-oriented language
   - Quantifiable results (percentages, numbers)
   - Action verbs (achieved, improved, developed, etc.)

**Total: 100 points**

## 📧 Email Configuration for Different Providers

### Gmail (Recommended)
```python
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
```

### Outlook/Hotmail
```python
app.config['MAIL_SERVER'] = 'smtp-mail.outlook.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
```

### Yahoo
```python
app.config['MAIL_SERVER'] = 'smtp.mail.yahoo.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
```

### Custom SMTP Server
```python
app.config['MAIL_SERVER'] = 'your-smtp-server.com'
app.config['MAIL_PORT'] = 587  # or 465 for SSL
app.config['MAIL_USE_TLS'] = True  # or MAIL_USE_SSL = True
```

## 🛠️ Troubleshooting

### Email Not Sending
1. Check environment variables are set correctly
2. Verify Gmail App Password (not regular password)
3. Check spam folder for emails
4. Ensure 2-Step Verification is enabled in Gmail
5. Check console for error messages

### Resume Score Too Low
- Resume must have at least 100 characters
- Include relevant sections (Education, Experience, Skills)
- Add domain-specific keywords
- Include quantifiable achievements
- Use proper formatting and structure

### Allocation Not Working
- Ensure at least 1 student and 1 company exist
- Students must have complete profiles with resumes
- Companies must have added job positions
- Student's domain must match position domain
- Student's CGPA must meet minimum requirement

## 📊 Key Improvements

### Before (Original System)
- ❌ Relied on manually entered skills
- ❌ No resume content analysis
- ❌ Simple keyword matching
- ❌ No email notifications
- ❌ Profile skills weighted heavily

### After (Enhanced System)
- ✅ Analyzes actual resume content
- ✅ ATS-powered job description matching
- ✅ Comprehensive skill extraction
- ✅ Professional email notifications
- ✅ Resume content weighted 60%
- ✅ Fair scoring based on document quality

## 🔐 Security Notes

- Never commit email credentials to version control
- Always use environment variables for sensitive data
- Use App Passwords, not regular passwords
- Keep SECRET_KEY secure in production
- Use HTTPS in production environment

## 📝 Future Enhancements

- [ ] Interview scheduling system
- [ ] Multi-round allocation
- [ ] Student preferences and priorities
- [ ] Company rating and feedback
- [ ] Resume template suggestions
- [ ] PDF report generation
- [ ] Dashboard analytics improvements
- [ ] SMS notifications

## 🤝 Support

For issues or questions:
1. Check the troubleshooting section
2. Review console logs for error messages
3. Verify all environment variables are set
4. Ensure all dependencies are installed

## 📄 License

This project is for educational purposes.

---

**Built with ❤️ using Flask, Python, and AI**