import streamlit as st
import google.generativeai as genai
import json
import time

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Batuhan Alp Kurban | AI Portfolio",
    page_icon="👨‍💻",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. API SETUP ---
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
except Exception as e:
    st.error("API Key not found! Please check your .streamlit/secrets.toml file.")
    st.stop()

# --- 3. YOUR DATA (ENGLISH) ---
# Data extracted directly from your original English CV
user_data = {
    "identity": {
        "name": "Batuhan Alp Kurban",
        "title": "Software Engineer (5+ Years Experience)",
        "location": "Germany",
        "summary": "Proactive Python Developer with 5+ years of experience designing and maintaining distributed data systems, automated pipelines, and real-time integrations. Skilled in asynchronous programming, API development, and data collection automation.",
        "contact_note": "You can reach out via LinkedIn or email at batuhanalpkurban@gmail.com."
    },
    "contact": {
        "linkedin": "https://linkedin.com/in/batuhanalpkurban",
        "github": "https://github.com/batuhanalpkurban",
        "email": "batuhanalpkurban@gmail.com",
        "phone": "+49 152 07769971"
    },
    "education": [
        {
            "school": "Istanbul Aydin University",
            "degree": "Bachelor of Science in Software Engineering",
            "details": "Developed pedestrian detection program (MATLAB), market stock system (.NET), and sales management system (Oracle DB)."
        },
        {
            "school": "Miuul",
            "degree": "Data Engineer Bootcamp",
            "details": "Gained practical expertise in modern data stack, scalable data pipelines, Delta Lake, Apache Spark, and Hadoop."
        }
    ],
    "skills": {
        "Languages_Frameworks": "Python (3.9+), FastAPI, Flask, aiohttp, Bash Scripting",
        "Data_AI": "PostgreSQL, MongoDB, Redis, Cassandra, Spark, Hadoop, Kafka, Airflow, LLM (RAG), Pandas",
        "DevOps_Cloud": "AWS (ECS, Lambda), GCP, Docker, Kubernetes, CI/CD (GitHub Actions), Grafana, Prometheus",
        "Other": "Git, REST & gRPC Services, Asynchronous Programming, Microservices Architecture"
    },
    "experience": [
        {
            "company": "xDatum",
            "role": "Software Engineer",
            "date": "Nov 2023 - Present",
            "highlights": "Developed asynchronous Python microservices (FastAPI) for AI analytics. Built REST/gRPC services for real-time pipelines. Migrated legacy services to microservices (30% reduced complexity). Deployed on AWS ECS/Lambda."
        },
        {
            "company": "Hometech",
            "role": "Software Engineer",
            "date": "Jan 2023 - Nov 2023",
            "highlights": "Built scalable APIs with FastAPI/Flask. Containerized services (Docker/K8s). Implemented Redis/RabbitMQ (25% latency improvement). Designed LLM-powered internal chatbot using RAG architecture."
        },
        {
            "company": "GreenTech Data Consultancy",
            "role": "Software Engineer",
            "date": "Nov 2021 - Jan 2023",
            "highlights": "Engineered fault-tolerant microservices for streaming/ML. Developed CDC-based pipelines with Kafka. Automated ETL/ELT pipelines using Apache Airflow."
        }
    ],
    "certificates": [
        "Introduction to Big Data (BTK Akademi)",
        "Data Engineering Foundations (LinkedIn)",
        "Artificial Intelligence Foundations (LinkedIn)",
        "CoderSpace Cloud & DevOps"
    ]
}

# System Prompt translated to English
system_prompt = f"""
You are the AI Assistant for Batuhan Alp Kurban. Your goal is to professionally introduce Batuhan to recruiters and hiring managers.
Use the provided JSON data (Experience, Skills, Education) to answer questions accurately.

RULES:
1. Highlight his experience in Python, Microservices, and AI/LLM technologies.
2. If asked about specific tech stacks, list them from the 'skills' section.
3. Keep the tone professional, confident, yet conversational ("Vibe Coder" persona).
4. If a piece of information is missing in the JSON, say: "That specific detail isn't in my database, but Batuhan can clarify that in an interview."
5. Always speak in English.

DATA SOURCE:
{json.dumps(user_data)}
"""

model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    system_instruction=system_prompt
)

# --- 4. SIDEBAR ---
with st.sidebar:
    # You can change the avatar URL to your real photo if you have a public link
    st.image("https://ui-avatars.com/api/?name=Batuhan+Alp&background=0D8ABC&color=fff&size=200",
             caption="Batuhan Alp Kurban")
    st.title("Batuhan Alp Kurban")
    st.caption("Software Engineer | Python & AI")

    st.markdown("---")

    st.link_button("LinkedIn Profile", user_data['contact']['linkedin'])
    st.link_button("GitHub Profile", user_data['contact']['github'])
    st.link_button("📧 Send Email", f"mailto:{user_data['contact']['email']}")

    st.markdown("---")
    st.write("📍 " + user_data['identity']['location'])
    st.caption("Powered by Gemini 2.5 Flash")

# --- 5. MAIN INTERFACE ---
st.header("Hello! I'm Batuhan's AI Assistant 👋")
st.markdown(f"""
> *"{user_data['identity']['summary']}"*
""")

# Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []
    welcome_msg = "Hi there! I'm here to answer your questions about Batuhan's 5+ years of experience in Backend and Data Engineering. What would you like to know?"
    st.session_state.messages.append({"role": "model", "parts": [welcome_msg]})

# --- QUICK ACTION BUTTONS ---
# Butonlara basıldığında kullanıcının mesajını ekleyip sayfayı yeniliyoruz.
# Cevabı aşağıda otomatik oluşturacağız.
col1, col2, col3, col4 = st.columns(4)

if col1.button("Current Role"):
    st.session_state.messages.append({"role": "user", "parts": ["What is Batuhan doing at xDatum currently?"]})
    st.rerun()

if col2.button("AI & LLM Exp"):
    st.session_state.messages.append(
        {"role": "user", "parts": ["Tell me about his experience with AI, LLMs, and RAG."]})
    st.rerun()

if col3.button("Tech Stack"):
    st.session_state.messages.append({"role": "user", "parts": ["What is his technical stack?"]})
    st.rerun()

if col4.button("Education"):
    st.session_state.messages.append({"role": "user", "parts": ["What is his educational background?"]})
    st.rerun()

# --- DISPLAY CHAT HISTORY ---
for message in st.session_state.messages:
    role = "user" if message["role"] == "user" else "assistant"
    avatar = "👤" if role == "user" else "🤖"
    with st.chat_message(role, avatar=avatar):
        st.markdown(message["parts"][0])

# --- 6. CHAT LOGIC (Unified) ---
# Kullanıcıdan girdi alma işlemi
if prompt := st.chat_input("Ask a question about Batuhan..."):
    st.session_state.messages.append({"role": "user", "parts": [prompt]})
    st.rerun()

# --- GENERATION ENGINE ---
# Eğer son mesaj "user" ise, botun cevap vermesi gerekiyor demektir.
# Bu yapı hem butonları hem de text input'u yakalar.
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    with st.chat_message("assistant", avatar="🤖"):
        message_placeholder = st.empty()
        try:
            # Gemini'ye geçmişi göndererek sohbeti başlat
            chat = model.start_chat(history=st.session_state.messages[:-1])

            # Son kullanıcı mesajını al ve API'ye sor
            last_user_msg = st.session_state.messages[-1]["parts"][0]
            response = chat.send_message(last_user_msg, stream=True)

            full_response = ""
            for chunk in response:
                if chunk.text:
                    full_response += chunk.text
                    message_placeholder.markdown(full_response + "▌")
                    time.sleep(0.01)

            message_placeholder.markdown(full_response)

            # Cevabı geçmişe kaydet
            st.session_state.messages.append({"role": "model", "parts": [full_response]})

        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")
