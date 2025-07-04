import streamlit as st
import tempfile
import os
import docx2txt
import pdfplumber
import re
import json
from datetime import datetime
import openai

# --- 1. Streamlit Ayarları ---
st.set_page_config(
    page_title="🎯 LLM Destekli ATS CV Puanlayıcı",
    page_icon="🎯",
    layout="wide"
)

# --- 2. OpenAI API Key ---
# Streamlit secrets dosyasını kullan: streamlit.io'da AYARLAR > Secrets bölümüne ekleyebilirsin
openai.api_key = st.secrets.get("OPENAI_API_KEY")

# --- 3. Dark Theme ---
def inject_dark_theme():
    st.markdown("""
    <style>
    body {
        background-color: #1e1e1e;
        color: #ffffff;
    }
    .block-container {
        background-color: #1e1e1e;
    }
    .stButton > button {
        background-color: #0066cc;
        color: #ffffff;
        border-radius: 8px;
    }
    .stButton > button:hover {
        background-color: #0052a3;
    }
    </style>
    """, unsafe_allow_html=True)

inject_dark_theme()

# --- 4. Dosya Okuma ---
def extract_text(file) -> str:
    if file.type == "application/pdf":
        text = ""
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text
    elif file.type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"]:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
            tmp.write(file.read())
            text = docx2txt.process(tmp.name)
        os.unlink(tmp.name)
        return text
    else:
        return ""

def preprocess_text(text: str) -> str:
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s\-\.]', ' ', text)
    return text.strip()

# --- 5. LLM Çağrısı ---
def call_llm_analysis(cv_text: str, role: str) -> dict:
    prompt = f"""
You are an ATS CV analyzer for a {role} position.
Analyze the following CV text.
- Extract relevant skills, tools, methodologies, frameworks.
- Estimate years of experience if possible.
- Identify missing important keywords for this role.
- Provide 5 clear recommendations to improve the CV for ATS systems.
Return a JSON object with: {{
  "extracted_skills": [...],
  "missing_skills": [...],
  "experience_years": int,
  "recommendations": [...],
  "role_fit_score": float
}}
CV TEXT:
{cv_text[:4000]}
"""
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are an ATS CV analysis expert for software testing."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1
    )

    result = response['choices'][0]['message']['content']

    try:
        result_json = json.loads(result)
    except json.JSONDecodeError:
        result_json = {"error": "JSON parsing error. Raw result: " + result}

    return result_json

# --- 6. Uygulama ---
st.title("🎯 LLM Destekli ATS CV Puanlayıcı")

st.markdown("""
Yazılım Test Mühendisliği rollerine başvururken CV'nizin ATS uyumluluğunu GPT-4o ile analiz edin.
""")

role = st.selectbox(
    "📌 Hedef Rol",
    ["Manual Tester", "Test Automation Engineer", "Full Stack Automation Engineer"]
)

uploaded_file = st.file_uploader(
    "📄 CV Yükle (PDF veya DOCX)",
    type=["pdf", "docx"]
)

if st.button("🚀 LLM ile Analiz Et"):
    if not uploaded_file:
        st.warning("Lütfen bir dosya yükleyin.")
        st.stop()

    with st.spinner("LLM CV'nizi analiz ediyor..."):
        raw_text = extract_text(uploaded_file)
        cleaned_text = preprocess_text(raw_text)

        if len(cleaned_text) < 100:
            st.error("CV'den yeterli metin çıkarılamadı.")
            st.stop()

        llm_result = call_llm_analysis(cleaned_text, role)

    if "error" in llm_result:
        st.error(llm_result["error"])
    else:
        st.success("Analiz tamamlandı!")
        st.markdown(f"## 🎯 ATS Skoru: **{llm_result['role_fit_score']}%**")
        st.markdown(f"**Tahmini Deneyim:** {llm_result['experience_years']} yıl")
        
        st.markdown("### ✅ Tespit Edilen Yetkinlikler")
        st.write(llm_result["extracted_skills"])

        st.markdown("### ❌ Eksik Bulunanlar")
        st.write(llm_result["missing_skills"])

        st.markdown("### 💡 Öneriler")
        for rec in llm_result["recommendations"]:
            st.markdown(f"- {rec}")

        # JSON rapor indirme
        report_data = {
            "Role": role,
            "Score": llm_result["role_fit_score"],
            "Experience_Years": llm_result["experience_years"],
            "Extracted_Skills": llm_result["extracted_skills"],
            "Missing_Skills": llm_result["missing_skills"],
            "Recommendations": llm_result["recommendations"],
            "Analysis_Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        st.download_button(
            label="📥 JSON Raporu İndir",
            data=json.dumps(report_data, indent=2, ensure_ascii=False),
            file_name=f"cv_analysis_{role.lower().replace(' ', '_')}.json",
            mime="application/json"
        )

else:
    st.info("""
    👈 Sol panelden rolünüzü seçin, CV'nizi yükleyin ve 'LLM ile Analiz Et' butonuna basın.
    """)

