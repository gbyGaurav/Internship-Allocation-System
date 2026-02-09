from flask_mail import Message
import os
import traceback  # ← Added for full error printing

def send_allocation_email(mail, student_email, student_name, company_name, domain, stipend, location, rank, match_score):
    """
    Send allocation notification email to student
    
    Args:
        mail: Flask-Mail instance
        student_email: Student's email address
        student_name: Student's full name
        company_name: Name of the company
        domain: Job domain/role
        stipend: Monthly stipend amount
        location: Company location
        rank: Student's rank in allocation
        match_score: ATS match score (0-100)
    """
    subject = f"🎉 Congratulations! Internship Allocation Confirmed - {company_name}"
    
    # Create HTML email body (keeping your original truncated version)
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                text-align: center;
                border-radius: 10px 10px 0 0;
            }}
            /* ... rest of your styles ... (keeping as-is, truncated in your original) */
        </style>
    </head>
    <body>
        <div class="header">
            <div class="emoji">🎉</div>
            <h1>Congratulations, {student_name}!</h1>
            <p>You have been allocated an internship!</p>
        </div>
        <div class="content">
            <div class="detail-box">
                <div class="detail-item">
                    <span class="label">Company:</span>
                    <span class="value">{company_name}</span>
                </div>
                <div class="detail-item">
                    <span class="label">Domain/Role:</span>
                    <span class="value">{domain}</span>
                </div>
                <div class="detail-item">
                    <span class="label">Stipend:</span>
                    <span class="value">₹{stipend:,}/month</span>
                </div>
                <div class="detail-item">
                    <span class="label">Location:</span>
                    <span class="value">{location}</span>
                </div>
                <div class="detail-item">
                    <span class="label">Your Rank:</span>
                    <span class="rank-badge">#{rank}</span>
                </div>
                <div class="detail-item">
                    <span class="label">ATS Match Score:</span>
                    <span class="score-badge">{match_score}/100</span>
                </div>
            </div>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="http://localhost:5000/login" class="cta-button">
                    🚀 View Dashboard
                </a>
            </div>
            
            <p style="font-size: 14px; color: #64748b; text-align: center; margin-top: 30px;">
                This is an automated notification from the Internship Allocation Platform.<br>
                If you have any questions, please contact the administrator.
            </p>
        </div>
        
        <div class="footer">
            <p style="margin: 5px 0;"><strong>Internship Allocation Platform</strong></p>
            <p style="margin: 5px 0;">AI-Powered Student-Company Matching System</p>
            <p style="margin: 15px 0 5px 0; font-size: 12px;">
                © 2026 Internship Allocation Platform. All rights reserved.
            </p>
        </div>
    </body>
    </html>
    """
    
    # Plain text fallback (your original)
    text_body = f"""
    Congratulations, {student_name}!
    
    You've Been Selected for an Internship!
    
    INTERNSHIP DETAILS:
    -------------------
    Company: {company_name}
    Domain/Role: {domain}
    Stipend: ₹{stipend:,}/month
    Location: {location}
    
    Your Allocation Rank: #{rank}
    ATS Match Score: {match_score}/100
    
    WHAT THIS MEANS:
    - Your profile and resume were matched using our AI algorithm
    - You scored {match_score}/100 on our ATS system
    - The company will contact you soon with further details
    - Keep checking your email and dashboard for updates
    
    NEXT STEPS:
    1. Wait for the company to reach out via email or phone
    2. Prepare for potential interviews or assessments
    3. Review the job requirements and prepare accordingly
    4. Login to your dashboard for more details
    
    This is an automated notification from the Internship Allocation Platform.
    If you have any questions, please contact the administrator.
    
    © 2026 Internship Allocation Platform
    """
    
    print(f"[EMAIL DEBUG] Attempting to send email to: {student_email} | Subject: {subject}")
    
    try:
        msg = Message(
            subject=subject,
            recipients=[student_email],
            html=html_body,
            body=text_body
        )
        print("[EMAIL DEBUG] Message created successfully. Calling mail.send()...")
        mail.send(msg)
        print("[EMAIL DEBUG] Email sent successfully!")
        return True, "Email sent successfully"
    except Exception as e:
        print("EMAIL SEND FAILED WITH EXCEPTION:")
        traceback.print_exc()  # ← This shows the FULL error in terminal
        error_msg = f"Failed to send email to {student_email}: {str(e)}"
        print(error_msg)
        return False, error_msg


def send_bulk_allocation_emails(mail, allocations_data):
    """
    Send allocation emails to multiple students
    
    Args:
        mail: Flask-Mail instance
        allocations_data: List of dicts with keys:
            - student_email
            - student_name
            - company_name
            - domain
            - stipend
            - location
            - rank
            - match_score
    
    Returns:
        tuple: (success_count, failed_count, errors)
    """
    success_count = 0
    failed_count = 0
    errors = []
    
    for data in allocations_data:
        print(f"[BULK EMAIL] Processing student: {data['student_name']} ({data['student_email']})")
        success, message = send_allocation_email(
            mail=mail,
            student_email=data['student_email'],
            student_name=data['student_name'],
            company_name=data['company_name'],
            domain=data['domain'],
            stipend=data['stipend'],
            location=data['location'],
            rank=data['rank'],
            match_score=data['match_score']
        )
        
        if success:
            success_count += 1
            print(f"[BULK EMAIL] Success for {data['student_email']}")
        else:
            failed_count += 1
            errors.append({
                'student': data['student_name'],
                'email': data['student_email'],
                'error': message
            })
            print(f"[BULK EMAIL] Failed for {data['student_email']}: {message}")
    
    print(f"[BULK EMAIL SUMMARY] Sent: {success_count} | Failed: {failed_count}")
    return success_count, failed_count, errors