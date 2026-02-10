import re
from collections import Counter

# ============================================================================
# DOMAIN-SPECIFIC REQUIRED SKILLS MAPPING
# ============================================================================

DOMAIN_REQUIRED_SKILLS = {
    "AI": [
        "Python", "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch", 
        "Neural Networks", "NLP", "Computer Vision", "Scikit-learn", "Keras",
        "Data Analysis", "NumPy", "Pandas", "AI", "Artificial Intelligence"
    ],
    "Artificial Intelligence": [
        "Python", "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch", 
        "Neural Networks", "NLP", "Computer Vision", "Scikit-learn", "Keras",
        "Data Analysis", "NumPy", "Pandas", "AI", "Artificial Intelligence"
    ],
    "Data Science": [
        "Python", "Pandas", "NumPy", "SQL", "Data Analysis", "Machine Learning",
        "Data Visualization", "Matplotlib", "Seaborn", "Statistics", "R",
        "Excel", "Tableau", "Power BI", "Big Data", "Jupyter"
    ],
    "Cyber Security": [
        "Network Security", "Linux", "Ethical Hacking", "Penetration Testing",
        "Kali Linux", "Wireshark", "Metasploit", "Nmap", "Burp Suite",
        "OWASP", "Security", "Firewall", "Cryptography", "TCP/IP"
    ],
    "Web Development": [
        "HTML", "CSS", "JavaScript", "React", "Node.js", "MongoDB", "Express",
        "Angular", "Vue.js", "TypeScript", "REST API", "Git", "Bootstrap",
        "jQuery", "MySQL", "PostgreSQL", "Web Design", "Frontend", "Backend"
    ],
    "Mobile Development": [
        "Android", "iOS", "React Native", "Flutter", "Kotlin", "Swift",
        "Java", "Dart", "Mobile UI", "API Integration", "Firebase",
        "App Development", "Xamarin", "Mobile Design"
    ],
    "Cloud Computing": [
        "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Cloud Architecture",
        "EC2", "S3", "Lambda", "DevOps", "Linux", "Networking",
        "Serverless", "CloudFormation", "Terraform"
    ],
    "DevOps": [
        "Docker", "Kubernetes", "Jenkins", "Git", "CI/CD", "Linux",
        "AWS", "Azure", "Terraform", "Ansible", "Chef", "Puppet",
        "GitLab", "GitHub Actions", "Monitoring", "Automation"
    ],
    "General": [
        "Python", "Java", "JavaScript", "Programming", "Problem Solving",
        "Git", "Communication", "Teamwork", "Project Management"
    ]
}


def get_domain_skills(domain: str) -> str:
    """
    Get required skills for a given domain
    Returns comma-separated string of skills
    """
    if not domain:
        domain = "General"
    
    domain_normalized = domain.strip()
    
    # Try exact match first
    if domain_normalized in DOMAIN_REQUIRED_SKILLS:
        skills = DOMAIN_REQUIRED_SKILLS[domain_normalized]
        return ", ".join(skills)
    
    # Try case-insensitive match
    for key in DOMAIN_REQUIRED_SKILLS:
        if key.lower() == domain_normalized.lower():
            skills = DOMAIN_REQUIRED_SKILLS[key]
            return ", ".join(skills)
    
    # Default to General if not found
    skills = DOMAIN_REQUIRED_SKILLS["General"]
    return ", ".join(skills)



def calculate_skill_match(student_skills: str, required: str) -> float:
    """Calculate skill match percentage between student and required skills"""
    if not student_skills or not required:
        return 0.0
    s = {x.strip().lower() for x in student_skills.split(',') if x.strip()}
    r = {x.strip().lower() for x in required.split(',') if x.strip()}
    if not r:
        return 0.0
    return round(len(s & r) / len(r) * 100, 2)


def normalize_domain(d: str) -> str:
    """Normalize domain names for comparison"""
    return d.strip().lower().replace(" ", "").replace("-", "").replace("_", "")


def is_resume_fake_or_spam(text: str) -> tuple[bool, str]:
    """
    ENHANCED: Detect if resume is fake, spam, or has gibberish content
    Returns: (is_fake: bool, reason: str)
    """
    if not text or len(text.strip()) < 100:
        return True, "Resume is empty or too short (minimum 100 characters required)"
    
    text_lower = text.lower()
    words = text_lower.split()
    
    # ===== CRITICAL CHECKS =====
    
    # Check 1: Too many repeated characters (e.g., "aaaaaaa", "xxxxxxx")
    repeated_chars = re.findall(r'(.)\1{6,}', text_lower)
    if repeated_chars:
        return True, "Resume contains excessive repeated characters (detected as spam)"
    
    # Check 2: Look for obvious spam/placeholder patterns (MOST COMMON ISSUE)
    spam_patterns = [
        'lorem ipsum',
        'test test test',
        'sample resume',
        'this is a test',
        'fake resume',
        'dummy text',
        'placeholder',
        'example text',
        'template resume',
        'your name here',
        'asdf',
        'qwerty',
        'xxxxxx',
        'sample content',
        'copy paste',
        'random text'
    ]
    for pattern in spam_patterns:
        if pattern in text_lower:
            return True, f"Resume contains placeholder/test content: '{pattern}'"
    
    # Check 3: Must have common resume sections (CRITICAL)
    required_sections = {
        'education': ['education', 'academic', 'degree', 'university', 'college', 'school'],
        'experience': ['experience', 'employment', 'work', 'internship', 'job'],
        'skills': ['skill', 'technical', 'programming', 'technology', 'tools']
    }
    
    sections_found = 0
    for section_type, keywords in required_sections.items():
        if any(keyword in text_lower for keyword in keywords):
            sections_found += 1
    
    if sections_found < 2:
        return True, "Resume missing critical sections (must have at least Education, Experience, OR Skills)"
    
    # Check 4: Check for actual professional/academic content
    professional_indicators = [
        # Educational terms
        'university', 'college', 'degree', 'bachelor', 'master', 'graduation', 'gpa', 'cgpa',
        'diploma', 'certificate', 'course', 'semester', 'academic', 'institute', 'school',
        
        # Professional terms
        'project', 'internship', 'worked', 'developed', 'created', 'implemented', 'designed',
        'built', 'managed', 'led', 'collaborated', 'achieved', 'improved', 'optimized',
        'analyzed', 'researched', 'trained', 'mentored', 'coordinated', 'delivered',
        
        # Technical/skill terms
        'programming', 'software', 'development', 'engineering', 'technology', 'system',
        'application', 'database', 'algorithm', 'code', 'framework', 'tool', 'platform'
    ]
    
    found_indicators = sum(1 for indicator in professional_indicators if indicator in text_lower)
    
    if found_indicators < 5:
        return True, "Resume lacks sufficient professional/academic content (needs more education, work, or technical details)"
    
    # Check 5: Gibberish detection - words with unusual character patterns
    if len(words) > 20:
        gibberish_count = 0
        for word in words:
            if len(word) > 8:  # Check longer words
                # Count vowels - gibberish has very few vowels
                vowels = sum(1 for c in word if c in 'aeiou')
                consonants = sum(1 for c in word if c.isalpha() and c not in 'aeiou')
                
                # Gibberish: < 15% vowels OR > 85% consonants
                if len(word) > 0:
                    vowel_ratio = vowels / len(word)
                    if vowel_ratio < 0.15 or (consonants > 0 and vowels / consonants < 0.2):
                        gibberish_count += 1
        
        # If > 20% of longer words are gibberish, reject
        longer_words = [w for w in words if len(w) > 8]
        if longer_words and gibberish_count / len(longer_words) > 0.2:
            return True, "Resume contains excessive gibberish/random text (unreadable words detected)"
    
    # Check 6: Minimum meaningful content
    meaningful_words = [w for w in words if len(w) > 3 and w.isalpha()]
    if len(meaningful_words) < 30:
        return True, "Resume has insufficient meaningful content (needs more substance)"
    
    # Check 7: Check for reasonable word variety (not just repeating same words)
    if len(words) > 50:
        unique_words = set(words)
        uniqueness_ratio = len(unique_words) / len(words)
        if uniqueness_ratio < 0.3:
            return True, "Resume has too much repetition (needs more variety in content)"
    
    return False, "Resume passed validation"


def extract_skills_from_text(text: str) -> list[str]:
    """
    Extract technical skills from resume text
    Returns: List of detected skills
    """
    if not text:
        return []
    
    text_lower = text.lower()
    
    # Comprehensive skill database
    all_skills = set()
    for domain_skills in DOMAIN_REQUIRED_SKILLS.values():
        all_skills.update([s.lower() for s in domain_skills])
    
    # Find skills mentioned in resume
    found_skills = []
    for skill in all_skills:
        # Use word boundaries to avoid partial matches
        pattern = r'\b' + re.escape(skill.lower()) + r'\b'
        if re.search(pattern, text_lower):
            found_skills.append(skill.title())
    
    return sorted(list(set(found_skills)))


def analyze_resume_against_job(resume_text: str, job_description: dict) -> tuple[int, dict]:
    """
    ENHANCED ATS-STYLE RESUME SCORING
    
    Analyzes resume quality and job-specific keyword matching
    
    Args:
        resume_text: Full text content of resume
        job_description: Dict with keys 'domain', 'required_skills', 'min_cgpa'
    
    Returns:
        (score: int, analysis: dict) where score is 0-100
    """
    score = 0
    analysis = {
        'resume_quality': 0,
        'keyword_match': 0,
        'skill_match': 0,
        'experience_signals': 0,
        'breakdown': []
    }
    
    if not resume_text:
        analysis['breakdown'].append("❌ No resume text provided")
        return 0, analysis
    
    text_lower = resume_text.lower()
    words = text_lower.split()
    
    # ===== 1. RESUME QUALITY & STRUCTURE (25 points) =====
    quality_score = 0
    
    # Word count (optimal: 200-600 words)
    word_count = len(words)
    if 200 <= word_count <= 600:
        quality_score += 10
        analysis['breakdown'].append(f"✅ Good length: {word_count} words (+10)")
    elif 100 <= word_count < 200 or 600 < word_count <= 800:
        quality_score += 5
        analysis['breakdown'].append(f"⚠️ Acceptable length: {word_count} words (+5)")
    else:
        analysis['breakdown'].append(f"⚠️ Length issue: {word_count} words (+0)")
    
    # Section structure
    sections = ['education', 'experience', 'skills', 'projects', 'certifications']
    sections_found = sum(1 for section in sections if section in text_lower)
    
    if sections_found >= 4:
        quality_score += 10
        analysis['breakdown'].append(f"✅ Excellent structure: {sections_found}/5 sections (+10)")
    elif sections_found >= 2:
        quality_score += 5
        analysis['breakdown'].append(f"⚠️ Basic structure: {sections_found}/5 sections (+5)")
    else:
        analysis['breakdown'].append(f"❌ Poor structure: {sections_found}/5 sections (+0)")
    
    # Professional formatting indicators
    formatting_keywords = ['•', '-', ':', 'bachelor', 'master', 'degree', 'gpa', 'cgpa']
    formatting_score = min(sum(2 for kw in formatting_keywords if kw in text_lower), 5)
    quality_score += formatting_score
    
    if formatting_score > 0:
        analysis['breakdown'].append(f"✅ Professional formatting (+{formatting_score})")
    
    score += quality_score
    analysis['resume_quality'] = quality_score
    
    # ===== 2. JOB-SPECIFIC KEYWORDS (30 points) =====
    keyword_score = 0
    
    domain = job_description.get('domain', 'General')
    domain_keywords = DOMAIN_REQUIRED_SKILLS.get(domain, DOMAIN_REQUIRED_SKILLS['General'])
    
    # Keywords found in resume
    keywords_found = []
    for keyword in domain_keywords:
        pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
        if re.search(pattern, text_lower):
            keywords_found.append(keyword)
    
    keyword_match_percent = (len(keywords_found) / len(domain_keywords)) * 100 if domain_keywords else 0
    keyword_score = min(int(keyword_match_percent * 0.3), 30)
    
    score += keyword_score
    analysis['keyword_match'] = keyword_score
    analysis['breakdown'].append(
        f"🎯 Domain keywords: {len(keywords_found)}/{len(domain_keywords)} found ({keyword_match_percent:.0f}%) (+{keyword_score})"
    )
    
    # ===== 3. TECHNICAL SKILLS MATCH (25 points) =====
    skill_score = 0
    
    required_skills = job_description.get('required_skills', '')
    if required_skills:
        required_list = [s.strip().lower() for s in required_skills.split(',')]
        skills_matched = []
        
        for req_skill in required_list:
            pattern = r'\b' + re.escape(req_skill) + r'\b'
            if re.search(pattern, text_lower):
                skills_matched.append(req_skill)
        
        skill_match_percent = (len(skills_matched) / len(required_list)) * 100 if required_list else 0
        skill_score = min(int(skill_match_percent * 0.25), 25)
        
        score += skill_score
        analysis['skill_match'] = skill_score
        analysis['breakdown'].append(
            f"🔧 Required skills: {len(skills_matched)}/{len(required_list)} matched ({skill_match_percent:.0f}%) (+{skill_score})"
        )
    else:
        analysis['breakdown'].append("⚠️ No specific skills required (+0)")
    
    # ===== 4. EXPERIENCE & IMPACT INDICATORS (20 points) =====
    experience_score = 0
    
    # Action verbs (shows active contribution)
    action_verbs = ['achieved', 'improved', 'developed', 'created', 'designed', 'implemented',
                    'built', 'led', 'managed', 'optimized', 'increased', 'decreased']
    action_count = sum(1 for verb in action_verbs if verb in text_lower)
    experience_score += min(action_count * 2, 10)
    
    if action_count > 0:
        analysis['breakdown'].append(f"✅ Action verbs: {action_count} found (+{min(action_count * 2, 10)})")
    
    # Quantifiable results (numbers, percentages, metrics)
    numbers = re.findall(r'\d+%|\d+x|\d+\+', text_lower)
    metrics_score = min(len(numbers) * 2, 10)
    experience_score += metrics_score
    
    if metrics_score > 0:
        analysis['breakdown'].append(f"📊 Quantifiable results: {len(numbers)} metrics (+{metrics_score})")
    
    score += experience_score
    analysis['experience_signals'] = experience_score
    
    # ===== FINAL SCORE =====
    final_score = min(score, 100)
    
    return final_score, analysis


def student_company_position_score(student, position, resume_text=None):
    """
    Calculate match score for student-position pair
    Uses RESUME-FIRST approach (60% weight on resume ATS analysis)
    
    Args:
        student: (user_id, name, email, skills, cgpa, domain, exp, resume_path, profile_photo, extracted_skills)
        position: (position_id, company_id, domain, required_skills, min_cgpa, positions, stipend)
        resume_text: Full resume text (if available)
    
    Returns:
        float: Score 0-100
    """
    sid = student[0]
    cgpa = student[4] or 0
    sdomain = student[5] or ""
    exp = student[6] or 0
    extracted_skills = student[9] or ""
    
    pid = position[0]
    pdomain = position[2]
    req_skills = position[3]
    min_cgpa = position[4]
    
    # Domain must match
    if normalize_domain(sdomain) != normalize_domain(pdomain):
        print(f"  ❌ Domain mismatch: Student wants {sdomain}, Position is {pdomain}")
        return 0
    
    # CGPA must meet minimum
    if cgpa < min_cgpa:
        print(f"  ❌ CGPA too low: {cgpa} < {min_cgpa}")
        return 0
    
    score = 0
    
    # Resume-based ATS scoring (60% of total score)
    if not resume_text:
        print(f"  ❌ Student {sid} has NO RESUME - cannot score")
        return 0
    
    job_desc = {
        'domain': pdomain,
        'required_skills': req_skills,
        'min_cgpa': min_cgpa
    }
    ats_score, analysis = analyze_resume_against_job(resume_text, job_desc)
    
    # 60% weight on resume ATS score
    score += ats_score * 0.6
    
    print(f"  ✅ Student {sid} ATS Score: {ats_score}/100")
    print(f"     Domain: {pdomain} | Required Skills: {req_skills[:50]}...")

    # CGPA contribution (20 points max)
    cgpa_points = (cgpa / 10.0) * 20
    score += cgpa_points
    
    # Experience contribution (10 points max)
    exp_points = min(exp * 3.33, 10)
    score += exp_points
    
    # Bonus for extracted skills matching (10 points max)
    if extracted_skills and req_skills:
        resume_skill_match = calculate_skill_match(extracted_skills, req_skills)
        skill_bonus = min(resume_skill_match / 10, 10)
        score += skill_bonus

    final_score = min(round(score, 2), 100.0)
    print(f"  ✅ Student {sid} Final Score: {final_score}/100 (CGPA: {cgpa_points:.1f}, Exp: {exp_points:.1f})")
    
    return final_score


def run_smart_allocation(students, positions, resume_texts=None):
    """
    FAIR ROUND-ROBIN ALLOCATION ALGORITHM
    
    Strategy:
    1. Validate all resumes (existing logic)
    2. Calculate scores for all student-position pairs
    3. GROUP matches by position/company
    4. Use ROUND-ROBIN allocation to ensure fair distribution
    5. Allocate best student to each company in turns
    
    Returns: List of allocations (student_id, company_id, position_id, score, rank)
    """
    if resume_texts is None:
        resume_texts = {}
    
    print("\n" + "=" * 80)
    print("🔍 PHASE 1: STRICT RESUME VALIDATION (RESUME REQUIRED!)")
    print("=" * 80)
    
    valid_students = []
    no_resume_count = 0
    fake_count = 0
    
    for student in students:
        student_id = student[0]
        resume_text = resume_texts.get(student_id, None)
        
        if not resume_text:
            print(f"❌ Student {student_id} EXCLUDED: NO RESUME UPLOADED (MANDATORY)")
            no_resume_count += 1
            continue
        
        is_fake, fake_reason = is_resume_fake_or_spam(resume_text)
        if is_fake:
            print(f"❌ Student {student_id} EXCLUDED: {fake_reason}")
            fake_count += 1
            continue
        
        print(f"✅ Student {student_id}: Resume validated")
        valid_students.append(student)
    
    print(f"\n📊 VALIDATION SUMMARY:")
    print(f"   Total students: {len(students)}")
    print(f"   Valid resumes: {len(valid_students)}")
    print(f"   No resume (EXCLUDED): {no_resume_count}")
    print(f"   Fake resumes (EXCLUDED): {fake_count}")
    print(f"   Eligible for allocation: {len(valid_students)}")
    
    if not valid_students:
        print("\n⚠️ NO ELIGIBLE STUDENTS FOUND - ALLOCATION ABORTED")
        return []
    
    print("\n" + "=" * 80)
    print("🎯 PHASE 2: CALCULATING MATCH SCORES")
    print("=" * 80)
    
    # Build position-specific candidate lists
    position_candidates_map = {}  # position_id -> [(student_id, company_id, score), ...]
    
    for position in positions:
        pid = position[0]
        company_id = position[1]
        domain = position[2]
        pos_num = position[5]
        
        print(f"\n📋 Position {pid}: {domain} at Company {company_id} ({pos_num} openings)")
        
        position_candidates = []
        for student in valid_students:
            student_id = student[0]
            resume_text = resume_texts.get(student_id, None)
            score = student_company_position_score(student, position, resume_text)
            
            if score > 0:
                position_candidates.append({
                    'student_id': student_id,
                    'company_id': company_id,
                    'position_id': pid,
                    'score': score
                })
        
        # Sort candidates for this position by score (highest first)
        position_candidates.sort(key=lambda x: x['score'], reverse=True)
        position_candidates_map[pid] = position_candidates
        
        if position_candidates:
            print(f"   Eligible candidates: {len(position_candidates)}")
            print(f"   Top 3 scores: {[f'S{c['student_id']}:{c['score']:.1f}' for c in position_candidates[:3]]}")
    
    print("\n" + "=" * 80)
    print("🎓 PHASE 3: FAIR ROUND-ROBIN ALLOCATION")
    print("=" * 80)
    
    # ========== FAIR ALLOCATION LOGIC ==========
    
    allocations = []
    taken_students = set()
    position_info = {}
    
    # Initialize position tracking
    for position in positions:
        pid = position[0]
        position_info[pid] = {
            'allocated': 0,
            'max_positions': position[5],
            'company_id': position[1],
            'domain': position[2],
            'current_rank': 1
        }
    
    # Create a queue of positions that still need allocations
    active_positions = list(position_info.keys())
    
    print(f"\n🔄 Round-robin allocation across {len(active_positions)} positions...\n")
    
    allocation_round = 1
    while active_positions:
        print(f"--- Round {allocation_round} ---")
        positions_allocated_this_round = 0
        positions_to_remove = []
        
        # Try to allocate one student to each active position
        for pid in active_positions:
            info = position_info[pid]
            
            # Check if position is full
            if info['allocated'] >= info['max_positions']:
                positions_to_remove.append(pid)
                continue
            
            # Get next best available student for this position
            candidates = position_candidates_map.get(pid, [])
            allocated_to_position = False
            
            for candidate in candidates:
                sid = candidate['student_id']
                
                # Skip if student already allocated
                if sid in taken_students:
                    continue
                
                # Allocate this student
                cid = candidate['company_id']
                score = candidate['score']
                rank = info['current_rank']
                
                allocations.append((sid, cid, pid, score, rank))
                taken_students.add(sid)
                info['allocated'] += 1
                info['current_rank'] += 1
                positions_allocated_this_round += 1
                allocated_to_position = True
                
                print(f"   ✅ Student {sid} → Company {cid}, Position {pid} (Rank #{rank}, Score: {score:.1f})")
                break
            
            # If no student was allocated and position still has space, check if any candidates remain
            if not allocated_to_position and info['allocated'] < info['max_positions']:
                # Check if there are any unallocated students left for this position
                has_available = any(c['student_id'] not in taken_students for c in candidates)
                if not has_available:
                    positions_to_remove.append(pid)
        
        # Remove positions that are full or have no more candidates
        for pid in positions_to_remove:
            if pid in active_positions:
                active_positions.remove(pid)
                print(f"   ℹ️ Position {pid} complete or no more candidates")
        
        # Break if no allocations were made this round
        if positions_allocated_this_round == 0:
            print(f"   ⚠️ No allocations possible this round - ending allocation")
            break
        
        allocation_round += 1
        print()
    
    print("=" * 80)
    print("✅ ALLOCATION COMPLETE")
    print("=" * 80)
    print(f"Total allocations: {len(allocations)}")
    print(f"Students allocated: {len(taken_students)}")
    print(f"Students not allocated: {len(valid_students) - len(taken_students)}")
    
    # Company-wise distribution
    print("\n📊 COMPANY-WISE DISTRIBUTION:")
    company_distribution = {}
    for alloc in allocations:
        cid = alloc[1]
        company_distribution[cid] = company_distribution.get(cid, 0) + 1
    
    for cid, count in sorted(company_distribution.items()):
        print(f"   Company {cid}: {count} students allocated")
    
    # Position-wise distribution
    print("\n📋 POSITION-WISE DISTRIBUTION:")
    for pid, info in sorted(position_info.items()):
        print(f"   Position {pid} (Company {info['company_id']}): {info['allocated']}/{info['max_positions']} filled")
    
    print("=" * 80 + "\n")
    
    return allocations


def analyze_resume_quality(text: str, domain: str = "General"):
    """
    Analyze resume quality with domain-specific skills
    
    Args:
        text: Resume text content
        domain: Student's domain of interest (AI, Data Science, Web Development, etc.)
    
    Returns: (score, detailed_analysis)
    """
    # Get domain-specific required skills
    required_skills = get_domain_skills(domain)
    
    # Create job description with domain and skills
    job_desc = {
        'domain': domain,
        'required_skills': required_skills,
        'min_cgpa': 0
    }
    
    print(f"[RESUME ANALYSIS] Domain: {domain}, Required Skills: {required_skills[:100]}...")
    
    return analyze_resume_against_job(text, job_desc)