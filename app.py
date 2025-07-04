import streamlit as st
import tempfile
import os
import docx2txt
import pdfplumber
import re
import io
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

# ==== UTILITIES ====

def extract_text_from_docx(docx_file):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
        tmp.write(docx_file.read())
        text = docx2txt.process(tmp.name)
    os.unlink(tmp.name)
    return text

def extract_text_from_pdf(pdf_file):
    text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

def preprocess_text(text):
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^a-z0-9\s.,]", "", text)
    return text

def get_keywords_for_role(role):
    # Genişletilebilir - role göre anahtar kelimeler
    keywords = {
        "Manual Tester": [
            "test case", "test scenario", "manual testing", "bug", "jira", "test plan", "test execution",
            "defect", "exploratory", "regression", "test documentation", "qa process"
        ],
        "Test Automation Engineer": [
            "selenium", "python", "java", "cypress", "automation", "webdriver", "pytest", "jenkins",
            "ci/cd", "test script", "api testing", "postman", "rest", "bdd", "tdd", "page object",
            "maven", "gradle", "testng", "allure", "robot framework", "git", "docker"
        ],
        "Full Stack Automation Engineer": [
            "frontend automation", "backend automation", "selenium", "cypress", "rest assured",
            "playwright", "javascript", "typescript", "java", "python", "docker", "kubernetes",
            "ci/cd", "aws", "azure", "microservices", "api automation", "performance testing",
            "load testing", "jmeter", "gatling", "database testing", "graphql"
        ]
    }
    return keywords.get(role, [])

def keyword_score(cv_text, keywords):
    # Anahtar kelime eşleşme oranı
    cv_text = preprocess_text(cv_text)
    matches = [kw for kw in keywords if kw in cv_text]
    score = int(100 * len(matches) / len(keywords)) if keywords else 0
    missing = [kw for kw in keywords if kw not in cv_text]
    return score, matches, missing

def extract_action_verbs(text):
    # Sık kullanılan action verb'ler listesi
    verbs = [
        "developed", "designed", "implemented", "created", "led", "managed", "executed",
        "improved", "analyzed", "optimized", "tested", "automated", "collaborated",
        "integrated", "supported", "documented"
    ]
    found = [v for v in verbs if v in text.lower()]
    return found

def find_metrics(text):
    # Sayısal metrikleri bul
    pattern = r"\d+(\.\d+)?\s?(%|percent|users|cases|bugs|issues|coverage|time|minutes|hours|days|saniye|dk|test|project|release|sprint)"
    found = re.findall(pattern, text.lower())
    return list(set([f[0] for f in found])) if found else []

def similarity_with_job_desc(cv_text, job_desc):
    # TF-IDF ile benzerlik ölçümü
    try:
        vect = TfidfVectorizer(stop_words="english")
        tfidf = vect.fit_transform([cv_text, job_desc])
        sim = (tfidf * tfidf.T).A[0, 1]
        return int(sim * 100)
    except Exception:
        return 0

def section_scores(cv_text, role_keywords, job_desc=None):
    kw_score, present_kw, missing_kw = keyword_score(cv_text, role_keywords)
    verbs = extract_action_verbs(cv_text)
    metrics = find_metrics(cv_text)
    if job_desc:
        sim_score = similarity_with_job_desc(cv_text, job_desc)
    else:
        sim_score = None
    # Ağırlıklandırılmış skor
    base = 0.5 * kw_score + 0.2 * (len(verbs)*5) + 0.2 * (len(metrics)*5)
    if sim_score is not None:
        base = 0.6 * base + 0.4 * sim_score
    base = min(int(base), 100)
    return {
        "overall": base,
        "keywords": kw_score,
        "present_keywords": present_kw,
        "missing_keywords": missing_kw,
        "action_verbs": verbs,
        "metrics": metrics,
        "job_desc_similarity": sim_score
    }

def personalized_feedback(scores, role):
    feedback = []
    # Anahtar kelime önerisi
    if scores["keywords"] < 70:
        feedback.append(f"🔑 **Anahtar Kelimeler**: {len(scores['missing_keywords'])} eksik anahtar kelime bulundu. "
                        f"CV'nize şunları eklemeyi değerlendirin: {', '.join(scores['missing_keywords'][:5])}.")
    else:
        feedback.append("✅ Anahtar kelimeler yeterli düzeyde kullanılmış.")

    # Action verb önerisi
    if len(scores["action_verbs"]) < 4:
        feedback.append("🔨 **İfade Gücü**: Daha fazla etkili action verb (örn. designed, implemented, improved) kullanın.")
    else:
        feedback.append("✅ Güçlü action verb'ler kullanılmış.")

    # Metrik önerisi
    if len(scores["metrics"]) < 2:
        feedback.append("📊 **Metrik ve Sonuçlar**: Proje ve görevlerinizde sayısal sonuç/metrik belirtmeye çalışın (örn. %30 daha hızlı, 100+ test case vs.).")
    else:
        feedback.append("✅ CV'de sayısal metrikler yer alıyor.")

    # İş ilanı ile benzerlik
    if scores.get("job_desc_similarity") is not None:
        if scores["job_desc_similarity"] < 30:
            feedback.append("🎯 **İş İlanı Uyumu**: CV'nizi iş ilanındaki gereksinimlerle daha uyumlu hale getirin.")
        elif scores["job_desc_similarity"] < 60:
            feedback.append("🟠 İş ilanı ile kısmen uyumlu. Daha fazla ortak anahtar kelime kullanabilirsiniz.")
        else:
            feedback.append("✅ İş ilanı ile yüksek uyumluluk.")
    return feedback

# ==== STREAMLIT UI ====

st.set_page_config(page_title="🎯 ATS CV Puanlayıcı", layout="centered")
st.title("🎯 ATS CV Puanlayıcı")
st.caption(
    "Manuel Tester • Test Automation Engineer • Full Stack Automation Engineer için özelleştirilmiş CV analizi ve ATS uyumluluk puanı"
)

st.markdown(
    """
    <style>
    .big-score {font-size: 40px; font-weight: bold; color: #5BCEFA;}
    .feedback {font-size: 17px;}
    </style>
    """,
    unsafe_allow_html=True
)

role = st.selectbox(
    "📌 Hedef Rolünüzü Seçin",
    (
        "Manual Tester",
        "Test Automation Engineer",
        "Full Stack Automation Engineer"
    ),
    help="Başvurmak istediğiniz pozisyonu seçin."
)

uploaded_file = st.file_uploader(
    "📄 CV'nizi Yükleyin (PDF veya DOCX)", type=["pdf", "docx"]
)

job_desc = st.text_area(
    "🎯 İş İlanı Ekleyin (Opsiyonel)",
    placeholder="Başvurduğunuz iş ilanından önemli gereksinimleri buraya yapıştırabilirsiniz.",
    help="İş ilanı eklerseniz, CV'nizin ilanla uyumu da ölçülür."
)

if st.button("🚀 CV'yi Analiz Et"):
    if uploaded_file is not None:
        try:
            # Dosya metnini çıkar
            if uploaded_file.type == "application/pdf":
                cv_text = extract_text_from_pdf(uploaded_file)
            elif uploaded_file.type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"]:
                cv_text = extract_text_from_docx(uploaded_file)
            else:
                st.error("Yalnızca PDF ve DOCX dosyaları desteklenmektedir.")
                st.stop()
            if not cv_text or len(cv_text) < 200:
                st.warning("CV'nizden yeterli metin çıkarılamadı. Farklı bir dosya ile tekrar deneyin.")
                st.stop()

            role_keywords = get_keywords_for_role(role)
            scores = section_scores(cv_text, role_keywords, job_desc if job_desc.strip() else None)

            st.markdown(f"<div class='big-score'>📊 {scores['overall']}/100</div>", unsafe_allow_html=True)

            if scores['overall'] < 60:
                st.error("🔴 Büyük Revizyon Gerekli")
            elif scores['overall'] < 80:
                st.warning("🟠 İyileştirme Gerekli")
            else:
                st.success("🟢 Harika! CV'niz ATS için güçlü görünüyor.")

            with st.expander("🔗 Analiz Detayları"):
                st.markdown(f"""
                - **Anahtar Kelime Skoru:** {scores['keywords']} / 100  
                - **Kullanılan Anahtar Kelimeler:** {', '.join(scores['present_keywords']) if scores['present_keywords'] else 'Yok'}
                - **Eksik Anahtar Kelimeler:** {', '.join(scores['missing_keywords']) if scores['missing_keywords'] else 'Yok'}
                - **Action Verb'ler:** {', '.join(scores['action_verbs']) if scores['action_verbs'] else 'Yok'}
                - **Sayısal Metrikler:** {', '.join(scores['metrics']) if scores['metrics'] else 'Yok'}
                """)

                if scores.get("job_desc_similarity") is not None:
                    st.markdown(f"- **İş İlanı Uyumluluk Skoru:** %{scores['job_desc_similarity']}")

            st.subheader("🎯 Kişiselleştirilmiş Öneriler")
            for f in personalized_feedback(scores, role):
                st.markdown(f"<div class='feedback'>{f}</div>", unsafe_allow_html=True)

            st.markdown(
                """
                <hr>
                <small>
                Not: Bu analiz, modern ATS yazılımlarının anahtar kelime ve içerik odaklı bakış açılarını simüle eder. Sonuçlar, öneri niteliğindedir.
                </small>
                """,
                unsafe_allow_html=True
            )
        except Exception as e:
            st.error(f"Analiz sırasında hata oluştu: {e}")
    else:
        st.warning("Lütfen önce bir CV dosyası yükleyin.")