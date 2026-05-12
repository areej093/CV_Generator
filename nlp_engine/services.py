import spacy
import logging
import re
import PyPDF2

logger = logging.getLogger(__name__)

try:
    nlp = spacy.load('en_core_web_sm')
except OSError:
    logger.warning("en_core_web_sm not found. Falling back to blank model. NLP extraction might not be accurate until downloaded.")
    nlp = spacy.blank('en')

# Comprehensive ESCO/ROME dictionary for tech and business
ESCO_SKILLS_DB = {
    # Programming Languages
    "python": ["Software Engineer", "Data Scientist", "Backend Developer", "AI Engineer"],
    "java": ["Software Engineer", "Backend Developer", "Android Developer"],
    "javascript": ["Frontend Developer", "Full Stack Developer", "Node.js Developer"],
    "typescript": ["Frontend Developer", "Full Stack Developer", "Angular Developer"],
    "c++": ["Systems Engineer", "Game Developer", "Embedded Software Engineer"],
    "c#": [".NET Developer", "Game Developer", "Backend Developer"],
    "ruby": ["Backend Developer", "Ruby on Rails Developer"],
    "go": ["Backend Developer", "Cloud Engineer", "Systems Engineer"],
    "php": ["Backend Developer", "WordPress Developer"],
    "swift": ["iOS Developer", "Mobile Engineer"],
    "kotlin": ["Android Developer", "Mobile Engineer"],
    
    # Frameworks & Libraries
    "django": ["Backend Developer", "Full Stack Developer", "Python Developer"],
    "react": ["Frontend Developer", "Full Stack Developer", "UI Developer"],
    "angular": ["Frontend Developer", "Web Developer"],
    "vue": ["Frontend Developer", "Web Developer"],
    "spring": ["Backend Developer", "Java Developer"],
    "express": ["Backend Developer", "Node.js Developer"],
    "flask": ["Backend Developer", "Python Developer"],
    
    # Data & AI
    "machine learning": ["Data Scientist", "AI Engineer", "Machine Learning Engineer"],
    "deep learning": ["AI Researcher", "Machine Learning Engineer"],
    "data analysis": ["Data Analyst", "Business Intelligence Analyst"],
    "sql": ["Data Analyst", "Database Administrator", "Backend Developer"],
    "nosql": ["Database Administrator", "Backend Developer"],
    "pandas": ["Data Scientist", "Data Analyst"],
    "tensorflow": ["AI Engineer", "Machine Learning Engineer"],
    "pytorch": ["AI Engineer", "Machine Learning Engineer"],
    
    # DevOps & Cloud
    "docker": ["DevOps Engineer", "Backend Developer", "Cloud Architect"],
    "kubernetes": ["DevOps Engineer", "Cloud Architect", "Site Reliability Engineer"],
    "aws": ["Cloud Architect", "DevOps Engineer", "Backend Developer"],
    "azure": ["Cloud Architect", "DevOps Engineer", "Systems Administrator"],
    "gcp": ["Cloud Architect", "Data Engineer"],
    "ci/cd": ["DevOps Engineer", "Release Manager"],
    "linux": ["Systems Administrator", "DevOps Engineer", "Backend Developer"],
    
    # Soft Skills & Business
    "project management": ["Project Manager", "Scrum Master", "Product Manager"],
    "agile": ["Scrum Master", "Project Manager", "Software Engineer"],
    "scrum": ["Scrum Master", "Agile Coach"],
    "leadership": ["Manager", "Team Lead", "Director"],
    "communication": ["HR Specialist", "Sales Representative", "Product Manager"],
    "marketing": ["Marketing Specialist", "Growth Hacker", "SEO Specialist"],
    "seo": ["SEO Specialist", "Digital Marketer"],
    "sales": ["Account Executive", "Sales Representative"],
    "customer service": ["Customer Support Specialist", "Account Manager"],
    "ui/ux": ["UX Designer", "UI Designer", "Product Designer"],
    "figma": ["UX Designer", "UI Designer"],
    "adobe xd": ["UX Designer", "UI Designer"],
    "photoshop": ["Graphic Designer", "UI Designer"],
    "illustrator": ["Graphic Designer"],
    "node.js": ["Backend Developer", "Full Stack Developer"],
    "html": ["Frontend Developer", "Web Developer"],
    "css": ["Frontend Developer", "Web Developer"],
    "git": ["Software Engineer", "Developer"],
    "github": ["Software Engineer", "Developer"],
    "mongodb": ["Database Administrator", "Backend Developer"],
    "postgresql": ["Database Administrator", "Backend Developer"],
    "mysql": ["Database Administrator", "Backend Developer"],
    "redis": ["Backend Developer"],
    "rest api": ["Backend Developer", "Full Stack Developer"],
    "graphql": ["Frontend Developer", "Backend Developer"],
    "unit testing": ["Software Engineer", "QA Engineer"],
    "cypress": ["QA Engineer", "Frontend Developer"],
    "jest": ["Frontend Developer"],
    "selenium": ["QA Engineer"],
}

JOB_REQUIREMENTS_DB = {
    "Software Engineer": ["python", "java", "sql", "git", "agile", "unit testing"],
    "Frontend Developer": ["javascript", "html", "css", "react", "ui/ux", "typescript", "git"],
    "Data Scientist": ["python", "machine learning", "sql", "pandas", "data analysis", "deep learning"],
    "Backend Developer": ["python", "django", "sql", "docker", "linux", "go", "rest api"],
    "DevOps Engineer": ["docker", "kubernetes", "aws", "linux", "ci/cd", "git"],
    "Cloud Architect": ["aws", "azure", "docker", "kubernetes", "linux"],
    "Project Manager": ["project management", "agile", "scrum", "leadership", "communication"],
    "UX Designer": ["ui/ux", "figma", "communication", "html", "css", "adobe xd"],
    "AI Engineer": ["python", "machine learning", "deep learning", "tensorflow", "pytorch"],
    "Data Analyst": ["sql", "data analysis", "python", "pandas", "communication"],
    "Graphic Designer": ["photoshop", "illustrator", "figma", "communication"],
    "QA Engineer": ["selenium", "unit testing", "cypress", "git", "communication"],
}

def extract_skills_from_text(text):
    if not text:
        return []
    
    text_lower = text.lower()
    # Normalize some common variations
    text_lower = text_lower.replace('node js', 'node.js').replace('nodejs', 'node.js')
    
    extracted_skills = set()
    
    # Language-Agnostic Extraction
    for skill in ESCO_SKILLS_DB.keys():
        # Special tech words with symbols or dots
        if skill in ['c++', 'c#', 'ui/ux', 'ci/cd', '.net', 'node.js']:
            if skill in text_lower:
                extracted_skills.add(skill)
        else:
            # Use regex word boundaries for accurate matching
            if re.search(r'\b' + re.escape(skill) + r'\b', text_lower):
                extracted_skills.add(skill)
                
    return list(extracted_skills)

def calculate_profile_completeness(cv):
    score = 0
    max_score = 100
    
    # Personal Info (max 20)
    if cv.full_name: score += 5
    if cv.email: score += 5
    if cv.phone: score += 5
    if cv.summary and len(cv.summary) > 20: score += 5
        
    # Experiences (max 30)
    exp_count = cv.experiences.count()
    if exp_count >= 2: score += 30
    elif exp_count == 1: score += 15
        
    # Education (max 20)
    if cv.education.exists(): score += 20
        
    # Skills (max 20)
    skill_count = cv.skills.count()
    if skill_count >= 5: score += 20
    elif skill_count > 0: score += 10
        
    # Languages & Certs (max 10)
    if hasattr(cv, 'languages') and cv.languages.exists(): score += 5
    if hasattr(cv, 'certifications') and cv.certifications.exists(): score += 5
        
    return min(score, max_score)

def get_job_recommendations(skills):
    job_scores = {}
    for skill in skills:
        skill_lower = skill.lower()
        if skill_lower in ESCO_SKILLS_DB:
            for job in ESCO_SKILLS_DB[skill_lower]:
                job_scores[job] = job_scores.get(job, 0) + 1
                
    sorted_jobs = sorted(job_scores.items(), key=lambda x: x[1], reverse=True)[:3]
    
    recommendations = []
    user_skills_set = set([s.lower() for s in skills])
    
    for job, score in sorted_jobs:
        req_skills = JOB_REQUIREMENTS_DB.get(job, [])
        missing = [s for s in req_skills if s.lower() not in user_skills_set]
        
        match_percentage = 0
        if req_skills:
            match_percentage = int(((len(req_skills) - len(missing)) / len(req_skills)) * 100)
            
        recommendations.append({
            "job_title": job,
            "match_score": score,
            "match_percentage": match_percentage,
            "missing_skills": missing
        })
        
    return recommendations

def analyze_cv(cv):
    score = calculate_profile_completeness(cv)
    
    text_corpus = cv.summary + " "
    for exp in cv.experiences.all():
        text_corpus += f"{exp.position} {exp.company} {exp.description} "
        
    nlp_extracted_skills = extract_skills_from_text(text_corpus)
    
    explicit_skills = [s.name.lower() for s in cv.skills.all()]
    all_skills = list(set(nlp_extracted_skills + explicit_skills))
    
    recommendations = get_job_recommendations(all_skills)
    
    return {
        "completeness_score": score,
        "explicit_skills": explicit_skills,
        "nlp_extracted_skills": nlp_extracted_skills,
        "recommended_jobs": recommendations,
        "status": "success"
    }

def parse_pdf_to_json(file_obj):
    """
    ATS Parser: Reads a PDF file, extracts raw text, and uses Regex and our NLP Engine
    to pull out auto-fillable fields for the CV form.
    """
    try:
        reader = PyPDF2.PdfReader(file_obj)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
    except Exception as e:
        logger.error(f"Error reading PDF: {e}")
        return {"error": "Failed to read PDF file. Make sure it is a valid PDF document."}
        
    # Regex Extractions
    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
    email = email_match.group(0) if email_match else ""
    
    # Enhanced phone regex for French (06 12 34 56 78) & International formats
    phone_match = re.search(r'(?:(?:\+|00)33|0)\s*[1-9](?:[\s.-]*\d{2}){4}|(?:\+?\d[\d -]{8,15}\d)', text)
    phone = phone_match.group(0).strip() if phone_match else ""
    
    # Smart Heuristic for Name (Skips common CV titles in English/French)
    ignore_words = ["curriculum vitae", "cv", "resume", "résumé", "profil", "profile", "développeur", "developer"]
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    name = ""
    for line in lines[:5]:  # Check first 5 lines
        if len(line) < 3 or len(line) > 40:
            continue
        if any(ignore in line.lower() for ignore in ignore_words):
            continue
        # If it doesn't contain a number, it's likely the name
        if not re.search(r'\d', line):
            name = line
            break
    
    # Use our existing NLP Engine to extract ALL skills found in the PDF!
    extracted_skills = extract_skills_from_text(text)
    
    return {
        "fullName": name,
        "email": email,
        "phone": phone,
        "extracted_skills": extracted_skills
    }

def match_cv_to_job(cv, job):
    """
    AI Match Score & Gap Analysis:
    Compares CV skills with Job requirements to calculate a match %
    and identifies missing skills.
    """
    # 1. Extract job skills (from title, description and requirements)
    job_text = f"{job.title} {job.description} {job.requirements}"
    job_skills = set(extract_skills_from_text(job_text))
    
    # 2. Extract CV skills (NLP + Explicit)
    cv_text = f"{cv.professional_title} {cv.summary}"
    for exp in cv.experiences.all():
        cv_text += f" {exp.position} {exp.description}"
    
    cv_skills_nlp = set(extract_skills_from_text(cv_text))
    cv_skills_explicit = set([s.name.lower() for s in cv.skills.all()])
    cv_skills = cv_skills_nlp.union(cv_skills_explicit)
    
    # 3. Calculate match
    if not job_skills:
        # Default match based on Title similarity if no tech skills found
        match_percentage = 70 if (job.title.lower() in cv.professional_title.lower() or cv.professional_title.lower() in job.title.lower()) else 50
        return {"match_percentage": match_percentage, "matching_skills": [], "missing_skills": []}
        
    matching_skills = list(job_skills.intersection(cv_skills))
    missing_skills = list(job_skills.difference(cv_skills))
    
    # Improved Matching Logic
    # 1. Base score from skill overlap (max 60%)
    base_match = (len(matching_skills) / len(job_skills)) * 60
    
    # 2. Title matching bonus (max 30%)
    title_bonus = 0
    job_title_words = set(job.title.lower().split())
    cv_title_words = set(cv.professional_title.lower().split())
    
    # Full phrase match
    if job.title.lower() in cv.professional_title.lower() or cv.professional_title.lower() in job.title.lower():
        title_bonus = 30
    else:
        # Partial word match bonus
        common_words = job_title_words.intersection(cv_title_words)
        # Filter out common stop words if necessary, but for job titles most words are significant
        if common_words:
            title_bonus = min(20, len(common_words) * 10)
    
    # 3. Experience bonus (max 10%)
    # Users with more experience entries in a related field should get a slight boost
    experience_bonus = min(10, cv.experiences.count() * 5)
        
    match_percentage = int(min(100, base_match + title_bonus + experience_bonus))
    
    # Quality Floor: If they have the exact title and some skills, don't let it be too low
    if title_bonus >= 30 and len(matching_skills) > 0:
        match_percentage = max(match_percentage, 75)
        
    # Force 100% for perfect keyword matches
    if not missing_skills and len(matching_skills) > 0:
        match_percentage = 100
        
    return {
        "match_percentage": match_percentage,
        "matching_skills": matching_skills,
        "missing_skills": missing_skills
    }

def generate_cover_letter(cv, job):
    """
    AI Content Generator: Creates a customized cover letter.
    """
    skills_list = [s.name for s in cv.skills.all()][:3]
    top_skills = ", ".join(skills_list) if skills_list else "my professional expertise"
    
    prev_comp = cv.experiences.first().company if cv.experiences.exists() else "my previous experience"
    
    letter = f"""Dear Hiring Manager at {job.company.name},

I am writing to express my strong interest in the {job.title} position. With my background as a {cv.professional_title} and my expertise in {top_skills}, I am confident that I can contribute effectively to your team.

My experience at {prev_comp} has prepared me to tackle the challenges described in the {job.title} role. I am particularly drawn to this opportunity at {job.company.name} because of your focus on innovation and excellence in {job.location}.

My skills align well with your requirements, especially in areas such as {", ".join(extract_skills_from_text(job.description)[:3])}. I am eager to bring my unique perspective and problem-solving abilities to your organization.

Thank you for considering my application. I look forward to the possibility of discussing how my skills and experience can support the goals of {job.company.name}.

Best regards,

{cv.full_name}"""
    
    return letter.strip()
