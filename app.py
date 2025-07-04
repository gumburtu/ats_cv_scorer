import streamlit as st
import tempfile
import os
import docx2txt
import pdfplumber
import re
import json

# --- 1. Kriter Matrisleri ---

CRITERIA = {
    "Manual Tester": {
        "Anahtar Kelimeler & Teknik Terimler": [
            "Software Tester", "QA Tester", "Quality Assurance", "Manual Tester", "QA Engineer",
            "Smoke Testing", "Sanity Testing", "Regression Testing", "User Acceptance Testing", "UAT",
            "Exploratory Testing", "Ad-hoc Testing", "Functional Testing", "Integration Testing", "System Testing",
            "JIRA", "Zephyr", "TestRail", "Xray", "ALM", "Quality Center", "Bugzilla", "Mantis",
            "Test Plan", "Test Case", "Test Scenario", "Bug Report", "Defect Tracking"
        ],
        "Yöntemler & Yaklaşımlar": [
            "SDLC", "STLC", "Agile", "Scrum", "Defect Lifecycle", "Peer Review",
            "Test Case Review", "Requirement Traceability Matrix", "RTM"
        ],
        "Yumuşak Beceriler & Güçlü İfadeler": [
            "detail oriented", "communication", "teamwork", "time management", "problem solving"
        ],
        "Ekstralar": [
            "SQL", "SELECT", "JOIN", "WHERE", "test data preparation", "API testing", "Postman"
        ]
    },
    "Test Automation Engineer": {
        "Anahtar Kelimeler & Teknik Terimler": [
            "Test Automation Engineer", "QA Automation", "SDET", "Software Development Engineer in Test",
            "Selenium WebDriver", "Cypress", "Playwright", "Appium", "TestNG", "JUnit", "NUnit", "Cucumber",
            "BDD", "TDD", "Java", "Python", "C#", "JavaScript", "TypeScript",
            "Postman", "Rest Assured", "SoapUI", "Karate",
            "Jenkins", "GitLab CI/CD", "GitHub Actions",
            "Extent Reports", "Allure Reports"
        ],
        "Yöntemler & Yaklaşımlar": [
            "Page Object Model", "Data Driven", "Keyword Driven", "Hybrid",
            "Git", "GitHub", "Bitbucket", "Docker", "Virtual Machines", "Pipeline"
        ],
        "Yumuşak Beceriler & Güçlü İfadeler": [
            "clean code", "code review", "mentoring", "debugging", "automation ROI"
        ],
        "Ekstralar": [
            "JMeter", "LoadRunner", "OWASP", "AWS", "Azure DevOps"
        ]
    },
    "Full Stack Automation Engineer": {
        "Anahtar Kelimeler & Teknik Terimler": [
            "Full Stack QA", "Full Stack Test Automation Engineer", "SDET",
            "UI automation", "API automation",
            "database testing", "stored procedures", "views",
            "JMeter", "Gatling", "Locust", "OWASP", "ZAP", "Burp Suite",
            "Infrastructure as Code", "Docker Compose", "Kubernetes", "Terraform",
            "mock data", "service virtualization"
        ],
        "Yöntemler & Yaklaşımlar": [
            "end-to-end test", "microservice", "test strategy", "contract testing",
            "Pact", "Spring Cloud Contract", "distributed test execution"
        ],
        "Yumuşak Beceriler & Güçlü İfadeler": [
            "leadership", "mentoring", "test strategy", "test debt", "cross-functional", "efficiency metrics"
        ],
        "Ekstralar": [
            "WireMock", "performance test report", "security vulnerability", "scan results"
        ]
    }
}

# --- 2. ATS Tavsiye Mesajları ---
ATS_TIPS = [
    "Başlık ve özet kısmında rol odaklı anahtar kelimeler kullanın.",
    "Her araç, metodoloji ve framework güncel isimleriyle yer almalı.",
    "İş deneyimlerinde bağlamsal anahtar kelimeler kullanmaya özen gösterin.",
    "Kısaltmalar yerine açıklamalı isim kullanın (örn: 'JIRA Bug Tracking Tool').",
    "Teknik yetkinlikleri 'Skills' veya 'Core Competencies' başlığında öne çıkarın.",
    "İngilizce kullanın, Türkçe terimlerden kaçının.",
    "Dosya formatını PDF veya DOCX olarak kullanın.",
    "Yumuşak becerileri de anahtar kelime olarak belirtin.",
    "Sertifikaları ve LinkedIn URL’nizi eklemeyi unutmayın."
]

# --- 3. CV'den Metin Çıkarma ---
def extract_text(file):
    if file.type == "application/pdf":
        with pdfplumber.open(file) as pdf:
            return " ".join([page.extract_text() or "" for page in pdf.pages])
    elif file.type in [
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"
    ]:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
            tmp.write(file.read())
            text = docx2txt.process(tmp.name)
        os.unlink(tmp.name)
        return text
    return ""

# --- 4. Anahtar Kelime Eşleşmesi (Her başlıktan birkaçını bulmak yeterli!) ---
def match_criteria(cv_text, criteria_dict):
    cv_lower = cv_text.lower()
    summary = {}
    for main_cat, keywords in criteria_dict.items():
        found = [k for k in keywords if k.lower() in cv_lower]
        # En az 2-3 anahtar kelime eşleşmesi olması yeterli
        summary[main_cat] = {
            "found": found,
            "missing": [k for k in keywords if k not in found],
            "count": len(found)
        }
    return summary

def get_critical_missing(matched, critical_n=2):
    # Her ana başlıktan eksik olanları, az eşleşme varsa kritik olarak çıkar
    critical = []
    for main, result in matched.items():
        if result['count'] < critical_n:
            critical += result['missing'][:critical_n]
    return critical

def calculate_score(matched):
    # Eşleşen toplam anahtar kelime sayısının oranı üzerinden puanlama
    total = sum(len(v["found"]) + len(v["missing"]) for v in matched.values())
    found = sum(len(v["found"]) for v in matched.values())
    if total == 0: return 0
    raw = round((found / total) * 100)
    # 90 üzeri zor, 75-85 iyi, 60-74 geliştirilebilir, altı zayıf
    return min(raw+7, 100) if raw > 0 else 0

def get_recommendation(role, matched, crit_missing):
    recs = []
    if crit_missing:
        recs.append(f"Kritik eksikler: {', '.join(crit_missing)}")
    if matched.get("Ekstralar", {}).get("count", 0) < 2:
        if role == "Manual Tester":
            recs.append("SQL ve temel API test yeteneklerinizi vurgulayın.")
        elif role == "Test Automation Engineer":
            recs.append("Performance, security ve cloud test araçlarından bazılarını belirtin.")
        else:
            recs.append("Mock servis, güvenlik veya performans test araçları ekleyin.")
    recs.append("Sertifika ve LinkedIn linkinizi eklemeyi unutmayın.")
    return recs

# --- 5. Streamlit Arayüzü ---
st.set_page_config(page_title="🎯 ATS CV Puanlayıcı", layout="centered")
st.title("🎯 ATS CV Puanlayıcı")
st.caption(
    "Yazılım Test Mühendisliği rollerine özel: CV'nizi ATS sistemleri öncesi puanlayın, kritik öneriler alın!"
)

role = st.selectbox(
    "📌 Hedef Rolünüzü Seçin",
    list(CRITERIA.keys()),
    help="Başvurmak istediğiniz yazılım testi rolünü seçin."
)
uploaded_file = st.file_uploader(
    "📄 CV'nizi Yükleyin (PDF veya DOCX)", type=["pdf", "docx"]
)

if st.button("🚀 CV'yi Analiz Et"):
    if not uploaded_file:
        st.warning("Lütfen önce bir CV dosyası yükleyin.")
        st.stop()

    cv_text = extract_text(uploaded_file)
    if not cv_text or len(cv_text) < 200:
        st.error("CV'den yeterli metin çıkarılamadı. Lütfen farklı bir dosya ile tekrar deneyin.")
        st.stop()

    matched = match_criteria(cv_text, CRITERIA[role])
    crit_missing = get_critical_missing(matched)
    score = calculate_score(matched)
    recs = get_recommendation(role, matched, crit_missing)

    # Sonuç formatı
    st.markdown(f"""
    <br>
    <b>[ROLE]</b> <span style="color:#5BCEFA">{role}</span>  
    <b>[MATCHING KEYWORDS]</b> {sum(len(v['found']) for v in matched.values())} / {sum(len(v['found']) + len(v['missing']) for v in matched.values())}  
    <b>[CRITICAL TO IMPROVE]</b> {'Eksik: ' + ', '.join(crit_missing) if crit_missing else 'Yok'}  
    <b>[SCORE]</b> <span style="font-size:30px">{score}/100</span>  
    """, unsafe_allow_html=True)

    if score < 60:
        st.error("🔴 Büyük revizyon gerekli.")
    elif score < 75:
        st.warning("🟠 Geliştirme gerekli.")
    else:
        st.success("🟢 Güçlü bir CV!")

    st.subheader("🎯 Kişiselleştirilmiş Öneriler")
    for r in recs:
        st.write("•", r)

    st.markdown("---")
    st.markdown("##### **Ana Kriterler ve Bulunanlar**")
    for head, vals in matched.items():
        st.markdown(f"**{head}**: {', '.join(vals['found']) if vals['found'] else 'Yok'}")

    with st.expander("⚙️ ATS için Genel İpuçları"):
        for tip in ATS_TIPS:
            st.write("•", tip)
