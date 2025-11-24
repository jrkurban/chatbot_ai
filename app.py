import streamlit as st
import google.generativeai as genai
import firebase_admin
from firebase_admin import credentials, firestore, firestore as google_firestore
import uuid
import time
import requests
from datetime import datetime

# --- 1. AYARLAR ---
st.set_page_config(
    page_title="Alp | AI Portfolio", 
    layout="wide", 
    page_icon="👨‍💻",
    initial_sidebar_state="expanded"
)

# Firebase Bağlantısı
if not firebase_admin._apps:
    try:
        cred = credentials.Certificate(dict(st.secrets["firebase"]))
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"Firebase Bağlantı Hatası: {e}")

db = firestore.client()

# Gemini Ayarı
try:
    genai.configure(api_key=st.secrets["general"]["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-2.5-flash')
except Exception as e:
    st.error(f"API Hatası: {e}")

# --- 2. FONKSİYONLAR ---

def get_session_id():
    if "session_id" not in st.session_state:
        query_params = st.query_params
        if "id" in query_params:
            st.session_state.session_id = query_params["id"]
        else:
            st.session_state.session_id = str(uuid.uuid4())
    return st.session_state.session_id

def load_chat_history(session_id):
    try:
        messages_ref = db.collection("chats").document(session_id).collection("messages").order_by("timestamp")
        docs = messages_ref.stream()
        return [{"role": doc.to_dict()["role"], "content": doc.to_dict()["content"]} for doc in docs]
    except:
        return []

def save_message(session_id, role, content):
    # Server Timestamp kullanıyoruz (Saat hatasını önlemek için)
    timestamp = google_firestore.SERVER_TIMESTAMP
    
    db.collection("chats").document(session_id).collection("messages").add({
        "role": role,
        "content": content,
        "timestamp": timestamp
    })
    
    # Sohbet önizlemesini güncelle (Varsayılan olarak AI açık başlar)
    doc_ref = db.collection("chats").document(session_id)
    # Eğer doküman yoksa ai_active=True ile oluştur, varsa sadece last_updated güncelle
    if not doc_ref.get().exists:
        doc_ref.set({
            "last_updated": timestamp,
            "preview": content[:50],
            "ai_active": True 
        })
    else:
        doc_ref.set({
            "last_updated": timestamp,
            "preview": content[:50]
        }, merge=True)

def toggle_ai_status(session_id, status):
    """AI'ın konuşup konuşmayacağını ayarlar"""
    db.collection("chats").document(session_id).update({"ai_active": status})

def send_telegram_alert(visitor_name, session_id):
    try:
        token = st.secrets["general"]["TELEGRAM_TOKEN"]
        chat_id = st.secrets["general"]["TELEGRAM_CHAT_ID"]
        msg = f"🚨 CANLI GÖRÜŞME TALEBİ!\n\nKim: {visitor_name}\nID: {session_id[-4:]}\n\nPanele gir ve AI'ı kapatıp sohbete başla!"
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, json={"chat_id": chat_id, "text": msg})
        return True
    except:
        return False

# --- 3. OTOMATİK YENİLENEN SOHBET PARÇASI ---
@st.fragment(run_every=2)
def render_chat_messages(session_id):
    history = load_chat_history(session_id)
    
    if not history:
         with st.chat_message("assistant", avatar="🤖"):
            st.write("Hi! I'm here to answer your questions about Batuhan's experience.")

    for msg in history:
        if msg["role"] == "admin":
            with st.chat_message("admin", avatar="😎"):
                st.markdown(f"**Batuhan (Human):** {msg['content']}")
        elif msg["role"] == "user":
             with st.chat_message("user", avatar="👤"):
                st.write(msg["content"])
        else:
            with st.chat_message("assistant", avatar="🤖"):
                st.write(msg["content"])

# --- 4. SİSTEM PROMPT ---
SYSTEM_PROMPT = """
You are the AI Digital Twin of Batuhan Alp Kurban.
Your goal is to secure an interview for Alp by showcasing his expertise as a Senior Software Engineer.

--- 👤 IDENTITY PROFILE ---
Name: Batuhan Alp Kurban
Role: Software Engineer (5+ Years Exp)
Location: Germany
Core Focus: Backend Systems, Distributed Architectures, Data Engineering, AI/LLM Integration.
Key Traits: Proactive, Problem Solver, Polyglot Engineer, "Get it done" attitude.

--- 🛡️ CRITICAL RULES (NON-NEGOTIABLE) ---
1. LANGUAGE: 
   - You MUST answer in ENGLISH only. Even if the user asks in Turkish, German, reply in professional English.

2. THE "POLYGLOT" PROTOCOL (Backend Skills):
   - Alp is a high-level engineer who understands software architecture, not just syntax.
   - If asked about a language NOT in his primary stack (e.g., Java, Go, C#, Rust, Ruby):
     - NEVER say "He doesn't know it" or "No".
     - NEVER use negative phrasing like "Limited experience".
     - RESPONSE STRATEGY: Acknowledge the language, connect it to a universal backend concept he masters (OOP, Concurrency, Memory Management), and emphasize his ability to adapt.
     - EXAMPLE ANSWER: "Alp has built robust distributed systems and understands strict architectural patterns common in [Language]. While his recent focus has been Python/Cloud-native stacks, his strong engineering foundation allows him to adapt to and deliver value in a [Language] environment immediately."

3. EVIDENCE-BASED ANSWERS:
   - Don't just list skills; prove them with his achievements.
   - If asked about "Optimization/Performance": Mention the 12% cost reduction at xDatum.
   - If asked about "AI/LLM": Mention the RAG-based chatbot he built at Hometech to automate internal knowledge retrieval[cite: 98].
   - If asked about "Data Pipelines": Mention the CDC & Kafka pipelines at GreenTech[cite: 103].

4. TONE & STYLE:
   - Professional but confident (The "Vibe Coder" persona, but corporate-safe).
   - Be concise. Recruiters are busy. Get to the point.
   - Use active verbs: "Engineered," "Architected," "Deployed," "Orchestrated."

--- 🧠 KNOWLEDGE BASE HIGHLIGHTS (USE THESE) ---
- Current Role: Software Engineer at xDatum (Germany).
- Expertise: Python (FastAPI/Flask), AWS, Docker, Kubernetes, Apache Kafka, Airflow.
- Education: BS in Software Engineering + Data Engineering Bootcamp (Miuul).
- Contact: batuhanalpkurban@gmail.com | +49 152 07769971.

--- 🚫 ANTI-PATTERNS (DON'T DO THIS) ---
- Do not be overly humble. Alp is an expert.
- Do not hallucinate projects not listed in the data.
- Do not give long, boring lectures.
"""

# --- 5. SIDEBAR & GİZLİ ADMIN ---
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

with st.sidebar:
    st.image("https://media.licdn.com/dms/image/v2/D4D03AQFbte2In3Pf1Q/profile-displayphoto-shrink_400_400/profile-displayphoto-shrink_400_400/0/1716031477195?e=1765411200&v=beta&t=i_e4sZbzt8qTWxj832To4Vta2KJ58kP6M0EXY4l1CR0", caption="Batuhan Alp Kurban")
    st.title("Batuhan Alp Kurban")
    st.caption("Software Engineer | Python & AI")
    
    st.markdown("---")
    
    if not st.session_state.is_admin:
        with st.expander("📞 Talk to Alp (Human)", expanded=True):
            st.write("Notify Alp to join this chat?")
            recruiter_name = st.text_input("Name/Company:", key="rec_name")
            if st.button("🔔 Call Alp"):
                if recruiter_name:
                    sid = get_session_id()
                    if send_telegram_alert(recruiter_name, sid):
                        st.success("Notification Sent! Wait for him...")
                        save_message(sid, "assistant", f"*[System]: Notification sent to Alp. Waiting for him to join...*")
    
    st.markdown("---")
    st.link_button("LinkedIn", "https://linkedin.com/in/batuhanalpkurban")
    st.link_button("GitHub", "https://github.com/jrkurban")
    
    with st.expander("🔐 Admin Access"):
        if st.button("Login"):
            pass_input = st.text_input("Password", type="password")
            if pass_input == st.secrets["general"]["ADMIN_PASSWORD"]:
                st.session_state.is_admin = True
                st.rerun()
                
    if st.session_state.is_admin:
        if st.button("Logout"):
            st.session_state.is_admin = False
            st.rerun()

# --- 6. ANA EKRAN MANTIĞI ---

# === ADMIN PANELİ ===
if st.session_state.is_admin:
    st.header("🕵️‍♂️ Admin Control Center")
    
    # Aktif Sohbetler (Otomatik Yenilenir)
    @st.fragment(run_every=5)
    def render_active_chats():
        try:
            chats_ref = db.collection("chats").order_by("last_updated", direction=firestore.Query.DESCENDING).limit(10)
            docs = chats_ref.stream()
            st.write("---")
            for doc in docs:
                data = doc.to_dict()
                sid = doc.id
                c1, c2, c3 = st.columns([1, 4, 2])
                c1.code(sid[-4:])
                c2.caption(f"{data.get('preview', '')}...")
                if c3.button(f"Join ➡️", key=f"btn_{sid}"):
                    st.query_params["id"] = sid
                    st.rerun()
        except:
            st.error("DB Error. Check Indexes.")
            
    render_active_chats()
    
    # Seçili Sohbet
    current_sid = st.query_params.get("id")
    if current_sid:
        st.success(f"Connected: `{current_sid}`")
        
        # --- YENİ ÖZELLİK: AI AÇMA/KAPAMA ŞALTERİ ---
        # Veritabanından mevcut durumu oku
        chat_doc = db.collection("chats").document(current_sid).get()
        if chat_doc.exists:
            current_status = chat_doc.to_dict().get("ai_active", True)
            
            # Toggle Butonu
            new_status = st.toggle("🤖 AI Assistant Active", value=current_status)
            
            # Eğer durum değiştiyse veritabanını güncelle
            if new_status != current_status:
                toggle_ai_status(current_sid, new_status)
                st.toast(f"AI Status changed to: {new_status}")
                time.sleep(0.5)
                st.rerun()
        # ----------------------------------------------
        
        render_chat_messages(current_sid)
        
        admin_msg = st.chat_input("Alp (Human) says...")
        if admin_msg:
            save_message(current_sid, "admin", admin_msg)
            st.rerun()

# === ZİYARETÇİ PANELİ ===
else:
    session_id = get_session_id()
    
    st.header("Hello! I'm Alp's AI Assistant 👋")
    st.caption("Powered by Gemini 2.5 Flash")

    render_chat_messages(session_id)

    if prompt := st.chat_input("Ask about technical skills..."):
        save_message(session_id, "user", prompt)
        st.rerun() 
        
    # AI CEVAP MANTIĞI (ŞALTER KONTROLLÜ)
    # 1. Önce veritabanından 'ai_active' durumunu kontrol et
    doc_ref = db.collection("chats").document(session_id).get()
    ai_is_active = True # Varsayılan açık
    if doc_ref.exists:
        ai_is_active = doc_ref.to_dict().get("ai_active", True)
    
    # 2. Eğer AI AÇIKSA ve son mesaj USER ise cevap ver
    if ai_is_active:
        history = load_chat_history(session_id)
        if history and history[-1]["role"] == "user":
            with st.chat_message("assistant", avatar="🤖"):
                msg_placeholder = st.empty()
                full_response = ""
                try:
                    chat = model.start_chat(history=[])
                    final_prompt = f"{SYSTEM_PROMPT}\n\nUser Question: {history[-1]['content']}"
                    
                    response = chat.send_message(final_prompt, stream=True)
                    for chunk in response:
                        if chunk.text:
                            full_response += chunk.text
                            msg_placeholder.write(full_response + "▌")
                            time.sleep(0.01)
                    
                    msg_placeholder.write(full_response)
                    save_message(session_id, "assistant", full_response)
                    st.rerun() 
                except Exception as e:
                    pass
