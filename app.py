from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
import os
import traceback
import sqlite3
import fitz  # PyMuPDF
from ai_engine import (
    extract_skills_from_text,
    analyze_resume_quality,
    run_smart_allocation
)
from email_utils import send_allocation_email, send_bulk_allocation_emails
from openpyxl import Workbook
import io
from datetime import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from io import BytesIO
import base64

# ────────────────────────────────────────────────
#  CONFIGURATION
# ────────────────────────────────────────────────

app = Flask(__name__)
app.secret_key = "super_secret_key_please_change_in_production"
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Email configuration - FIXED WITH YOUR CREDENTIALS
app.config['MAIL_SERVER']      = 'smtp.gmail.com'
app.config['MAIL_PORT']        = 587
app.config['MAIL_USE_TLS']     = True
app.config['MAIL_USERNAME']    = 'bobxdev5@gmail.com'
app.config['MAIL_PASSWORD']    = 'furksvdzojgmhfan'
app.config['MAIL_DEFAULT_SENDER'] = 'bobxdev5@gmail.com'

mail = Mail(app)

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif'}

# ────────────────────────────────────────────────
#  HELPER FUNCTIONS
# ────────────────────────────────────────────────

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def role_required(required_role):
    """Decorator to ensure user has the correct role"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash("Please log in to access this page.", "error")
                return redirect(url_for('login'))
            
            if session.get('role') != required_role:
                flash(f"Access denied. This page is for {required_role}s only.", "error")
                return render_template('403.html'), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def get_connection():
    return sqlite3.connect("platform.db")

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF using PyMuPDF"""
    try:
        text = ""
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text += page.get_text()
        return text.strip()
    except Exception as e:
        print(f"[PDF ERROR] {str(e)}")
        return ""

# ────────────────────────────────────────────────
#  ROUTES
# ────────────────────────────────────────────────

@app.route('/')
def index():
    """Root route - redirect to appropriate dashboard based on role"""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    role = session.get('role')
    print(f"[REDIRECT] User: {session.get('email')} | Role: {role}")

    if role == 'student':
        return redirect(url_for('student_dashboard'))
    elif role == 'company':
        return redirect(url_for('company_dashboard'))
    elif role == 'admin':
        return redirect(url_for('admin_dashboard'))
    else:
        print(f"[WARNING] Invalid role '{role}' for {session.get('email')}")
        session.clear()
        flash("Invalid session. Please log in again.", "warning")
        return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login route with proper role-based redirection"""
    if request.method == 'POST':
        email = request.form['email'].strip()
        password = request.form['password']

        with get_connection() as conn:
            user = conn.execute(
                "SELECT user_id, name, email, password, role FROM users WHERE email = ?",
                (email,)
            ).fetchone()

            if user and check_password_hash(user[3], password):
                # Clear any previous session
                session.clear()
                
                # Set new session data
                session['user_id'] = user[0]
                session['name']   = user[1]
                session['email']  = user[2]
                session['role']   = user[4]

                print(f"[LOGIN SUCCESS] {email} logged in as {user[4]}")
                flash(f'Welcome back, {user[1]}!', 'success')
                
                # Redirect to appropriate dashboard
                return redirect(url_for('index'))
            else:
                flash('Invalid email or password. Please try again.', 'error')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registration route with profile creation"""
    if request.method == 'POST':
        name     = request.form['name'].strip()
        email    = request.form['email'].strip()
        password = request.form['password']
        role     = request.form['role']

        # Validate role
        if role not in ['student', 'company']:
            flash('Invalid role selected.', 'error')
            return render_template('register.html')

        hashed = generate_password_hash(password)

        with get_connection() as conn:
            try:
                # Check if email already exists
                existing = conn.execute(
                    "SELECT email FROM users WHERE email = ?", (email,)
                ).fetchone()
                
                if existing:
                    flash('Email already registered. Please login.', 'error')
                    return render_template('register.html')

                # Insert new user
                conn.execute(
                    "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
                    (name, email, hashed, role)
                )
                conn.commit()

                user_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

                # Create corresponding profile
                if role == 'student':
                    conn.execute("INSERT INTO student_profile (user_id) VALUES (?)", (user_id,))
                elif role == 'company':
                    conn.execute("INSERT INTO company_profile (user_id) VALUES (?)", (user_id,))

                conn.commit()

                print(f"[REGISTRATION SUCCESS] {email} registered as {role}")
                flash('Registration successful! Please log in.', 'success')
                return redirect(url_for('login'))
                
            except sqlite3.IntegrityError as e:
                flash('Email already registered.', 'error')
                print(f"[REGISTRATION ERROR] {str(e)}")
            except Exception as e:
                flash(f'Registration error: {str(e)}', 'error')
                print(f"[REGISTRATION ERROR] {str(e)}")

    return render_template('register.html')


@app.route('/logout')
def logout():
    """Logout route"""
    user_email = session.get('email', 'Unknown')
    print(f"[LOGOUT] {user_email}")
    session.clear()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('login'))


# ────────────────────────────────────────────────
#  STUDENT ROUTES
# ────────────────────────────────────────────────

@app.route('/student/dashboard', methods=['GET', 'POST'])
@role_required('student')
def student_dashboard():
    """Student dashboard with profile management and resume upload"""
    feedback_message = None
    resume_score = None
    detailed_feedback = None
    
    if request.method == 'POST':
        skills = request.form.get('skills', '').strip()
        cgpa = float(request.form.get('cgpa', 0))
        interest_domain = request.form.get('interest_domain', '').strip()
        experience_years = int(request.form.get('experience_years', 0))
        past_education = request.form.get('past_education', '').strip()

        resume_file = request.files.get('resume')
        photo_file = request.files.get('profile_photo')

        with get_connection() as conn:
            # Get current profile
            current = conn.execute(
                "SELECT resume_path, profile_photo FROM student_profile WHERE user_id = ?",
                (session['user_id'],)
            ).fetchone()

            resume_path = current[0] if current else None
            photo_path = current[1] if current else None
            extracted_skills = None

            # Handle resume upload with AI analysis
            if resume_file and allowed_file(resume_file.filename):
                filename = secure_filename(resume_file.filename)
                new_resume_path = os.path.join('students/resumes', f"{session['user_id']}_{filename}")
                full_path = os.path.join(app.config['UPLOAD_FOLDER'], new_resume_path)
                
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                resume_file.save(full_path)

                # Extract and analyze resume
                resume_text = extract_text_from_pdf(full_path)
                
                if resume_text:
                    # Get ATS score
                    resume_score, analysis = analyze_resume_quality(resume_text, interest_domain)
                    detailed_feedback = analysis
                    
                    # Extract skills
                    extracted_skills_list = extract_skills_from_text(resume_text)
                    extracted_skills = ', '.join(extracted_skills_list) if extracted_skills_list else None
                    
                    # Build feedback message
                    feedback_lines = [
                        f"📊 Resume Score: {resume_score}/100",
                        "",
                        "📋 Detailed Analysis:"
                    ]
                    
                    # Add score breakdown by category
                    categories = {
                        'resume_quality': ('Resume Quality', 25),
                        'keyword_match': ('Domain Keywords', 30),
                        'skill_match': ('Technical Skills', 25),
                        'experience_signals': ('Experience & Impact', 20)
                    }
                    
                    for key, (label, max_score) in categories.items():
                        if key in analysis:
                            score_value = analysis[key]
                            percentage = (score_value / max_score * 100) if max_score > 0 else 0
                            status = "✅" if percentage >= 70 else "⚠️" if percentage >= 40 else "❌"
                            feedback_lines.append(f"{status} {label}: {score_value}/{max_score} ({percentage:.0f}%)")
                    
                    # Add detailed breakdown if available
                    if 'breakdown' in analysis and analysis['breakdown']:
                        feedback_lines.append("")
                        feedback_lines.append("📝 Detailed Breakdown:")
                        for item in analysis['breakdown']:
                            feedback_lines.append(f"  {item}")
                    
                    if resume_score >= 50:
                        resume_path = new_resume_path
                        feedback_lines.append("")
                        feedback_lines.append("✅ Resume accepted and saved!")
                        if extracted_skills:
                            feedback_lines.append(f"🤖 Extracted Skills: {extracted_skills}")
                    else:
                        # Delete rejected resume
                        if os.path.exists(full_path):
                            os.remove(full_path)
                        feedback_lines.append("")
                        feedback_lines.append("❌ Resume score too low (minimum 50/100 required)")
                        feedback_lines.append("Please improve your resume and try again.")
                    
                    feedback_message = "\n".join(feedback_lines)
                else:
                    feedback_message = "❌ Could not extract text from PDF. Please ensure it's a valid resume."
                    resume_score = 0

            # Handle photo upload
            if photo_file and allowed_file(photo_file.filename):
                filename = secure_filename(photo_file.filename)
                photo_path = os.path.join('students/photos', f"{session['user_id']}_{filename}")
                full_path = os.path.join(app.config['UPLOAD_FOLDER'], photo_path)
                
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                photo_file.save(full_path)

            # Update profile
            try:
                conn.execute("""
                    UPDATE student_profile 
                    SET skills = ?, cgpa = ?, interest_domain = ?, 
                        experience_years = ?, resume_path = ?, 
                        past_education = ?, profile_photo = ?, extracted_skills = ?
                    WHERE user_id = ?
                """, (skills, cgpa, interest_domain, experience_years, 
                      resume_path, past_education, photo_path, extracted_skills, session['user_id']))
                conn.commit()

                if not feedback_message:
                    flash('Profile updated successfully!', 'success')
                
            except Exception as e:
                flash(f'Error updating profile: {str(e)}', 'error')
                print(f"[PROFILE UPDATE ERROR] {str(e)}")

    # Get profile data
    with get_connection() as conn:
        profile = conn.execute("""
            SELECT skills, cgpa, interest_domain, experience_years, 
                   resume_path, past_education, profile_photo, extracted_skills
            FROM student_profile 
            WHERE user_id = ?
        """, (session['user_id'],)).fetchone()

        # Get allocation data
        allocation = conn.execute("""
            SELECT cp.company_name, pos.domain, a.score, a.rank, pos.stipend, cp.location
            FROM allocations a
            JOIN company_profile cp ON a.company_id = cp.user_id
            JOIN company_positions pos ON a.position_id = pos.position_id
            WHERE a.student_id = ?
        """, (session['user_id'],)).fetchone()

    return render_template('student_dashboard.html', 
                          profile=profile, 
                          allocation=allocation,
                          feedback_message=feedback_message,
                          resume_score=resume_score,
                          detailed_feedback=detailed_feedback)


# ────────────────────────────────────────────────
#  COMPANY ROUTES
# ────────────────────────────────────────────────

@app.route('/company/dashboard', methods=['GET', 'POST'])
@role_required('company')
def company_dashboard():
    """Company dashboard with profile and position management"""
    if request.method == 'POST':
        # Check if adding position
        if request.form.get('add_position'):
            domain = request.form.get('domain', '').strip()
            required_skills = request.form.get('required_skills', '').strip()
            min_cgpa = float(request.form.get('min_cgpa', 0))
            positions = int(request.form.get('positions', 0))
            stipend = int(request.form.get('stipend', 0))

            with get_connection() as conn:
                try:
                    conn.execute("""
                        INSERT INTO company_positions 
                        (company_id, domain, required_skills, min_cgpa, positions, stipend)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (session['user_id'], domain, required_skills, min_cgpa, positions, stipend))
                    conn.commit()
                    flash('Position added successfully!', 'success')
                except Exception as e:
                    flash(f'Error adding position: {str(e)}', 'error')
        else:
            # Update company profile
            company_name = request.form.get('company_name', '').strip()
            location = request.form.get('location', '').strip()
            contact_email = request.form.get('contact_email', '').strip()
            contact_no = request.form.get('contact_no', '').strip()
            logo_file = request.files.get('profile_logo')

            with get_connection() as conn:
                current = conn.execute(
                    "SELECT profile_logo FROM company_profile WHERE user_id = ?",
                    (session['user_id'],)
                ).fetchone()

                logo_path = current[0] if current else None

                if logo_file and allowed_file(logo_file.filename):
                    filename = secure_filename(logo_file.filename)
                    logo_path = os.path.join('companies/logos', f"{session['user_id']}_{filename}")
                    full_path = os.path.join(app.config['UPLOAD_FOLDER'], logo_path)
                    
                    os.makedirs(os.path.dirname(full_path), exist_ok=True)
                    logo_file.save(full_path)

                try:
                    conn.execute("""
                        UPDATE company_profile 
                        SET company_name = ?, location = ?, contact_email = ?, 
                            contact_no = ?, profile_logo = ?
                        WHERE user_id = ?
                    """, (company_name, location, contact_email, contact_no, 
                          logo_path, session['user_id']))
                    conn.commit()
                    flash('Company profile updated successfully!', 'success')
                except Exception as e:
                    flash(f'Error updating profile: {str(e)}', 'error')

    # Get company data
    with get_connection() as conn:
        profile = conn.execute("""
            SELECT company_name, location, contact_email, contact_no, profile_logo
            FROM company_profile 
            WHERE user_id = ?
        """, (session['user_id'],)).fetchone()

        positions = conn.execute("""
            SELECT position_id, company_id, domain, required_skills, min_cgpa, positions, stipend
            FROM company_positions 
            WHERE company_id = ?
        """, (session['user_id'],)).fetchall()

        allocated_students = conn.execute("""
            SELECT u.name, sp.skills, sp.cgpa, sp.interest_domain, 
                   a.score, a.rank, sp.resume_path, sp.experience_years,
                   sp.profile_photo, pos.domain
            FROM allocations a
            JOIN users u ON a.student_id = u.user_id
            JOIN student_profile sp ON a.student_id = sp.user_id
            JOIN company_positions pos ON a.position_id = pos.position_id
            WHERE a.company_id = ?
            ORDER BY a.rank
        """, (session['user_id'],)).fetchall()

    return render_template('company_dashboard.html', 
                          profile=profile, 
                          positions=positions,
                          allocated_students=allocated_students)


# ────────────────────────────────────────────────
#  ADMIN ROUTES
# ────────────────────────────────────────────────

@app.route('/admin/dashboard')
@role_required('admin')
def admin_dashboard():
    """Admin dashboard showing all users and allocations"""
    with get_connection() as conn:
        students = conn.execute("""
            SELECT u.user_id, u.name, u.email, sp.skills, sp.cgpa, 
                   sp.interest_domain, sp.experience_years, sp.resume_path, sp.profile_photo
            FROM users u 
            LEFT JOIN student_profile sp ON u.user_id = sp.user_id
            WHERE u.role = 'student'
            ORDER BY u.name
        """).fetchall()

        companies = conn.execute("""
            SELECT u.user_id, u.name, u.email, cp.company_name, cp.location
            FROM users u 
            LEFT JOIN company_profile cp ON u.user_id = cp.user_id
            WHERE u.role = 'company'
            ORDER BY u.name
        """).fetchall()
        
        # Get positions for each company
        company_positions = conn.execute("""
            SELECT company_id, COUNT(*) as position_count, SUM(positions) as total_openings
            FROM company_positions
            GROUP BY company_id
        """).fetchall()
        
        # Convert to dict for easy lookup
        positions_dict = {cp[0]: {'count': cp[1], 'openings': cp[2]} for cp in company_positions}

        allocations = conn.execute("""
            SELECT u.name, cp.company_name, pos.domain, a.score, a.rank,
                   a.student_id, sp.resume_path, u.email, sp.profile_photo, sp.skills, sp.cgpa
            FROM allocations a
            JOIN users u ON a.student_id = u.user_id
            JOIN company_profile cp ON a.company_id = cp.user_id
            JOIN company_positions pos ON a.position_id = pos.position_id
            JOIN student_profile sp ON a.student_id = sp.user_id
            ORDER BY a.rank
        """).fetchall()

    return render_template('admin_dashboard.html', 
                          students=students, 
                          companies=companies,
                          company_positions=positions_dict,
                          allocations=allocations)


@app.route('/admin/allocate', methods=['POST'])
@role_required('admin')
def admin_allocate():
    """Run allocation algorithm with email notifications"""
    send_emails = request.form.get('send_emails') == 'on'
    
    print("\n" + "="*80)
    print("🚀 STARTING ALLOCATION PROCESS")
    print(f"📧 Send emails: {send_emails}")
    print("="*80 + "\n")
    
    with get_connection() as conn:
        # Get all students with profiles
        students = conn.execute("""
            SELECT u.user_id, u.name, u.email, sp.skills, sp.cgpa, 
                   sp.interest_domain, sp.experience_years, sp.resume_path,
                   sp.profile_photo, sp.extracted_skills
            FROM users u
            JOIN student_profile sp ON u.user_id = sp.user_id
            WHERE u.role = 'student' AND sp.cgpa IS NOT NULL
        """).fetchall()

        # Get all positions
        positions = conn.execute("""
            SELECT position_id, company_id, domain, required_skills, 
                   min_cgpa, positions, stipend
            FROM company_positions
        """).fetchall()

        if not students:
            flash('No students with complete profiles found.', 'warning')
            return redirect(url_for('admin_dashboard'))

        if not positions:
            flash('No positions available. Companies must add positions first.', 'warning')
            return redirect(url_for('admin_dashboard'))

        # Load resume texts
        resume_texts = {}
        for student in students:
            student_id = student[0]
            resume_path_row = conn.execute(
                "SELECT resume_path FROM student_profile WHERE user_id = ?",
                (student_id,)
            ).fetchone()
            
            if resume_path_row and resume_path_row[0]:
                full_path = os.path.join(app.config['UPLOAD_FOLDER'], resume_path_row[0])
                if os.path.exists(full_path):
                    resume_texts[student_id] = extract_text_from_pdf(full_path)

        # Run allocation algorithm
        allocations = run_smart_allocation(students, positions, resume_texts)

        # Clear previous allocations
        conn.execute("DELETE FROM allocations")
        conn.commit()

        # Save new allocations
        email_data_list = []
        
        for sid, cid, pid, score, rank in allocations:
            conn.execute("""
                INSERT INTO allocations (student_id, company_id, position_id, score, rank)
                VALUES (?, ?, ?, ?, ?)
            """, (sid, cid, pid, score, rank))
            
            # Prepare email data if sending emails
            if send_emails:
                student_info = conn.execute("""
                    SELECT u.email, u.name
                    FROM users u
                    WHERE u.user_id = ?
                """, (sid,)).fetchone()
                
                company_info = conn.execute("""
                    SELECT cp.company_name, cp.location, pos.domain, pos.stipend
                    FROM company_profile cp
                    JOIN company_positions pos ON pos.position_id = ?
                    WHERE cp.user_id = ?
                """, (pid, cid)).fetchone()
                
                if student_info and company_info:
                    email_data_list.append({
                        'student_email': student_info[0],
                        'student_name': student_info[1],
                        'company_name': company_info[0],
                        'location': company_info[1] or 'Not specified',
                        'domain': company_info[2],
                        'stipend': company_info[3],
                        'rank': rank,
                        'match_score': int(score)
                    })
        
        conn.commit()

        # Send emails if enabled
        email_status = ""
        if send_emails and email_data_list:
            print(f"\n📧 Sending {len(email_data_list)} allocation emails...")
            success_count, failed_count, errors = send_bulk_allocation_emails(mail, email_data_list)
            
            email_status = f" | Emails sent: {success_count}, Failed: {failed_count}"
            
            if failed_count > 0:
                print(f"⚠️ Email failures:")
                for error in errors:
                    print(f"   - {error['student']}: {error['error']}")
        
        flash(f'Allocation completed! {len(allocations)} students matched{email_status}', 'success')
        print(f"\n✅ Allocation complete: {len(allocations)} matches made\n")

    return redirect(url_for('admin_dashboard'))


@app.route('/admin/deallocate/<int:student_id>', methods=['POST'])
@role_required('admin')
def deallocate_student(student_id):
    """Remove allocation for a specific student"""
    with get_connection() as conn:
        # Check if student is allocated
        allocation = conn.execute("""
            SELECT a.allocation_id, u.name, cp.company_name
            FROM allocations a
            JOIN users u ON u.user_id = a.student_id
            JOIN company_profile cp ON cp.user_id = a.company_id
            WHERE a.student_id = ?
        """, (student_id,)).fetchone()
        
        if not allocation:
            flash(f'Student ID {student_id} is not currently allocated.', 'warning')
            return redirect(url_for('admin_dashboard'))
        
        # Delete the allocation
        try:
            conn.execute("DELETE FROM allocations WHERE student_id = ?", (student_id,))
            conn.commit()
            
            student_name = allocation[1]
            company_name = allocation[2]
            flash(f'Successfully deallocated {student_name} from {company_name}!', 'success')
            print(f"[DEALLOCATION] Student {student_id} ({student_name}) removed from {company_name}")
        except Exception as e:
            flash(f'Error deallocating student: {str(e)}', 'error')
            print(f"[DEALLOCATION ERROR] {str(e)}")
    
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/deallocate_all', methods=['POST'])
@role_required('admin')
def deallocate_all():
    """Remove all allocations (reset allocation system)"""
    with get_connection() as conn:
        try:
            count = conn.execute("SELECT COUNT(*) FROM allocations").fetchone()[0]
            conn.execute("DELETE FROM allocations")
            conn.commit()
            
            flash(f'Successfully cleared all {count} allocations! You can now run allocation again.', 'success')
            print(f"[DEALLOCATION ALL] Removed {count} allocations")
        except Exception as e:
            flash(f'Error clearing allocations: {str(e)}', 'error')
            print(f"[DEALLOCATION ALL ERROR] {str(e)}")
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/analytics')
@role_required('admin')
def admin_analytics():
    """Analytics page with charts"""
    with get_connection() as conn:
        total_students = conn.execute("SELECT COUNT(*) FROM users WHERE role = 'student'").fetchone()[0]
        allocated = conn.execute("SELECT COUNT(DISTINCT student_id) FROM allocations").fetchone()[0]
        
        success_rate = round((allocated / total_students * 100) if total_students > 0 else 0, 1)
        
        # Create pie chart
        fig, ax = plt.subplots(figsize=(8, 6))
        sizes = [allocated, total_students - allocated]
        labels = [f'Allocated ({allocated})', f'Not Allocated ({total_students - allocated})']
        colors = ['#27ae60', '#e74c3c']
        explode = (0.1, 0)
        
        ax.pie(sizes, explode=explode, labels=labels, colors=colors,
               autopct='%1.1f%%', shadow=True, startangle=90)
        ax.axis('equal')
        plt.title('Student Allocation Status', fontsize=16, fontweight='bold')
        
        # Convert plot to base64
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        pie_chart = base64.b64encode(buf.read()).decode('utf-8')
        plt.close()
        
    return render_template('admin_analytics.html', 
                          success_rate=success_rate, 
                          pie_chart=pie_chart)


@app.route('/admin/export_students')
@role_required('admin')
def export_students():
    """Export students to Excel"""
    with get_connection() as conn:
        students = conn.execute("""
            SELECT u.name, u.email, sp.skills, sp.cgpa, sp.interest_domain, 
                   sp.experience_years
            FROM users u
            LEFT JOIN student_profile sp ON u.user_id = sp.user_id
            WHERE u.role = 'student'
        """).fetchall()
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Students"
    
    # Headers
    headers = ['Name', 'Email', 'Skills', 'CGPA', 'Domain', 'Experience (years)']
    ws.append(headers)
    
    # Data
    for student in students:
        ws.append(list(student))
    
    # Save to bytes
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'students_{datetime.now().strftime("%Y%m%d")}.xlsx'
    )


@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    """Serve uploaded files"""
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename))


# ────────────────────────────────────────────────
#  INITIALIZATION
# ────────────────────────────────────────────────

if __name__ == '__main__':
    # Create upload folders
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'students/resumes'),  exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'students/photos'),   exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'companies/logos'),   exist_ok=True)

    # Initialize database
    from database import create_tables
    create_tables()

    # Create admin if not exists
    with get_connection() as conn:
        if not conn.execute("SELECT 1 FROM users WHERE email = 'admin@platform.com'").fetchone():
            hashed = generate_password_hash('admin123')
            conn.execute(
                "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
                ('Admin', 'admin@platform.com', hashed, 'admin')
            )
            conn.commit()
            print("✅ Admin user created: admin@platform.com / admin123")

    print("\n" + "="*80)
    print("🚀 INTERNSHIP ALLOCATION PLATFORM")
    print("="*80)
    print("📧 Email: CONFIGURED (bobxdev5@gmail.com)")
    print("🔐 Admin: admin@platform.com / admin123")
    print("🌐 Server: http://localhost:5000")
    print("="*80 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)

@app.route('/company/position/delete/<int:position_id>', methods=['POST'])
@role_required('company')
def delete_position(position_id):
    """Delete a position posted by the company"""
    with get_connection() as conn:
        # Verify the position belongs to this company
        position = conn.execute("""
            SELECT position_id FROM company_positions 
            WHERE position_id = ? AND company_id = ?
        """, (position_id, session['user_id'])).fetchone()
        
        if not position:
            flash('Position not found or unauthorized access.', 'error')
            return redirect(url_for('company_dashboard'))
        
        # Delete the position
        try:
            conn.execute("DELETE FROM company_positions WHERE position_id = ?", (position_id,))
            conn.commit()
            flash('Position deleted successfully!', 'success')
        except Exception as e:
            flash(f'Error deleting position: {str(e)}', 'error')
    
    return redirect(url_for('company_dashboard'))


@app.route('/company/position/edit/<int:position_id>', methods=['GET', 'POST'])
@role_required('company')
def edit_position(position_id):
    """Edit a position posted by the company"""
    with get_connection() as conn:
        # Verify the position belongs to this company
        position = conn.execute("""
            SELECT position_id, domain, required_skills, min_cgpa, positions, stipend
            FROM company_positions 
            WHERE position_id = ? AND company_id = ?
        """, (position_id, session['user_id'])).fetchone()
        
        if not position:
            flash('Position not found or unauthorized access.', 'error')
            return redirect(url_for('company_dashboard'))
        
        if request.method == 'POST':
            domain = request.form.get('domain', '').strip()
            required_skills = request.form.get('required_skills', '').strip()
            min_cgpa = float(request.form.get('min_cgpa', 0))
            positions_count = int(request.form.get('positions', 0))
            stipend = int(request.form.get('stipend', 0))
            
            try:
                conn.execute("""
                    UPDATE company_positions 
                    SET domain = ?, required_skills = ?, min_cgpa = ?, positions = ?, stipend = ?
                    WHERE position_id = ?
                """, (domain, required_skills, min_cgpa, positions_count, stipend, position_id))
                conn.commit()
                flash('Position updated successfully!', 'success')
                return redirect(url_for('company_dashboard'))
            except Exception as e:
                flash(f'Error updating position: {str(e)}', 'error')
        
        # Get company profile for the edit page
        profile = conn.execute("""
            SELECT company_name, location, contact_email, contact_no, profile_logo
            FROM company_profile 
            WHERE user_id = ?
        """, (session['user_id'],)).fetchone()
    
    return render_template('edit_position.html', position=position, profile=profile)