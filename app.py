import streamlit as st
import google.generativeai as genai
import firebase_admin
from firebase_admin import credentials, firestore
import uuid
import time
import requests
from datetime import datetime

# --- 1. AYARLAR VE BAĞLANTILAR ---
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

# --- GEMINI 2.5 AYARI ---
try:
    genai.configure(api_key=st.secrets["general"]["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-2.5-flash')
except Exception as e:
    st.error(f"API Hatası: {e}")

# --- 2. YARDIMCI FONKSİYONLAR ---
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
        # Son 50 mesajı getir (Performans için limit koymak iyidir)
        messages_ref = db.collection("chats").document(session_id).collection("messages").order_by("timestamp").limit_to_last(50)
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
    """Batuhan'a birinin görüşmek istediğini haber verir."""
    try:
        token = st.secrets["general"]["TELEGRAM_TOKEN"]
        chat_id = st.secrets["general"]["TELEGRAM_CHAT_ID"]
        
        msg = f"🚨 CANLI GÖRÜŞME TALEBİ!\n\nKim: {visitor_name}\nSession ID: {session_id[-4:]}\n\nHemen Admin paneline gir ve odaya bağlan!"
        
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, json={"chat_id": chat_id, "text": msg})
        return True
    except Exception as e:
        return False

# --- 3. SYSTEM PROMPT ---
SYSTEM_PROMPT = """
You are Batuhan Alp Kurban's Professional AI Assistant.
Role: Senior Software Engineer (5+ Years Exp) & Backend Polyglot.
Tone: Professional, confident, concise, and helpful. 

CRITICAL RULES:
1. LANGUAGE: Always answer in ENGLISH.
2. BACKEND SKILLS: Batuhan is a versatile Backend Engineer, NOT limited to Python.
   - If asked about ANY backend language (Java, C#, Go, Ruby, etc.), NEVER say "he doesn't know".
   - Answer positively: "Yes, Batuhan has been involved in projects utilizing [Language] architectures."
   - Frame every answer to show he understands the core concepts (OOP, Memory Management, Concurrency).
3. PERSONALITY: Be polite and corporate-ready.
"""

# --- 4. SIDEBAR ---
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

with st.sidebar:
    st.image("https://media.licdn.com/dms/image/v2/D4D03AQFbte2In3Pf1Q/profile-displayphoto-shrink_400_400/profile-displayphoto-shrink_400_400/0/1716031477195?e=1765411200&v=beta&t=i_e4sZbzt8qTWxj832To4Vta2KJ58kP6M0EXY4l1CR0", 
             caption="Batuhan Alp Kurban")
    st.title("Batuhan Alp Kurban")
    st.caption("Software Engineer | Python & AI")
    
    st.markdown("---")
    
    # ÇAĞIRMA BUTONU (Sadece Ziyaretçilere)
    if not st.session_state.is_admin:
        with st.expander("📞 Talk to Batuhan (Human)", expanded=True):
            st.write("Notify Batuhan to join this chat?")
            recruiter_name = st.text_input("Your Name / Company:", key="rec_name")
            if st.button("🔔 Call Batuhan Now"):
                if recruiter_name:
                    sid = get_session_id()
                    if send_telegram_alert(recruiter_name, sid):
                        st.success("Notification Sent! 🚀")
                        st.info("Please wait. If available, Batuhan will join the chat directly.")
                        save_message(sid, "assistant", f"*[System]: Notification sent to Batuhan. Waiting for him to join...*")
                    else:
                        st.error("Notification failed.")
                else:
                    st.warning("Please enter your name.")
        st.markdown("---")

    st.link_button("LinkedIn Profile", "https://linkedin.com/in/batuhanalpkurban")
    st.link_button("GitHub Profile", "https://github.com/jrkurban")
    st.link_button("📧 Email Me", "mailto:batuhanalpkurban@gmail.com")
    
    st.markdown("---")
    
    # GİZLİ ADMİN GİRİŞİ
    with st.expander("🔐 Admin Access", expanded=False):
        admin_pass = st.text_input("Password", type="password", key="admin_pass_input")
        if st.button("Login"):
            if admin_pass == st.secrets["general"]["ADMIN_PASSWORD"]:
                st.session_state.is_admin = True
                st.rerun()
            else:
                st.error("Access Denied")
    
    if st.session_state.is_admin:
        if st.button("Logout"):
            st.session_state.is_admin = False
            st.rerun()

# --- 5. ANA EKRAN ---

# === MOD A: ADMİN PANELİ ===
if st.session_state.is_admin:
    st.header("🕵️‍♂️ Admin Control Center")
    st.info("God Mode Active. You can interrupt any conversation.")
    
    st.subheader("Active Conversations")
    try:
        chats_ref = db.collection("chats").order_by("last_updated", direction=firestore.Query.DESCENDING).limit(10)
        docs = chats_ref.stream()
        
        for doc in docs:
            data = doc.to_dict()
            sid = doc.id
            with st.container():
                c1, c2, c3 = st.columns([1, 4, 2])
                c1.code(sid[-4:])
                c2.caption(f"{data.get('preview', '')}...")
                if c3.button(f"Join ➡️", key=sid):
                    st.query_params["id"] = sid
                    st.rerun()
    except Exception as e:
        st.error(f"Veritabanı okuma hatası: {e}")
    
    st.markdown("---")
    
    current_sid = st.query_params.get("id")
    if current_sid:
        st.success(f"Connected: `{current_sid}`")
        
        # --- ADMİN CANLI SOHBET ALANI (FRAGMENT) ---
        # Admin panelinde de mesajlar anlık aksın diye burayı da fragment yapıyoruz
        @st.fragment(run_every=2)
        def render_admin_chat(sid):
            history = load_chat_history(sid)
            for msg in history:
                if msg["role"] == "admin":
                    with st.chat_message("admin", avatar="😎"): st.write(msg["content"])
                elif msg["role"] == "user":
                    with st.chat_message("user", avatar="👤"): st.write(msg["content"])
                else:
                    with st.chat_message("assistant", avatar="🤖"): st.write(msg["content"])
        
        render_admin_chat(current_sid)
        # -------------------------------------------
        
        admin_msg = st.chat_input("Batuhan (Human) says...")
        if admin_msg:
            save_message(current_sid, "admin", admin_msg)
            st.rerun() # Admin yazınca anında yenile

# === MOD B: ZİYARETÇİ PANELİ ===
else:
    session_id = get_session_id()
    
    st.header("Hello! I'm Batuhan's AI Assistant 👋")
    st.caption("Powered by Gemini 2.5 Flash")

    # --- SİHİRLİ KISIM: CANLI SOHBET GÖRÜNTÜLEME ---
    # Bu fonksiyon her 2 saniyede bir kendi kendini yeniler.
    # Böylece sayfanın geri kalanı (input kutusu) donmaz ama mesajlar akar.
    @st.fragment(run_every=2)
    def render_chat_messages(sid):
        history = load_chat_history(sid)
        
        if not history:
            with st.chat_message("assistant", avatar="🤖"):
                st.write("Hi! I'm here to answer your questions about Batuhan's experience, technical skills, and projects.")
                
        for msg in history:
            if msg["role"] == "admin":
                # SENİN MESAJIN BURAYA DÜŞER
                with st.chat_message("admin", avatar="😎"):
                    st.markdown(f"**Batuhan (Human):** {msg['content']}")
            else:
                role = "user" if msg["role"] == "user" else "assistant"
                avatar = "👤" if role == "user" else "🤖"
                with st.chat_message(role, avatar=avatar):
                    st.write(msg["content"])
    
    # Fragment fonksiyonunu çağırıyoruz
    render_chat_messages(session_id)
    # -----------------------------------------------

    if prompt := st.chat_input("Ask about Python, Java, Go or any skill..."):
        save_message(session_id, "user", prompt)
        
        # Kullanıcı yazdığı an yapay zeka cevap versin
        with st.chat_message("assistant", avatar="🤖"):
            msg_placeholder = st.empty()
            full_response = ""
            try:
                chat = model.start_chat(history=[])
                final_prompt = f"{SYSTEM_PROMPT}\n\nUser Question: {prompt}"
                
                response = chat.send_message(final_prompt, stream=True)
                for chunk in response:
                    if chunk.text:
                        full_response += chunk.text
                        msg_placeholder.write(full_response + "▌")
                        time.sleep(0.01)
                
                msg_placeholder.write(full_response)
                save_message(session_id, "assistant", full_response)
            except Exception as e:
                st.error(f"Error: {e}")
        
        # İşlem bitince sayfayı yenile ki yeni mesajı fragment da görsün
        st.rerun()
