import streamlit as st
import google.generativeai as genai
import json
import time
import requests  # Telegram bildirimi için şart

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

# --- TELEGRAM FUNCTION ---
def send_telegram_notification(sender_name):
    """Sends a push notification to your phone via Telegram."""
    try:
        # Secrets dosyasından bilgileri çekiyoruz
        bot_token = st.secrets["TELEGRAM_TOKEN"]
        chat_id = st.secrets["TELEGRAM_CHAT_ID"]
        
        message = f"🚨 İŞ FIRSATI (AI Asistan)! \n\nKimden: {sender_name}\n\nBir Recruiter seninle görüşmek için bildirim gönderdi."
        
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message
        }
        
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            return True
        else:
            # Hata detayını terminale yazdırır (Kullanıcı görmez)
            print(f"Telegram Hatası: {response.text}")
            return False
            
    except Exception as e:
        return False

# --- 3. YOUR DATA (ENGLISH) ---
user_data = {
    "identity": {
        "name": "Batuhan Alp Kurban",
        "title": "Software Engineer (5+ Years Experience)",
        "location": "Germany",
        "summary": "Proactive Python Developer with 5+ years of experience designing and maintaining distributed data systems, automated pipelines, and real-time integrations.",
        "contact_note": "You can reach out via LinkedIn or email at batuhanalpkurban@gmail.com."
    },
    "contact": {
        "linkedin": "https://linkedin.com/in/batuhanalpkurban",
        "github": "https://github.com/jrkurban",
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
            "highlights": "Developed asynchronous Python microservices (FastAPI) for AI analytics. Built REST/gRPC services for real-time pipelines. Migrated legacy services to microservices (30% reduced complexity)."
        },
        {
            "company": "Hometech",
            "role": "Software Engineer",
            "date": "Jan 2023 - Nov 2023",
            "highlights": "Built scalable APIs with FastAPI/Flask. Containerized services (Docker/K8s). Implemented Redis/RabbitMQ. Designed LLM-powered internal chatbot using RAG architecture."
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

# System Prompt
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

# --- MODEL SETUP ---
# Kullanıcının isteği üzerine 2.5 sürümü ayarlandı.
# Eğer API hata verirse "gemini-1.5-flash" veya "gemini-2.0-flash-exp" deneyin.
model = genai.GenerativeModel(
    model_name="gemini-2.5-flash", 
    system_instruction=system_prompt
)

# --- 4. SIDEBAR & CONTACT FORM ---
with st.sidebar:
    st.image("https://ui-avatars.com/api/?name=Batuhan+Alp&background=0D8ABC&color=fff&size=200", caption="Batuhan Alp Kurban")
    st.title("Batuhan Alp Kurban")
    st.caption("Software Engineer | Python & AI")
    
    st.markdown("---")

    # --- QUICK CONTACT FORM (TELEGRAM) ---
    with st.expander("📞 Contact Me Directly", expanded=True):
        st.write("Want to schedule an interview?")
        with st.form(key='contact_form'):
            sender_name = st.text_input("Your Name / Company:")
            submit_btn = st.form_submit_button(label="🚀 Notify Batuhan")
            
            if submit_btn:
                if sender_name:
                    if send_telegram_notification(sender_name):
                        st.success("Notification sent! Batuhan will get back to you shortly.")
                        st.balloons()
                    else:
                        st.error("Notification failed. Please verify Telegram settings.")
                else:
                    st.warning("Please enter your name.")

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
col1, col2, col3, col4 = st.columns(4)

if col1.button("Current Role"):
    st.session_state.messages.append({"role": "user", "parts": ["What is Batuhan doing at xDatum currently?"]})
    st.rerun()

if col2.button("AI & LLM Exp"):
    st.session_state.messages.append({"role": "user", "parts": ["Tell me about his experience with AI, LLMs, and RAG."]})
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
if prompt := st.chat_input("Ask a question about Batuhan..."):
    st.session_state.messages.append({"role": "user", "parts": [prompt]})
    st.rerun()

# --- GENERATION ENGINE ---
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    with st.chat_message("assistant", avatar="🤖"):
        message_placeholder = st.empty()
        try:
            chat = model.start_chat(history=st.session_state.messages[:-1])
            last_user_msg = st.session_state.messages[-1]["parts"][0]
            
            # Stream true yaparak daktilo efekti veriyoruz
            response = chat.send_message(last_user_msg, stream=True)

            full_response = ""
            for chunk in response:
                if chunk.text:
                    full_response += chunk.text
                    message_placeholder.markdown(full_response + "▌")
                    time.sleep(0.01)

            message_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "model", "parts": [full_response]})

        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")
