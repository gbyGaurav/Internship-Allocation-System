def calculate_skill_match(student_skills: str, required: str) -> float:
    if not student_skills or not required:
        return 0.0
    s = {x.strip().lower() for x in student_skills.split(',') if x.strip()}
    r = {x.strip().lower() for x in required.split(',') if x.strip()}
    if not r:
        return 0.0
    return round(len(s & r) / len(r) * 100, 2)


def normalize_domain(d: str) -> str:
    return d.strip().lower().replace(" ", "").replace("-", "").replace("_", "")


def calculate_resume_quality_score(text: str, domain: str) -> tuple[float, dict]:
    """
    Returns (total_score 0-100, detailed_feedback dict)
    Detailed feedback has category: {score, max, msg}
    """
    text_lower = text.lower()
    total_score = 0.0
    feedback = {
        "Length": {"score": 0, "max": 30, "msg": ""},
        "Structure & Sections": {"score": 0, "max": 25, "msg": ""},
        "General Keywords": {"score": 0, "max": 20, "msg": ""},
        "Domain-Specific Keywords": {"score": 0, "max": 25, "msg": ""},
        "Achievement & Impact Language": {"score": 0, "max": 15, "msg": ""}
    }

    # 1. Length (max 30)
    word_count = len(text_lower.split())
    if word_count < 150:
        feedback["Length"]["msg"] = "Too short - aim for 200-400 words"
        feedback["Length"]["score"] = 10
    elif word_count > 600:
        feedback["Length"]["msg"] = "Quite long - consider condensing"
        feedback["Length"]["score"] = 15
    else:
        feedback["Length"]["msg"] = "Good length"
        feedback["Length"]["score"] = 30
    total_score += feedback["Length"]["score"]

    # 2. Structure & Sections (max 25)
    structure_keywords = ["education", "experience", "skills", "project", "internship", "certification", "summary", "objective"]
    found_structure = sum(1 for kw in structure_keywords if kw in text_lower)
    structure_score = min(found_structure * 4, 25)
    feedback["Structure & Sections"]["score"] = structure_score
    feedback["Structure & Sections"]["msg"] = f"{found_structure}/{len(structure_keywords)} key sections detected"
    total_score += structure_score

    # 3. General Keywords / Soft Skills (max 20)
    general_keywords = ["teamwork", "communication", "leadership", "problem solving", "analytical", "adaptable", "time management"]
    found_general = sum(1 for kw in general_keywords if kw in text_lower)
    general_score = min(found_general * 3, 20)
    feedback["General Keywords"]["score"] = general_score
    feedback["General Keywords"]["msg"] = f"{found_general}/{len(general_keywords)} soft skills keywords found"
    total_score += general_score

    # 4. Domain-Specific Keywords (max 25)
    domain_keywords = {
        "ai": ["machine learning", "deep learning", "python", "tensorflow", "pytorch", "neural", "nlp", "computer vision", "ai", "artificial intelligence"],
        "data science": ["python", "r", "sql", "pandas", "statistics", "visualization", "machine learning", "big data", "data analysis"],
        "cyber security": ["cybersecurity", "network security", "ethical hacking", "penetration testing", "firewall", "encryption", "linux", "vulnerability", "malware", "security"],
        "web development": ["html", "css", "javascript", "react", "angular", "vue", "node.js", "django", "flask", "api", "frontend", "backend", "responsive"],
    }
    domain_lower = domain.lower()
    if domain_lower in domain_keywords:
        d_kws = domain_keywords[domain_lower]
        found_domain = sum(1 for kw in d_kws if kw in text_lower)
        domain_score = min(found_domain * 5, 25)
        feedback["Domain-Specific Keywords"]["score"] = domain_score
        feedback["Domain-Specific Keywords"]["msg"] = f"{found_domain}/{len(d_kws)} domain keywords found"
    else:
        feedback["Domain-Specific Keywords"]["score"] = 0
        feedback["Domain-Specific Keywords"]["msg"] = f"Domain '{domain}' not recognized - add relevant keywords"
    total_score += feedback["Domain-Specific Keywords"]["score"]

    # 5. Achievement & Impact Language (max 15)
    achievement_words = ["increased", "improved", "reduced", "achieved", "led", "managed", "developed", "boosted", "%", "by", "from", "to"]
    has_achievement = any(word in text_lower for word in achievement_words)
    if has_achievement:
        feedback["Achievement & Impact Language"]["score"] = 15
        feedback["Achievement & Impact Language"]["msg"] = "Good use of achievement-oriented language"
    else:
        feedback["Achievement & Impact Language"]["score"] = 0
        feedback["Achievement & Impact Language"]["msg"] = "Add quantifiable achievements (e.g. 'increased efficiency by 30%')"
    total_score += feedback["Achievement & Impact Language"]["score"]

    # Final cap at 100
    total_score = min(total_score, 100.0)

    return round(total_score, 1), feedback


def student_company_position_score(student, position):
    sid, skills, cgpa, interest_domain, exp, extracted_skills = student
    pid, cid, pdomain, req_skills, min_cgpa, pos, stipend = position

    if normalize_domain(interest_domain) != normalize_domain(pdomain):
        return 0.0

    if cgpa < min_cgpa:
        return 0.0

    all_skills = (skills + ',' + extracted_skills) if extracted_skills else skills

    score = 0.0
    skill_match = calculate_skill_match(all_skills, req_skills)
    score += skill_match * 0.35
    score += (cgpa / 10.0) * 25
    score += 30
    score += min(exp * 5, 10)

    resume_match = calculate_skill_match(extracted_skills, req_skills)
    score += 20 if resume_match >= 80 else (10 if resume_match >= 50 else 0)

    return min(round(score, 2), 100.0)


def run_smart_allocation(students, positions):
    matches = []

    for position in positions:
        pid = position[0]
        pos_num = position[5]

        position_matches = []
        for student in students:
            score = student_company_position_score(student, position)
            if score > 0:
                position_matches.append((student[0], score))

        position_matches.sort(key=lambda x: x[1], reverse=True)
        matches.append((pid, position[1], pos_num, position_matches))

    matches.sort(key=lambda x: x[3][0][1] if x[3] else 0, reverse=True)

    allocations = []
    taken = set()

    for pid, cid, pos_num, pmatches in matches:
        count = 0
        rank = 1
        for sid, score in pmatches:
            if sid not in taken and count < pos_num:
                allocations.append((sid, cid, pid, score, rank))
                taken.add(sid)
                count += 1
                rank += 1

    return allocations