from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
from database import create_tables, get_connection
from ai_engine import calculate_resume_quality_score, run_smart_allocation, calculate_skill_match
import os
import fitz
from io import BytesIO
import base64
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from openpyxl import Workbook

app = Flask(__name__)
app.secret_key = "your_super_secret_key_change_in_production"
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def role_required(required_role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session or session.get('role') != required_role:
                return render_template('403.html'), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route('/')
def index():
    if 'user_id' in session:
        role = session.get('role')
        if role == 'student':
            return redirect(url_for('student_dashboard'))
        elif role == 'company':
            return redirect(url_for('company_dashboard'))
        elif role == 'admin':
            return redirect(url_for('admin_dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        
        if not all([name, email, password, role]):
            return render_template('register.html', error="All fields are required")
        
        if role not in ['student', 'company']:
            return render_template('register.html', error="Invalid role selected")
        
        hashed_password = generate_password_hash(password)
        
        try:
            with get_connection() as conn:
                cursor = conn.execute(
                    "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
                    (name, email, hashed_password, role)
                )
                user_id = cursor.lastrowid
                
                if role == 'student':
                    conn.execute("INSERT INTO student_profile (user_id) VALUES (?)", (user_id,))
                elif role == 'company':
                    conn.execute("INSERT INTO company_profile (user_id) VALUES (?)", (user_id,))
                
                conn.commit()
                flash('Registration successful! Please login.', 'success')
                return redirect(url_for('login'))
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                return render_template('register.html', error="Email already registered")
            return render_template('register.html', error="Registration failed. Please try again.")
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        with get_connection() as conn:
            user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        
        if user and check_password_hash(user[3], password):
            session['user_id'] = user[0]
            session['name'] = user[1]
            session['role'] = user[4]
            
            if user[4] == 'student':
                return redirect(url_for('student_dashboard'))
            elif user[4] == 'company':
                return redirect(url_for('company_dashboard'))
            elif user[4] == 'admin':
                return redirect(url_for('admin_dashboard'))
        else:
            return render_template('login.html', error="Invalid email or password")
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/student/dashboard', methods=['GET', 'POST'])
@role_required('student')
def student_dashboard():
    user_id = session['user_id']
    feedback_message = None
    resume_score = None
    detailed_feedback = None
    
    if request.method == 'POST':
        skills = request.form.get('skills', '').strip()
        cgpa = float(request.form.get('cgpa', 0))
        interest_domain = request.form.get('interest_domain', '').strip()
        experience_years = int(request.form.get('experience_years', 0))
        past_education = request.form.get('past_education', '').strip()
        
        resume_path = None
        extracted_skills = ""
        
        with get_connection() as conn:
            current_profile = conn.execute("SELECT resume_path FROM student_profile WHERE user_id=?", (user_id,)).fetchone()
            current_resume = current_profile[0] if current_profile else None
        
        if 'resume' in request.files:
            file = request.files['resume']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(f"{user_id}_{file.filename}")
                resume_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'students/resumes')
                os.makedirs(resume_dir, exist_ok=True)
                temp_path = os.path.join(resume_dir, filename)
                file.save(temp_path)
                
                try:
                    doc = fitz.open(temp_path)
                    text = ""
                    for page in doc:
                        text += page.get_text()
                    doc.close()
                    
                    if len(text.strip()) < 100:
                        os.remove(temp_path)
                        feedback_message = "⚠️ RESUME REJECTED: The uploaded PDF appears to be empty or has insufficient content. Please upload a proper resume with at least 100 characters."
                        resume_score = 0
                        resume_path = current_resume
                    else:
                        resume_score, detailed_feedback = calculate_resume_quality_score(text, interest_domain)
                        
                        feedback_lines = [f"Overall Score: {resume_score}/100\n"]
                        for category, data in detailed_feedback.items():
                            feedback_lines.append(f"{category}: {data['score']}/{data['max']} – {data['msg']}")
                        
                        feedback_message = "\n".join(feedback_lines)
                        
                        common_skills = [
                            "python", "java", "javascript", "sql", "react", "angular", "vue",
                            "node", "django", "flask", "machine learning", "data science",
                            "aws", "azure", "docker", "git", "html", "css", "bootstrap",
                            "cybersecurity", "network security", "ethical hacking", "tensorflow",
                            "pytorch", "nlp", "computer vision", "pandas", "numpy", "scikit-learn",
                            "mongodb", "postgresql", "redis", "kubernetes", "jenkins", "c++", "c#",
                            "spring boot", "fastapi", "graphql", "rest api", "microservices"
                        ]
                        found = [s for s in common_skills if s in text.lower()]
                        extracted_skills = ','.join(found) if found else ""
                        
                        if resume_score >= 50:
                            resume_path = os.path.join('students/resumes', filename)
                            feedback_message = "✅ " + feedback_message + "\n\n🎉 Your resume has been successfully saved!"
                        else:
                            os.remove(temp_path)
                            resume_path = current_resume
                            feedback_message = "❌ " + feedback_message + "\n\n⚠️ Your resume was NOT saved (score below 50/100). Your resume quality is too poor. Please improve based on the feedback above and upload again."
                
                except Exception as e:
                    print(f"Resume processing error: {e}")
                    os.remove(temp_path) if os.path.exists(temp_path) else None
                    feedback_message = "❌ Could not read the resume file. Please upload a valid PDF with selectable text (not scanned image)."
                    resume_path = current_resume
                    resume_score = 0
            else:
                resume_path = current_resume
        else:
            resume_path = current_resume
        
        profile_photo = None
        with get_connection() as conn:
            current_profile = conn.execute("SELECT profile_photo FROM student_profile WHERE user_id=?", (user_id,)).fetchone()
            current_photo = current_profile[0] if current_profile else None
        
        if 'profile_photo' in request.files:
            file = request.files['profile_photo']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(f"{user_id}_{file.filename}")
                photo_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'students/photos')
                os.makedirs(photo_dir, exist_ok=True)
                profile_photo = os.path.join('students/photos', filename)
                full_path = os.path.join(app.config['UPLOAD_FOLDER'], profile_photo)
                file.save(full_path)
            else:
                profile_photo = current_photo
        else:
            profile_photo = current_photo
        
        with get_connection() as conn:
            conn.execute("""
                UPDATE student_profile SET
                    skills=?, cgpa=?, interest_domain=?, experience_years=?, past_education=?,
                    resume_path=?, profile_photo=?, extracted_skills=?
                WHERE user_id=?
            """, (skills, cgpa, interest_domain, experience_years, past_education,
                  resume_path, profile_photo, extracted_skills, user_id))
            conn.commit()
    
    with get_connection() as conn:
        profile = conn.execute("SELECT * FROM student_profile WHERE user_id=?", (user_id,)).fetchone()
        
        allocation = conn.execute("""
            SELECT c.company_name, p.domain, a.score, a.rank, p.stipend, c.location
            FROM allocations a
            JOIN company_positions p ON a.position_id = p.position_id
            JOIN company_profile c ON a.company_id = c.user_id
            WHERE a.student_id=?
        """, (user_id,)).fetchone()
    
    return render_template('student_dashboard.html',
                          profile=profile,
                          allocation=allocation,
                          feedback_message=feedback_message,
                          resume_score=resume_score,
                          detailed_feedback=detailed_feedback)


@app.route('/company/dashboard', methods=['GET', 'POST'])
@role_required('company')
def company_dashboard():
    user_id = session['user_id']
    
    if request.method == 'POST':
        if 'add_position' in request.form:
            domain = request.form.get('domain')
            required_skills = request.form.get('required_skills')
            min_cgpa = float(request.form.get('min_cgpa', 0))
            positions = int(request.form.get('positions', 0))
            stipend = int(request.form.get('stipend', 0))
            
            with get_connection() as conn:
                conn.execute("""
                    INSERT INTO company_positions (company_id, domain, required_skills, min_cgpa, positions, stipend)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (user_id, domain, required_skills, min_cgpa, positions, stipend))
                conn.commit()
            
            flash('Position added successfully!', 'success')
        else:
            company_name = request.form.get('company_name')
            location = request.form.get('location')
            contact_email = request.form.get('contact_email')
            contact_no = request.form.get('contact_no')
            
            profile_logo = None
            with get_connection() as conn:
                current_profile = conn.execute("SELECT profile_logo FROM company_profile WHERE user_id=?", (user_id,)).fetchone()
                current_logo = current_profile[0] if current_profile else None
            
            if 'profile_logo' in request.files:
                file = request.files['profile_logo']
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(f"{user_id}_{file.filename}")
                    logo_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'companies/logos')
                    os.makedirs(logo_dir, exist_ok=True)
                    profile_logo = os.path.join('companies/logos', filename)
                    full_path = os.path.join(app.config['UPLOAD_FOLDER'], profile_logo)
                    file.save(full_path)
                else:
                    profile_logo = current_logo
            else:
                profile_logo = current_logo
            
            with get_connection() as conn:
                conn.execute("""
                    UPDATE company_profile SET
                        company_name=?, location=?, contact_email=?, contact_no=?, profile_logo=?
                    WHERE user_id=?
                """, (company_name, location, contact_email, contact_no, profile_logo, user_id))
                conn.commit()
            
            flash('Profile updated successfully!', 'success')
    
    with get_connection() as conn:
        profile = conn.execute("SELECT * FROM company_profile WHERE user_id=?", (user_id,)).fetchone()
        positions = conn.execute("SELECT * FROM company_positions WHERE company_id=?", (user_id,)).fetchall()
        
        allocated_students = conn.execute("""
            SELECT u.name, sp.skills, sp.cgpa, sp.interest_domain, a.score, a.rank,
                   sp.resume_path, sp.experience_years, sp.profile_photo, p.domain, sp.extracted_skills
            FROM allocations a
            JOIN users u ON a.student_id = u.user_id
            JOIN student_profile sp ON a.student_id = sp.user_id
            JOIN company_positions p ON a.position_id = p.position_id
            WHERE a.company_id=?
            ORDER BY a.rank
        """, (user_id,)).fetchall()
    
    return render_template('company_dashboard.html',
                          profile=profile,
                          positions=positions,
                          allocated_students=allocated_students)

@app.route('/admin/dashboard')
@role_required('admin')
def admin_dashboard():
    with get_connection() as conn:
        students = conn.execute("""
            SELECT u.user_id, u.name, u.email, sp.skills, sp.cgpa, sp.interest_domain,
                   sp.experience_years, sp.resume_path, sp.past_education, sp.profile_photo
            FROM users u
            LEFT JOIN student_profile sp ON u.user_id = sp.user_id
            WHERE u.role = 'student'
            ORDER BY u.user_id
        """).fetchall()
        
        companies = conn.execute("""
            SELECT u.user_id, u.name, u.email, cp.company_name, cp.location,
                   cp.contact_email, cp.contact_no, cp.profile_logo
            FROM users u
            LEFT JOIN company_profile cp ON u.user_id = cp.user_id
            WHERE u.role = 'company'
            ORDER BY u.user_id
        """).fetchall()
        
        allocations = conn.execute("""
            SELECT u.name as student_name, c.company_name, p.domain, a.score, a.rank,
                   sp.resume_path, sp.experience_years, sp.profile_photo, sp.skills, sp.cgpa
            FROM allocations a
            JOIN users u ON a.student_id = u.user_id
            JOIN company_profile c ON a.company_id = c.user_id
            JOIN company_positions p ON a.position_id = p.position_id
            JOIN student_profile sp ON a.student_id = sp.user_id
            ORDER BY a.rank
        """).fetchall()
        
        documents = conn.execute("""
            SELECT u.name, 
                   CASE WHEN sp.resume_path IS NOT NULL THEN 'Resume' END as doc_type,
                   sp.resume_path
            FROM users u
            JOIN student_profile sp ON u.user_id = sp.user_id
            WHERE u.role = 'student' AND sp.resume_path IS NOT NULL
            UNION ALL
            SELECT u.name,
                   CASE WHEN sp.profile_photo IS NOT NULL THEN 'Photo' END as doc_type,
                   sp.profile_photo
            FROM users u
            JOIN student_profile sp ON u.user_id = sp.user_id
            WHERE u.role = 'student' AND sp.profile_photo IS NOT NULL
        """).fetchall()
    
    return render_template('admin_dashboard.html',
                          students=students,
                          companies=companies,
                          allocations=allocations,
                          documents=documents)

@app.route('/admin/run_allocation', methods=['POST'])
@role_required('admin')
def run_allocation():
    with get_connection() as conn:
        students = conn.execute("""
            SELECT user_id, skills, cgpa, interest_domain, experience_years, extracted_skills
            FROM student_profile
            WHERE skills IS NOT NULL AND cgpa > 0 AND interest_domain IS NOT NULL
        """).fetchall()
        
        positions = conn.execute("""
            SELECT position_id, company_id, domain, required_skills, min_cgpa, positions, stipend
            FROM company_positions
        """).fetchall()
        
        if not students or not positions:
            flash('Need at least one student and one position to run allocation', 'error')
            return redirect(url_for('admin_dashboard'))
        
        allocations = run_smart_allocation(students, positions)
        
        conn.execute("DELETE FROM allocations")
        
        for student_id, company_id, position_id, score, rank in allocations:
            conn.execute("""
                INSERT INTO allocations (student_id, company_id, position_id, score, rank)
                VALUES (?, ?, ?, ?, ?)
            """, (student_id, company_id, position_id, score, rank))
        
        conn.commit()
    
    flash(f'Allocation completed successfully! {len(allocations)} students allocated.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/analytics')
@role_required('admin')
def admin_analytics():
    with get_connection() as conn:
        total_students = conn.execute("SELECT COUNT(*) FROM users WHERE role='student'").fetchone()[0]
        allocated_students = conn.execute("SELECT COUNT(DISTINCT student_id) FROM allocations").fetchone()[0]
    
    success_rate = round((allocated_students / total_students * 100), 2) if total_students > 0 else 0
    
    labels = ['Allocated', 'Not Allocated']
    sizes = [allocated_students, total_students - allocated_students]
    colors = ['#27ae60', '#e74c3c']
    
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
    ax.axis('equal')
    plt.title('Student Allocation Status', fontsize=16, fontweight='bold')
    
    buffer = BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
    buffer.seek(0)
    pie_chart = base64.b64encode(buffer.read()).decode()
    plt.close()
    
    return render_template('admin_analytics.html',
                          success_rate=success_rate,
                          pie_chart=pie_chart)

@app.route('/admin/export_students')
@role_required('admin')
def export_students():
    with get_connection() as conn:
        students = conn.execute("""
            SELECT u.user_id, u.name, u.email, sp.skills, sp.cgpa, sp.interest_domain,
                   sp.experience_years, sp.past_education
            FROM users u
            LEFT JOIN student_profile sp ON u.user_id = sp.user_id
            WHERE u.role = 'student'
        """).fetchall()
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Students"
    
    headers = ['ID', 'Name', 'Email', 'Skills', 'CGPA', 'Domain', 'Experience', 'Education']
    ws.append(headers)
    
    for student in students:
        ws.append(student)
    
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    return send_file(output, 
                    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    as_attachment=True,
                    download_name='students_export.xlsx')

@app.route('/admin/export_companies')
@role_required('admin')
def export_companies():
    with get_connection() as conn:
        companies = conn.execute("""
            SELECT u.user_id, u.name, u.email, cp.company_name, cp.location,
                   cp.contact_email, cp.contact_no
            FROM users u
            LEFT JOIN company_profile cp ON u.user_id = cp.user_id
            WHERE u.role = 'company'
        """).fetchall()
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Companies"
    
    headers = ['ID', 'Contact Name', 'Email', 'Company Name', 'Location', 'Contact Email', 'Contact No']
    ws.append(headers)
    
    for company in companies:
        ws.append(company)
    
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    return send_file(output,
                    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    as_attachment=True,
                    download_name='companies_export.xlsx')

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename))

if __name__ == '__main__':
    create_tables()
    
    with get_connection() as conn:
        admin_exists = conn.execute("SELECT * FROM users WHERE email='admin@platform.com'").fetchone()
        
        if not admin_exists:
            hashed_password = generate_password_hash('admin123')
            conn.execute(
                "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
                ('Admin', 'admin@platform.com', hashed_password, 'admin')
            )
            conn.commit()
            print("✅ Admin user created - Email: admin@platform.com | Password: admin123")
    
    print("🚀 Starting Internship Allocation Platform...")
    print("📧 Admin Login: admin@platform.com | Password: admin123")
    app.run(debug=True, host='0.0.0.0', port=5000)