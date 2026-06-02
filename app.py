import re
import streamlit as st
from matcher import match_resume, generate_suggestions
import PyPDF2
import docx
import pandas as pd
import json
import os

st.set_page_config(page_title="AI Resume Matcher", layout="centered")

# -------- USER STORAGE --------
USERS_FILE = "users.json"

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        try:
            data = json.load(f)
        except:
            return {}

    # 🔄 Auto-migrate old format -> new format
    updated = False
    for u, val in list(data.items()):
        if isinstance(val, str):  # old format
            data[u] = {"email": "", "password": val}
            updated = True

    if updated:
        save_users(data)

    return data

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

USERS = load_users()

# -------- SESSION --------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user" not in st.session_state:
    st.session_state.user = None

if "history" not in st.session_state:
    st.session_state.history = []

if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = "login"

# -------- AUTH SYSTEM --------
def auth_page():
    col1, col2, col3 = st.columns([1,2,1])

    with col2:

        # LOGIN
        if st.session_state.auth_mode == "login":
            st.markdown("## 🔐 Login")

            username = st.text_input("Username", key="login_user", autocomplete="off")
            password = st.text_input("Password", type="password", key="login_pass", autocomplete="off")

            if st.button("Login"):
                if username in USERS:
                    stored_password = USERS[username].get("password")

                    if stored_password == password:
                        st.session_state.logged_in = True
                        st.session_state.user = username
                        st.rerun()
                    else:
                        st.error("Invalid credentials")
                else:
                    st.error("Invalid credentials")

            st.markdown("---")

            colA, colB = st.columns(2)

            with colA:
                if st.button("Create Account"):
                    st.session_state.auth_mode = "signup"
                    st.rerun()

            with colB:
                if st.button("Forgot Password"):
                    st.session_state.auth_mode = "forgot"
                    st.rerun()

        # SIGNUP
        elif st.session_state.auth_mode == "signup":
            st.markdown("## 📝 Signup")

            username = st.text_input("Choose Username", key="signup_user")
            email = st.text_input("Email (optional)", key="signup_email")
            password = st.text_input("Choose Password", type="password", key="signup_pass")

            if st.button("Create Account"):
                if not username or not password:
                    st.warning("Fill required fields")
                elif username in USERS:
                    st.warning("Username already exists")
                else:
                    USERS[username] = {
                        "email": email,
                        "password": password
                    }
                    save_users(USERS)
                    st.success("Account created! Please login")
                    st.session_state.auth_mode = "login"
                    st.rerun()

            if st.button("Back to Login"):
                st.session_state.auth_mode = "login"
                st.rerun()

        # FORGOT PASSWORD
        elif st.session_state.auth_mode == "forgot":
            st.markdown("## 🔑 Reset Password")

            username = st.text_input("Enter Username", key="forgot_user")
            new_password = st.text_input("New Password", type="password", key="forgot_pass")

            if st.button("Update Password"):
                if username not in USERS:
                    st.error("User not found")
                elif not new_password:
                    st.warning("Enter new password")
                else:
                    USERS[username]["password"] = new_password
                    save_users(USERS)
                    st.success("Password updated! Please login")
                    st.session_state.auth_mode = "login"
                    st.rerun()

            if st.button("Back to Login"):
                st.session_state.auth_mode = "login"
                st.rerun()

def logout():
    st.session_state.logged_in = False
    st.session_state.user = None
    st.rerun()

# -------- PROTECT --------
if not st.session_state.logged_in:
    auth_page()
    st.stop()

# -------- SIDEBAR --------
st.sidebar.title("📂 Navigation")

if "page" not in st.session_state:
    st.session_state.page = "Home"

if st.sidebar.button("🏠 Home"):
    st.session_state.page = "Home"

if st.sidebar.button("📜 History"):
    st.session_state.page = "History"

if st.sidebar.button("ℹ️ About"):
    st.session_state.page = "About"

st.sidebar.write(f"👤 {st.session_state.user}")

if st.sidebar.button("Logout"):
    logout()

menu = st.session_state.page

# -------- UI --------
st.markdown("""
<style>
.stApp {
    background: linear-gradient(to right, #0f172a, #1e293b);
    color: white;
}
</style>
""", unsafe_allow_html=True)

# -------- FILE HANDLING --------
def extract_text_from_pdf(file):
    reader = PyPDF2.PdfReader(file)
    return "".join([p.extract_text() or "" for p in reader.pages])

def extract_text_from_docx(file):
    doc = docx.Document(file)
    return " ".join([p.text for p in doc.paragraphs])

# -------- TEXT NORMALIZATION --------
# -------- TEXT NORMALIZATION --------

def normalize_text(text):

    synonyms = {
        "ml": "machine learning",
        "ai": "artificial intelligence",
        "js": "javascript"
    }

    text = text.lower()

    # safer synonym replacement
    for k, v in synonyms.items():
        text = re.sub(rf'\b{k}\b', v, text)

    # remove special characters
    text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)

    # remove extra spaces
    text = re.sub(r'\s+', ' ', text).strip()

    return text

# =========================
# HOME
# =========================
if menu == "Home":

    st.title("📄 AI Resume Matcher")

    mode = st.radio("Choose Mode:", ["Single Resume", "Multiple Resumes"])

    # SINGLE
    if mode == "Single Resume":

        job_desc = st.text_area("📋 Paste Job Description", key="single_jd")
        uploaded_file = st.file_uploader("📄 Upload Resume", type=["pdf","docx"])

        if st.button("🚀 Analyze Resume"):

            if uploaded_file and job_desc:

                job_desc = normalize_text(job_desc)

                if uploaded_file.type == "application/pdf":
                    resume_text = extract_text_from_pdf(uploaded_file)
                else:
                    resume_text = extract_text_from_docx(uploaded_file)

                resume_text = normalize_text(resume_text)

                score, matched, missing = match_resume(resume_text, job_desc)

                st.progress(int(score))
                st.success(f"Match Score: {score}%")

                st.session_state.history.append({
                    "User": st.session_state.user,
                    "Resume": uploaded_file.name,
                    "Score": score
                })

                st.subheader("✅ Matched Skills")

                if matched:
                    for skill in matched:
                        st.success(skill)
                else:
                    st.info("No matching skills found")

                st.subheader("❌ Missing Skills")

                if missing:
                    for skill in missing:
                        st.error(skill)
                else:
                    st.success("No missing skills")

                st.subheader("💡 Suggestions")
                for s in generate_suggestions(missing):
                    st.write("👉", s)

            else:
                st.warning("Upload resume and enter job description")

    # MULTIPLE
    else:

        job_desc = st.text_area("📋 Paste Job Description", key="multi_jd")
        uploaded_files = st.file_uploader("📄 Upload Resumes", accept_multiple_files=True)

        if st.button("🚀 Compare Resumes"):

            if uploaded_files and job_desc:

                job_desc = normalize_text(job_desc)
                results = []

                for file in uploaded_files:

                    if file.type == "application/pdf":
                        resume_text = extract_text_from_pdf(file)
                    else:
                        resume_text = extract_text_from_docx(file)

                    resume_text = normalize_text(resume_text)

                    score, matched, missing = match_resume(resume_text, job_desc)

                    results.append({
                        "Resume": file.name,
                        "Score": score,
                        "Missing": missing
                    })

                results = sorted(results, key=lambda x: x["Score"], reverse=True)

                st.subheader("🏆 Resume Ranking")

                for i, res in enumerate(results):

                    st.markdown(f"### {i+1}. {res['Resume']}")
                    st.progress(int(res["Score"]))
                    st.write(f"Score: {res['Score']}%")

                    if res["Missing"]:

                        st.write("❌ Missing Skills:")

                        for skill in res["Missing"][:5]:
                            st.write(f"- {skill}")

                    else:
                        st.success("All required skills matched")

                    for s in generate_suggestions(res["Missing"]):
                        st.write("👉", s)

                    st.divider()

                df = pd.DataFrame(results)
                st.download_button("📥 Download Results", df.to_csv(index=False))

            else:
                st.warning("Upload resumes and enter job description")

# =========================
# HISTORY
# =========================
elif menu == "History":

    st.title("📜 History")

    user_history = [h for h in st.session_state.history if h["User"] == st.session_state.user]

    if user_history:
        st.dataframe(pd.DataFrame(user_history))
    else:
        st.info("No history yet")

# =========================
# ABOUT
# =========================
else:

    st.title("ℹ️ About")

    st.write("""
    AI Resume Matcher System

    Features:
    - Resume vs Job Description matching
    - Skill extraction using NLP
    - Resume ranking
    - Suggestions for improvement
    - Multi-user authentication
    - History tracking
    """) 