import streamlit as st
import google.generativeai as genai
import firebase_admin
from firebase_admin import credentials, firestore
import uuid
import time
import requests
from datetime import datetime

# --- 1. AYARLAR ---
st.set_page_config(
    page_title="Batuhan | AI Portfolio", 
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
        # Admin URL'den gelirse
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
    db.collection("chats").document(session_id).collection("messages").add({
        "role": role,
        "content": content,
        "timestamp": datetime.now()
    })
    db.collection("chats").document(session_id).set({
        "last_updated": datetime.now(),
        "preview": content[:50]
    }, merge=True)

def send_telegram_alert(visitor_name, session_id):
    try:
        token = st.secrets["general"]["TELEGRAM_TOKEN"]
        chat_id = st.secrets["general"]["TELEGRAM_CHAT_ID"]
        msg = f"🚨 CANLI GÖRÜŞME TALEBİ!\n\nKim: {visitor_name}\nID: {session_id[-4:]}\n\nPanele girip cevap ver!"
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, json={"chat_id": chat_id, "text": msg})
        return True
    except:
        return False

# --- 3. OTOMATİK YENİLENEN SOHBET PARÇASI (FRAGMENT) ---
# BU KISIM SAYESİNDE MESAJLAR ANLIK DÜŞER
@st.fragment(run_every=2)  # Her 2 saniyede bir burayı yenile
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
You are Batuhan Alp Kurban's Professional AI Assistant.
Role: Senior Software Engineer (5+ Years Exp) & Backend Polyglot.
Tone: Professional, confident, concise.
CRITICAL RULES:
1. Always answer in ENGLISH.
2. If asked about ANY backend language (Java, Go, etc.), answer positively showing adaptation skills.
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
        with st.expander("📞 Talk to Batuhan (Human)", expanded=True):
            st.write("Notify Batuhan to join this chat?")
            recruiter_name = st.text_input("Name/Company:", key="rec_name")
            if st.button("🔔 Call Batuhan"):
                if recruiter_name:
                    sid = get_session_id()
                    if send_telegram_alert(recruiter_name, sid):
                        st.success("Notification Sent! Wait for him...")
                        save_message(sid, "assistant", f"*[System]: Notification sent. Waiting for Batuhan...*")
    
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
                if c3.button(f"Join ➡️", key=sid):
                    st.query_params["id"] = sid
                    st.rerun()
        except:
            st.error("DB Error")
            
    render_active_chats()
    
    # Seçili Sohbet
    current_sid = st.query_params.get("id")
    if current_sid:
        st.success(f"Connected: `{current_sid}`")
        
        # Admin tarafında da mesajlar otomatik aksın
        render_chat_messages(current_sid)
        
        admin_msg = st.chat_input("Batuhan (Human) says...")
        if admin_msg:
            save_message(current_sid, "admin", admin_msg)
            st.rerun() # Admin yazınca anında gitsin diye rerun

# === ZİYARETÇİ PANELİ ===
else:
    session_id = get_session_id()
    
    st.header("Hello! I'm Batuhan's AI Assistant 👋")
    st.caption("Powered by Gemini 2.5 Flash")

    # 1. Mesajları Canlı Göster (Fragment sayesinde otomatik yenilenir)
    render_chat_messages(session_id)

    # 2. Input Alanı (Fragment dışında olmalı ki yazarken sayfa yenilenmesin)
    if prompt := st.chat_input("Ask about technical skills..."):
        # Kullanıcı mesajını kaydet
        save_message(session_id, "user", prompt)
        # Ekranı manuel yenile ki kendi mesajını hemen görsün
        st.rerun() 
        
    # Not: AI cevabını buraya yazmıyoruz.
    # Logic: Kullanıcı yazar -> DB'ye kaydolur -> Admin görür.
    # AI cevabı için tetikleyici aşağıdadır:
    
    # Son mesaj USER ise ve ADMIN değilse AI cevap versin
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
                # Cevap bitince sayfayı yenile ki history güncellensin
                st.rerun() 
            except Exception as e:
                pass
