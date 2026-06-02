# =========================
# SKILLS DATABASE
# =========================

SKILLS_DB = [

    # Programming Languages
    "python",
    "java",
    "c",
    "c++",
    "javascript",
    "html",
    "css",

    # Frameworks / Libraries
    "react",
    "node.js",
    "pandas",
    "numpy",
    "matplotlib",
    "tensorflow",
    "keras",
    "scikit-learn",

    # AI / ML
    "machine learning",
    "deep learning",
    "natural language processing",
    "nlp",
    "data analysis",
    "data visualization",

    # Databases
    "sql",
    "mysql",
    "mongodb",

    # Tools / Platforms
    "aws",
    "cloud computing",
    "git",
    "github",
    "power bi",
    "tableau",
    "excel"
]

# =========================
# SKILL EXTRACTION
# =========================

def extract_skills(text):

    text = text.lower()

    found_skills = []

    for skill in SKILLS_DB:

        if skill.lower() in text:
            found_skills.append(skill)

    return list(set(found_skills))

# =========================
# MATCH FUNCTION
# =========================

def match_resume(resume_text, job_desc):

    resume_skills = extract_skills(resume_text)
    jd_skills = extract_skills(job_desc)

    matched = list(set(resume_skills) & set(jd_skills))

    missing = list(set(jd_skills) - set(resume_skills))

    if len(jd_skills) == 0:
        score = 0
    else:
        score = round((len(matched) / len(jd_skills)) * 100, 2)

    return score, matched, missing

# =========================
# SUGGESTIONS
# =========================

def generate_suggestions(missing_skills):

    suggestions = []

    if missing_skills:

        suggestions.append(
            "Consider adding these skills: " +
            ", ".join(missing_skills[:5])
        )

    return suggestions