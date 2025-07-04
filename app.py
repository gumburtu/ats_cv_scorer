import streamlit as st
import tempfile
import os
import docx2txt
import pdfplumber
import re
import json
from datetime import datetime
from typing import Dict, List

# --- 1. Kriter Matrisleri ---
CRITERIA = {
    "Manual Tester": {
        "Temel Test Bilgileri": [
            "Software Tester", "QA Tester", "Quality Assurance", "Manual Tester", "QA Engineer",
            "Test Engineer", "Quality Engineer", "Software Quality Analyst", "Test Analyst"
        ],
        "Test Türleri": [
            "Smoke Testing", "Sanity Testing", "Regression Testing", "User Acceptance Testing", "UAT",
            "Exploratory Testing", "Ad-hoc Testing", "Functional Testing", "Integration Testing", 
            "System Testing", "Unit Testing", "End-to-End Testing", "Black Box Testing", "White Box Testing",
            "Boundary Testing", "Negative Testing", "Compatibility Testing", "Usability Testing"
        ],
        "Test Araçları": [
            "JIRA", "Zephyr", "TestRail", "Xray", "ALM", "Quality Center", "Bugzilla", "Mantis",
            "Azure DevOps", "qTest", "PractiTest", "Testlink", "Confluence", "Trello"
        ],
        "Dokümantasyon": [
            "Test Plan", "Test Case", "Test Scenario", "Bug Report", "Defect Tracking",
            "Test Strategy", "Test Suite", "Test Data", "Requirement Traceability Matrix", "RTM",
            "Test Execution Report", "Defect Report", "Test Summary Report"
        ],
        "Metodolojiler": [
            "SDLC", "STLC", "Agile", "Scrum", "Defect Lifecycle", "Peer Review",
            "Test Case Review", "Waterfall", "Kanban", "DevOps", "Continuous Testing"
        ],
        "Teknik Beceriler": [
            "SQL", "SELECT", "JOIN", "WHERE", "test data preparation", "API testing", "Postman",
            "REST API", "SOAP", "JSON", "XML", "Database Testing", "Web Testing", "Mobile Testing"
        ],
        "Yumuşak Beceriler": [
            "detail oriented", "communication", "teamwork", "time management", "problem solving",
            "analytical thinking", "critical thinking", "attention to detail", "documentation skills"
        ]
    },
    "Test Automation Engineer": {
        "Automation Frameworks": [
            "Selenium WebDriver", "Cypress", "Playwright", "Appium", "TestNG", "JUnit", "NUnit", 
            "Cucumber", "SpecFlow", "Robot Framework", "Protractor", "WebDriverIO", "Puppeteer"
        ],
        "Programming Languages": [
            "Java", "Python", "C#", "JavaScript", "TypeScript", "Kotlin", "Scala", "Ruby", "Go"
        ],
        "Test Approaches": [
            "BDD", "TDD", "Data Driven", "Keyword Driven", "Hybrid", "Page Object Model", "POM",
            "Behavior Driven Development", "Test Driven Development", "ATDD"
        ],
        "API Testing": [
            "Postman", "Rest Assured", "SoapUI", "Karate", "Newman", "Insomnia", "Swagger",
            "REST API", "SOAP", "GraphQL", "API automation", "Contract Testing"
        ],
        "CI/CD & DevOps": [
            "Jenkins", "GitLab CI/CD", "GitHub Actions", "Azure DevOps", "TeamCity", "Bamboo",
            "Docker", "Kubernetes", "Pipeline", "Continuous Integration", "Continuous Deployment"
        ],
        "Version Control": [
            "Git", "GitHub", "Bitbucket", "GitLab", "SVN", "Mercurial", "Version Control"
        ],
        "Reporting": [
            "Extent Reports", "Allure Reports", "TestNG Reports", "Cucumber Reports", "Report Portal"
        ],
        "Additional Skills": [
            "Maven", "Gradle", "npm", "pip", "Virtual Machines", "AWS", "Azure", "GCP"
        ]
    },
    "Full Stack Automation Engineer": {
        "Full Stack Testing": [
            "Full Stack QA", "Full Stack Test Automation Engineer", "SDET", "Full Stack Testing",
            "End-to-End Testing", "System Integration Testing", "Cross-Platform Testing"
        ],
        "UI & Frontend": [
            "UI automation", "Frontend Testing", "Cross-Browser Testing", "Responsive Testing",
            "Visual Testing", "Accessibility Testing", "Component Testing"
        ],
        "API & Backend": [
            "API automation", "Backend Testing", "Microservice Testing", "Service Testing",
            "Contract Testing", "Pact", "Spring Cloud Contract", "WireMock"
        ],
        "Database & Data": [
            "Database testing", "stored procedures", "views", "Data validation", "ETL Testing",
            "NoSQL", "MongoDB", "PostgreSQL", "MySQL", "Oracle", "SQL Server"
        ],
        "Performance & Security": [
            "JMeter", "Gatling", "Locust", "LoadRunner", "Performance Testing", "Load Testing",
            "OWASP", "ZAP", "Burp Suite", "Security Testing", "Vulnerability Testing"
        ],
        "Infrastructure & Cloud": [
            "Infrastructure as Code", "Docker Compose", "Kubernetes", "Terraform", "Ansible",
            "AWS", "Azure", "GCP", "Cloud Testing", "Containerization"
        ],
        "Advanced Concepts": [
            "Service virtualization", "Mock data", "Test Strategy", "Test Architecture",
            "Distributed Testing", "Parallel Execution", "Test Orchestration"
        ],
        "Leadership & Strategy": [
            "Test Leadership", "Mentoring", "Test Strategy", "Test Planning", "Team Lead",
            "Cross-functional", "Stakeholder Management", "Test Metrics", "ROI Analysis"
        ]
    }
}

# --- 2. ATS Tavsiyeleri ---
ATS_TIPS = {
    "Genel": [
        "Başlık ve özet kısmında rol odaklı anahtar kelimeler kullanın",
        "Her araç, metodoloji ve framework güncel isimleriyle yer almalı",
        "İş deneyimlerinde bağlamsal anahtar kelimeler kullanmaya özen gösterin",
        "Kısaltmalar yerine açıklamalı isim kullanın (örn: 'JIRA Bug Tracking Tool')",
        "Teknik yetkinlikleri 'Skills' veya 'Core Competencies' başlığında öne çıkarın"
    ],
    "Format": [
        "İngilizce kullanın, Türkçe terimlerden kaçının",
        "Dosya formatını PDF veya DOCX olarak kullanın",
        "Başlıkları net ve standart tutun (Experience, Skills, Education)",
        "Bullet point kullanın ve her maddeyi aksiyon verbleriyle başlatın"
    ],
    "İçerik": [
        "Yumuşak becerileri de anahtar kelime olarak belirtin",
        "Sertifikaları ve LinkedIn URL'nizi eklemeyi unutmayın",
        "Proje sonuçlarını sayısal verilerle destekleyin",
        "İş deneyimlerinde sorumluluk ve başarıları vurgulayın"
    ]
}

# --- 3. Dark Theme CSS ---
def inject_dark_theme():
    st.markdown("""
    <style>
    .main .block-container {
        background-color: #1e1e1e;
        color: #ffffff;
        padding-top: 2rem;
    }
    .css-1d391kg {
        background-color: #2d2d2d;
    }
    .stMarkdown, .stText, p, h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
    }
    .metric-container {
        background-color: #2d2d2d;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #404040;
    }
    .streamlit-expanderHeader {
        background-color: #2d2d2d;
        color: #ffffff;
    }
    .stHTML {
        background-color: transparent;
    }
    .stInfo {
        background-color: #2d2d2d;
        color: #ffffff;
    }
    .stWarning {
        background-color: #4a3000;
        color: #ffffff;
    }
    .stError {
        background-color: #4a0000;
        color: #ffffff;
    }
    .stSuccess {
        background-color: #004a00;
        color: #ffffff;
    }
    .stButton > button {
        background-color: #0066cc;
        color: #ffffff;
        border: none;
        border-radius: 8px;
    }
    .stButton > button:hover {
        background-color: #0052a3;
    }
    .stSelectbox > div > div {
        background-color: #2d2d2d;
        color: #ffffff;
    }
    .stFileUploader {
        background-color: #2d2d2d;
        border-radius: 8px;
    }
    .stColumns {
        background-color: transparent;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. Yardımcı Fonksiyonlar ---

class CVAnalyzer:
    def __init__(self):
        self.cv_text = ""
        self.analysis_results = {}

    def extract_text(self, file) -> str:
        try:
            if file.type == "application/pdf":
                with pdfplumber.open(file) as pdf:
                    text = ""
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                    return text
            elif file.type in [
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document", 
                "application/msword"
            ]:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
                    tmp.write(file.read())
                    text = docx2txt.process(tmp.name)
                os.unlink(tmp.name)
                return text
            else:
                return ""
        except Exception as e:
            st.error(f"Dosya okuma hatası: {str(e)}")
            return ""

    def preprocess_text(self, text: str) -> str:
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s\-\+\#\.]', ' ', text)
        return text.strip()

    def extract_experience_years(self, text: str) -> int:
        patterns = [
            r'(\d+)\s*(?:years?|yıl|year)',
            r'(\d+)\s*(?:yr|y)s?',
            r'experience.*?(\d+)',
            r'(\d+)\s*(?:years?|yıl)\s*(?:of\s*)?experience'
        ]
        years = []
        for pattern in patterns:
            matches = re.findall(pattern, text.lower())
            years.extend([int(m) for m in matches if m.isdigit()])
        return max(years) if years else 0

    def match_criteria(self, cv_text: str, criteria_dict: Dict) -> Dict:
        cv_lower = cv_text.lower()
        summary = {}
        for main_cat, keywords in criteria_dict.items():
            found = []
            for keyword in keywords:
                if keyword.lower() in cv_lower:
                    found.append(keyword)
            missing = [k for k in keywords if k not in found]
            summary[main_cat] = {
                "found": found,
                "missing": missing,
                "count": len(found),
                "percentage": round((len(found) / len(keywords)) * 100, 1) if keywords else 0
            }
        return summary

    def calculate_detailed_score(self, matched: Dict) -> Dict:
        total_keywords = sum(len(v["found"]) + len(v["missing"]) for v in matched.values())
        total_found = sum(len(v["found"]) for v in matched.values())
        if total_keywords == 0:
            return {"overall": 0, "by_category": {}}
        category_scores = {}
        for cat, results in matched.items():
            total_cat = len(results["found"]) + len(results["missing"])
            if total_cat > 0:
                category_scores[cat] = round((len(results["found"]) / total_cat) * 100, 1)
            else:
                category_scores[cat] = 0
        overall_score = round((total_found / total_keywords) * 100, 1)
        bonus = 0
        if overall_score > 70:
            bonus += 5
        if overall_score > 85:
            bonus += 5
        final_score = min(overall_score + bonus, 100)
        return {
            "overall": final_score,
            "by_category": category_scores,
            "total_keywords": total_keywords,
            "total_found": total_found,
            "bonus": bonus
        }

    def get_recommendations(self, role: str, matched: Dict, score_info: Dict) -> List[str]:
        recommendations = []
        low_categories = [cat for cat, score in score_info["by_category"].items() if score < 50]
        if low_categories:
            recommendations.append(f"🔴 Öncelikli geliştirme alanları: {', '.join(low_categories)}")
        if role == "Manual Tester":
            if score_info["by_category"].get("Teknik Beceriler", 0) < 50:
                recommendations.append("💡 SQL ve API testing becerilerinizi geliştirin ve CV'nize ekleyin")
            if score_info["by_category"].get("Test Araçları", 0) < 60:
                recommendations.append("🔧 Popüler test araçlarından (JIRA, TestRail) deneyiminizi vurgulayın")
        elif role == "Test Automation Engineer":
            if score_info["by_category"].get("Programming Languages", 0) < 60:
                recommendations.append("💻 Programlama dili yetkinliğinizi açık bir şekilde belirtin")
            if score_info["by_category"].get("Automation Frameworks", 0) < 50:
                recommendations.append("🤖 Selenium, Cypress gibi automation framework deneyiminizi ekleyin")
        elif role == "Full Stack Automation Engineer":
            if score_info["by_category"].get("Performance & Security", 0) < 40:
                recommendations.append("⚡ Performance ve security testing araçlarından deneyiminizi belirtin")
            if score_info["by_category"].get("Infrastructure & Cloud", 0) < 40:
                recommendations.append("☁️ Cloud platform ve DevOps araçları deneyiminizi ekleyin")
        if score_info["overall"] < 70:
            recommendations.append("📄 CV'nizde daha fazla teknik detay ve proje örneği ekleyin")
        recommendations.append("🎯 LinkedIn profilinizi ve sertifikalarınızı eklemeyi unutmayın")
        recommendations.append("📊 Proje sonuçlarınızı sayısal verilerle destekleyin")
        return recommendations

    def analyze_cv(self, file, role: str) -> Dict:
        raw_text = self.extract_text(file)
        if not raw_text or len(raw_text) < 100:
            return {"error": "CV'den yeterli metin çıkarılamadı"}
        self.cv_text = self.preprocess_text(raw_text)
        matched = self.match_criteria(self.cv_text, CRITERIA[role])
        score_info = self.calculate_detailed_score(matched)
        experience_years = self.extract_experience_years(self.cv_text)
        recommendations = self.get_recommendations(role, matched, score_info)
        return {
            "matched": matched,
            "score_info": score_info,
            "experience_years": experience_years,
            "recommendations": recommendations,
            "word_count": len(self.cv_text.split())
        }

# --- 5. Görselleştirme Fonksiyonları ---

def create_score_display(score: float) -> str:
    if score >= 85:
        color = "#4ade80"
        status = "Mükemmel"
        emoji = "🟢"
    elif score >= 70:
        color = "#fbbf24"
        status = "İyi"
        emoji = "🟡"
    elif score >= 50:
        color = "#60a5fa"
        status = "Orta"
        emoji = "🟠"
    else:
        color = "#f87171"
        status = "Zayıf"
        emoji = "🔴"
    
    progress_html = f"""
    <div style="text-align: center; margin: 20px 0; padding: 20px; background-color: #2d2d2d; border-radius: 12px; border: 1px solid #404040;">
        <div style="font-size: 48px; font-weight: bold; color: {color}; margin-bottom: 10px;">
            {score}%
        </div>
        <div style="font-size: 24px; margin-bottom: 20px; color: #ffffff;">
            {emoji} {status}
        </div>
        <div style="width: 100%; background-color: #1e1e1e; border-radius: 10px; overflow: hidden; height: 25px; border: 1px solid #404040;">
            <div style="width: {score}%; height: 100%; background: linear-gradient(90deg, {color}, {color}80); border-radius: 10px; transition: width 0.3s ease;"></div>
        </div>
    </div>
    """
    return progress_html

def create_category_bars(category_scores: Dict) -> str:
    html_parts = []
    for category, score in category_scores.items():
        if score >= 70:
            color = "#4ade80"
            emoji = "🟢"
        elif score >= 50:
            color = "#fbbf24"
            emoji = "🟡"
        else:
            color = "#f87171"
            emoji = "🔴"
        
        category_html = f"""
        <div style="margin: 15px 0; padding: 15px; border-radius: 8px; background-color: #2d2d2d; border: 1px solid #404040;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <span style="font-weight: bold; font-size: 14px; color: #ffffff;">{category}</span>
                <span style="font-weight: bold; color: {color};">{emoji} {score}%</span>
            </div>
            <div style="width: 100%; background-color: #1e1e1e; border-radius: 6px; overflow: hidden; height: 22px; border: 1px solid #404040;">
                <div style="width: {score}%; height: 100%; background: linear-gradient(90deg, {color}, {color}80); transition: width 0.5s ease;"></div>
            </div>
        </div>
        """
        html_parts.append(category_html)
    
    return '<div style="margin: 20px 0;">' + ''.join(html_parts) + '</div>'

# --- 6. Streamlit Ana Uygulama ---

def main():
    st.set_page_config(
        page_title="🎯 Gelişmiş ATS CV Puanlayıcı",
        page_icon="🎯",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    inject_dark_theme()
    
    st.title("🎯 Gelişmiş ATS CV Puanlayıcı")
    st.markdown("""
    <div style='background-color: #2d2d2d; padding: 20px; border-radius: 10px; margin-bottom: 20px; border: 1px solid #404040;'>
        <h4 style='color: #ffffff; margin-bottom: 10px;'>📋 Yazılım Test Mühendisliği Rollerine Özel CV Analizi</h4>
        <p style='color: #cccccc; margin: 0;'>CV'nizi ATS (Applicant Tracking Systems) sistemlerine hazırlayın, detaylı analiz ve öneriler alın!</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.sidebar:
        st.header("⚙️ Ayarlar")
        
        role = st.selectbox(
            "📌 Hedef Rolünüzü Seçin",
            list(CRITERIA.keys()),
            help="Başvurmak istediğiniz yazılım testi rolünü seçin"
        )
        
        role_info = {
            "Manual Tester": "🔍 Manuel test süreçlerinde uzman, test senaryoları yazan ve uygulayan pozisyon",
            "Test Automation Engineer": "🤖 Test otomasyonu araçları kullanarak otomatik testler geliştiren pozisyon",
            "Full Stack Automation Engineer": "🚀 UI, API, Database ve Performance testlerini kapsayan tam yığın test uzmanı"
        }
        st.info(role_info[role])
        
        uploaded_file = st.file_uploader(
            "📄 CV'nizi Yükleyin",
            type=["pdf", "docx"],
            help="PDF veya Word formatında CV yükleyebilirsiniz"
        )
        
        analyze_button = st.button("🚀 CV'yi Analiz Et", type="primary")
    
    if analyze_button:
        if not uploaded_file:
            st.warning("⚠️ Lütfen önce bir CV dosyası yükleyin.")
            st.stop()
        
        with st.spinner("🔄 CV analiz ediliyor..."):
            analyzer = CVAnalyzer()
            results = analyzer.analyze_cv(uploaded_file, role)
        
        if "error" in results:
            st.error(f"❌ {results['error']}")
            st.stop()
        
        # Analiz sonuçları
        st.markdown("## 📊 Analiz Sonuçları")
        
        # Skor gösterimi
        score_html = create_score_display(results["score_info"]["overall"])
        st.markdown(score_html, unsafe_allow_html=True)
        
        # Kategori bazlı performans
        st.markdown("### 📈 Kategori Bazlı Performans")
        category_html = create_category_bars(results["score_info"]["by_category"])
        st.markdown(category_html, unsafe_allow_html=True)
        
        # Metriklerin gösterimi
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-container">
                <div style="color: #ffffff; font-size: 24px; font-weight: bold;">{results["score_info"]["total_keywords"]}</div>
                <div style="color: #cccccc; font-size: 14px;">Toplam Anahtar Kelime</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-container">
                <div style="color: #4ade80; font-size: 24px; font-weight: bold;">{results["score_info"]["total_found"]}</div>
                <div style="color: #cccccc; font-size: 14px;">Eşleşen Kelime</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-container">
                <div style="color: #60a5fa; font-size: 24px; font-weight: bold;">{results['experience_years']} yıl</div>
                <div style="color: #cccccc; font-size: 14px;">Deneyim Yılı</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="metric-container">
                <div style="color: #fbbf24; font-size: 24px; font-weight: bold;">{results["word_count"]}</div>
                <div style="color: #cccccc; font-size: 14px;">Kelime Sayısı</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Öneriler
        st.markdown("## 💡 Kişiselleştirilmiş Öneriler")
        for i, recommendation in enumerate(results["recommendations"], 1):
            st.markdown(f"**{i}.** {recommendation}")
        
        # Detaylı kategori analizi
        st.markdown("## 🔍 Detaylı Kategori Analizi")
        for category, data in results["matched"].items():
            with st.expander(f"{category} - {data['percentage']}% ({data['count']} adet)"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**✅ Bulunan Kelimeler:**")
                    if data["found"]:
                        for keyword in data["found"]:
                            st.markdown(f"• {keyword}")
                    else:
                        st.markdown("_Bulunan kelime yok_")
                
                with col2:
                    st.markdown("**❌ Eksik Kelimeler:**")
                    if data["missing"]:
                        for keyword in data["missing"][:10]:
                            st.markdown(f"• {keyword}")
                        if len(data["missing"]) > 10:
                            st.markdown(f"... ve {len(data['missing']) - 10} kelime daha")
                    else:
                        st.markdown("_Eksik kelime yok_")
        
        # ATS İpuçları
        st.markdown("## 💼 ATS İpuçları")
        for category, tips in ATS_TIPS.items():
            with st.expander(f"{category} İpuçları"):
                for tip in tips:
                    st.markdown(f"• {tip}")
        
        # Rapor indirme
        st.markdown("## 📥 Rapor İndir")
        report_data = {
            "Role": role,
            "Score": results["score_info"]["overall"],
            "Analysis_Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Total_Keywords": results["score_info"]["total_keywords"],
            "Found_Keywords": results["score_info"]["total_found"],
            "Experience_Years": results["experience_years"],
            "Word_Count": results["word_count"],
            "Category_Scores": results["score_info"]["by_category"],
            "Recommendations": results["recommendations"]
        }
        
        report_json = json.dumps(report_data, indent=2, ensure_ascii=False)
        st.download_button(
            label="📊 JSON Raporu İndir",
            data=report_json,
            file_name=f"cv_analysis_{role.replace(' ', '_').lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
    
    else:
        # Kullanım kılavuzu
        st.markdown("""
        <div style='background-color: #2d2d2d; padding: 28px; border-radius: 10px; margin-top: 25px; border: 1px solid #404040;'>
            <h4 style='color: #ffffff; margin-bottom: 12px;'>Nasıl Kullanılır?</h4>
            <ul style="color: #cccccc; font-size: 16px; line-height: 1.7;">
                <li>Sol menüden başvurmak istediğiniz <b>rolü</b> seçin</li>
                <li>CV'nizi <b>PDF</b> veya <b>DOCX</b> formatında yükleyin</li>
                <li>"CV'yi Analiz Et" butonuna tıklayın</li>
                <li>Detaylı skor, kategori analizi ve önerileri inceleyin</li>
                <li>JSON formatında kişisel analiz raporunuzu indirin</li>
            </ul>
            <hr style="border: 1px solid #404040;">
            <b>✨ İpucu:</b> Skorunuzu yükseltmek için eksik olan anahtar kelimeleri ve önerileri dikkate alın!
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
