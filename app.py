import streamlit as st
import tempfile
import os
import docx2txt
import pdfplumber
import re
import json
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import pandas as pd
from typing import Dict, List, Tuple, Optional

# --- 1. Geliştirilmiş Kriter Matrisleri ---

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

# --- 2. Geliştirilmiş ATS Tavsiye Mesajları ---
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

# --- 3. Yardımcı Fonksiyonlar ---

class CVAnalyzer:
    def __init__(self):
        self.cv_text = ""
        self.analysis_results = {}
        
    def extract_text(self, file) -> str:
        """CV'den metin çıkarma"""
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
        """Metin ön işleme"""
        # Fazla boşlukları temizle
        text = re.sub(r'\s+', ' ', text)
        # Özel karakterleri temizle
        text = re.sub(r'[^\w\s\-\+\#\.]', ' ', text)
        return text.strip()

    def extract_experience_years(self, text: str) -> int:
        """Deneyim yılını çıkarma"""
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
        """Kriter eşleşmesi analizi"""
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
        """Detaylı skor hesaplama"""
        total_keywords = sum(len(v["found"]) + len(v["missing"]) for v in matched.values())
        total_found = sum(len(v["found"]) for v in matched.values())
        
        if total_keywords == 0:
            return {"overall": 0, "by_category": {}}
        
        # Kategori bazlı skorlar
        category_scores = {}
        for cat, results in matched.items():
            total_cat = len(results["found"]) + len(results["missing"])
            if total_cat > 0:
                category_scores[cat] = round((len(results["found"]) / total_cat) * 100, 1)
            else:
                category_scores[cat] = 0
        
        # Genel skor
        overall_score = round((total_found / total_keywords) * 100, 1)
        
        # Bonus puanlar
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
        """Kişiselleştirilmiş öneriler"""
        recommendations = []
        
        # Düşük skorlu kategoriler için öneriler
        low_categories = [cat for cat, score in score_info["by_category"].items() if score < 50]
        
        if low_categories:
            recommendations.append(f"🔴 Öncelikli geliştirme alanları: {', '.join(low_categories)}")
        
        # Rol bazlı öneriler
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
        
        # Genel öneriler
        if score_info["overall"] < 70:
            recommendations.append("📄 CV'nizde daha fazla teknik detay ve proje örneği ekleyin")
        
        recommendations.append("🎯 LinkedIn profilinizi ve sertifikalarınızı eklemeyi unutmayın")
        recommendations.append("📊 Proje sonuçlarınızı sayısal verilerle destekleyin")
        
        return recommendations

    def analyze_cv(self, file, role: str) -> Dict:
        """Ana analiz fonksiyonu"""
        # Metin çıkarma
        raw_text = self.extract_text(file)
        if not raw_text or len(raw_text) < 100:
            return {"error": "CV'den yeterli metin çıkarılamadı"}
        
        # Metin ön işleme
        self.cv_text = self.preprocess_text(raw_text)
        
        # Kriter eşleşmesi
        matched = self.match_criteria(self.cv_text, CRITERIA[role])
        
        # Skor hesaplama
        score_info = self.calculate_detailed_score(matched)
        
        # Deneyim yılı çıkarma
        experience_years = self.extract_experience_years(self.cv_text)
        
        # Öneriler
        recommendations = self.get_recommendations(role, matched, score_info)
        
        return {
            "matched": matched,
            "score_info": score_info,
            "experience_years": experience_years,
            "recommendations": recommendations,
            "word_count": len(self.cv_text.split())
        }

# --- 4. Görselleştirme Fonksiyonları ---

def create_score_gauge(score: float) -> go.Figure:
    """Skor göstergesi oluşturma"""
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "ATS Uyumluluk Skoru"},
        delta = {'reference': 70},
        gauge = {
            'axis': {'range': [None, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 50], 'color': "lightgray"},
                {'range': [50, 70], 'color': "yellow"},
                {'range': [70, 85], 'color': "lightgreen"},
                {'range': [85, 100], 'color': "green"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    
    fig.update_layout(height=300)
    return fig

def create_category_chart(category_scores: Dict) -> go.Figure:
    """Kategori bazlı skor grafiği"""
    categories = list(category_scores.keys())
    scores = list(category_scores.values())
    
    colors = ['#FF6B6B' if score < 50 else '#4ECDC4' if score < 70 else '#45B7D1' 
              for score in scores]
    
    fig = go.Figure(data=[
        go.Bar(
            x=categories,
            y=scores,
            marker_color=colors,
            text=[f'{score}%' for score in scores],
            textposition='auto',
        )
    ])
    
    fig.update_layout(
        title="Kategori Bazlı Performans",
        xaxis_title="Kategoriler",
        yaxis_title="Skor (%)",
        xaxis={'tickangle': 45},
        height=400
    )
    
    return fig

# --- 5. Streamlit Ana Uygulama ---

def main():
    st.set_page_config(
        page_title="🎯 Gelişmiş ATS CV Puanlayıcı",
        page_icon="🎯",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Ana başlık
    st.title("🎯 Gelişmiş ATS CV Puanlayıcı")
    st.markdown("""
    <div style='background-color: #f0f2f6; padding: 20px; border-radius: 10px; margin-bottom: 20px;'>
        <h4>📋 Yazılım Test Mühendisliği Rollerine Özel CV Analizi</h4>
        <p>CV'nizi ATS (Applicant Tracking Systems) sistemlerine hazırlayın, detaylı analiz ve öneriler alın!</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Ayarlar")
        
        # Rol seçimi
        role = st.selectbox(
            "📌 Hedef Rolünüzü Seçin",
            list(CRITERIA.keys()),
            help="Başvurmak istediğiniz yazılım testi rolünü seçin"
        )
        
        # Rol hakkında bilgi
        role_info = {
            "Manual Tester": "🔍 Manuel test süreçlerinde uzman, test senaryoları yazan ve uygulayan pozisyon",
            "Test Automation Engineer": "🤖 Test otomasyonu araçları kullanarak otomatik testler geliştiren pozisyon",
            "Full Stack Automation Engineer": "🚀 UI, API, Database ve Performance testlerini kapsayan tam yığın test uzmanı"
        }
        
        st.info(role_info[role])
        
        # Dosya yükleme
        uploaded_file = st.file_uploader(
            "📄 CV'nizi Yükleyin",
            type=["pdf", "docx"],
            help="PDF veya Word formatında CV yükleyebilirsiniz"
        )
        
        # Analiz butonu
        analyze_button = st.button("🚀 CV'yi Analiz Et", type="primary")
    
    # Ana içerik
    if analyze_button:
        if not uploaded_file:
            st.warning("⚠️ Lütfen önce bir CV dosyası yükleyin.")
            st.stop()
        
        # Analiz başlat
        with st.spinner("🔄 CV analiz ediliyor..."):
            analyzer = CVAnalyzer()
            results = analyzer.analyze_cv(uploaded_file, role)
        
        if "error" in results:
            st.error(f"❌ {results['error']}")
            st.stop()
        
        # Sonuçları görüntüle
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("## 📊 Analiz Sonuçları")
            
            # Skor göstergesi
            fig_gauge = create_score_gauge(results["score_info"]["overall"])
            st.plotly_chart(fig_gauge, use_container_width=True)
            
            # Kategori grafiği
            fig_category = create_category_chart(results["score_info"]["by_category"])
            st.plotly_chart(fig_category, use_container_width=True)
        
        with col2:
            st.markdown("## 📋 Özet Bilgiler")
            
            # Skor kartı
            score = results["score_info"]["overall"]
            if score >= 85:
                status = "🟢 Mükemmel"
                color = "success"
            elif score >= 70:
                status = "🟡 İyi"
                color = "warning"
            elif score >= 50:
                status = "🟠 Orta"
                color = "info"
            else:
                status = "🔴 Zayıf"
                color = "error"
            
            st.metric("ATS Skoru", f"{score}%", f"{status}")
            
            # Diğer metrikler
            st.metric("Toplam Anahtar Kelime", results["score_info"]["total_keywords"])
            st.metric("Eşleşen Kelime", results["score_info"]["total_found"])
            st.metric("Deneyim Yılı", f"{results['experience_years']} yıl")
            st.metric("Kelime Sayısı", results["word_count"])
        
        # Öneriler
        st.markdown("## 💡 Kişiselleştirilmiş Öneriler")
        
        for i, recommendation in enumerate(results["recommendations"], 1):
            st.markdown(f"**{i}.** {recommendation}")
        
        # Detaylı analiz
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
                        for keyword in data["missing"][:10]:  # İlk 10 eksik
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
        
        # Rapor hazırlama
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
        # Başlangıç sayfası
        st.markdown("## 🚀 Nasıl Kullanılır?")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            ### 1️⃣ Rol Seç
            Soldaki menüden hedef rolünüzü seçin:
            - Manual Tester
            - Test Automation Engineer  
            - Full Stack Automation Engineer
            """)
        
        with col2:
            st.markdown("""
            ### 2️⃣ CV Yükle
            PDF veya Word formatında CV'nizi yükleyin.
            En az 100 kelime içermeli.
            """)
        
        with col3:
            st.markdown("""
            ### 3️⃣ Analiz Et
            "CV'yi Analiz Et" butonuna tıklayın ve 
            detaylı raporunuzu alın.
            """)
        
        st.markdown("---")
        st.markdown("## 🎯 Özellikler")
        
        feature_cols = st.columns(2)
        
        with feature_cols[0]:
            st.markdown("""
            ### 📊 Detaylı Analiz
            - **Kategori bazlı skorlama**
            - **Anahtar kelime eşleşmesi**
            - **Deneyim yılı tespiti**
            - **Kelime sayısı analizi**
            """)
        
        with feature_cols[1]:
            st.markdown("""
            ### 💡 Akıllı Öneriler
            - **Kişiselleştirilmiş tavsiyeler**
            - **Eksik anahtar kelimeler**
            - **ATS optimizasyon ipuçları**
            - **Rol bazlı öneriler**
            """)

if __name__ == "__main__":
    main()
