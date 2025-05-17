import os
import streamlit as st
from dotenv import load_dotenv
from PyPDF2 import PdfReader
import requests

# ── Load your Groq API key ────────────────────────────────────────────────────
load_dotenv()  # reads from .env
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    st.error("❌ GROQ_API_KEY not found in .env. Please add it and restart.")
    st.stop()

# ── Streamlit page config ─────────────────────────────────────────────────────
st.set_page_config(page_title="CV & Cover Letter Generator", layout="centered")
st.title("🎯 CV & Cover Letter Generator (via Groq Cloud)")

st.write(
    "1. Upload your current resume (PDF)  \n"
    "2. Paste the Job Description  \n"
    "3. Click **Generate** to get a tailored CV snippet + cover letter."
)

# ── UI Inputs ─────────────────────────────────────────────────────────────────
resume_file = st.file_uploader("📄 Upload your resume (PDF)", type=["pdf"])
jd = st.text_area(
    "🧐 Paste the Job Description here:",
    height=200,
    placeholder="e.g. “Seeking an experienced Python developer with AWS…”"
)

# ── Helpers ─────────────────────────────────────────────────────────────────────
def parse_resume(pdf_file) -> str:
    reader = PdfReader(pdf_file)
    pages = [p.extract_text() or "" for p in reader.pages]
    return "\n\n".join(pages)

def generate_documents(resume_text: str, jd_text: str) -> tuple[str, str]:
    """
    Send the same chat-completions payload to Groq’s OpenAI-compatible API.
    """
    prompt = (
        "You are a career coach. Given the candidate’s resume and the job description, produce:\n\n"
        "1) A concise, skill-focused CV section tailored to the JD.\n"
        "2) A crisp, professional cover letter that highlights the candidate’s fit.\n\n"
        "=== Resume ===\n"
        f"{resume_text}\n\n"
        "=== Job Description ===\n"
        f"{jd_text}\n\n"
        "Return the CV first, then on its own line “---”, then the cover letter."
    )

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GROQ_API_KEY}"
    }
    payload = {
        "model": "llama-3.3-70b-versatile",  # or pick another available model
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 1500
    }

    r = requests.post(url, headers=headers, json=payload)  # :contentReference[oaicite:0]{index=0}
    r.raise_for_status()
    data = r.json()
    content = data["choices"][0]["message"]["content"]
    cv_snip, cover = content.split("---", 1)
    return cv_snip.strip(), cover.strip()

# ── Generate Button Logic ──────────────────────────────────────────────────────
if st.button("🚀 Generate"):
    if not resume_file or not jd.strip():
        st.warning("⚠️ Please provide both a PDF resume and a job description.")
    else:
        with st.spinner("🔍 Parsing resume…"):
            text = parse_resume(resume_file)
        with st.spinner("✍️ Generating via Groq Cloud…"):
            try:
                cv_out, cover_out = generate_documents(text, jd)
            except requests.HTTPError as e:
                st.error(f"❌ API request failed: {e}")
            else:
                st.subheader("📝 Tailored CV Snippet")
                st.write(cv_out)
                st.subheader("📄 Cover Letter")
                st.write(cover_out)
