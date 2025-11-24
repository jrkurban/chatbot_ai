import streamlit as st
import google.generativeai as genai
import firebase_admin
from firebase_admin import credentials, firestore
import uuid
import time
from datetime import datetime

# --- 1. AYARLAR VE BAĞLANTILAR ---
st.set_page_config(
    page_title="Batuhan | AI Portfolio", 
    layout="wide", 
    page_icon="⚡",
    initial_sidebar_state="expanded"
)

# Firebase Bağlantısı (Singleton Pattern)
if not firebase_admin._apps:
    # Secrets içindeki firebase bilgisini dict'e çeviriyoruz
    cred = credentials.Certificate(dict(st.secrets["firebase"]))
    firebase_admin.initialize_app(cred)

db = firestore.client()

# --- GEMINI 2.5 AYARI (ANLAŞTIĞIMIZ GİBİ) ---
try:
    genai.configure(api_key=st.secrets["general"]["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-2.5-flash')
except Exception as e:
    st.error(f"Model Hatası: {e}")

# --- 2. FONKSİYONLAR ---
def get_session_id():
    """Her ziyaretçiye benzersiz bir ID verir."""
    if "session_id" not in st.session_state:
        # Admin, URL'den ?id=... ile gelirse o ID'yi al
        query_params = st.query_params
        if "id" in query_params:
            st.session_state.session_id = query_params["id"]
        else:
            st.session_state.session_id = str(uuid.uuid4())
    return st.session_state.session_id

def load_chat_history(session_id):
    """Firestore'dan mesajları çeker."""
    try:
        messages_ref = db.collection("chats").document(session_id).collection("messages").order_by("timestamp")
        docs = messages_ref.stream()
        return [{"role": doc.to_dict()["role"], "content": doc.to_dict()["content"]} for doc in docs]
    except:
        return []

def save_message(session_id, role, content):
    """Mesajı veritabanına kaydeder."""
    db.collection("chats").document(session_id).collection("messages").add({
        "role": role,
        "content": content,
        "timestamp": datetime.now()
    })
    # Son güncellenme zamanını ana dokümana işle (Admin listesi için)
    db.collection("chats").document(session_id).set({
        "last_updated": datetime.now(),
        "preview": content[:50]
    }, merge=True)

# --- 3. SİSTEM PROMPT ---
SYSTEM_PROMPT = """
You are Batuhan Alp Kurban's AI Assistant.
Role: Senior Software Engineer (5+ Years Exp).
Tone: Professional, confident, yet conversational ("Vibe Coder").
Goal: Impress recruiters with Batuhan's skills in Python, AI, and Microservices.
Rules:
1. Always speak English.
2. Be concise.
"""

# --- 4. GİZLİ ADMİN MANTIĞI ---
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

# --- SIDEBAR TASARIMI ---
with st.sidebar:
    # Profil Kısmı
    st.image("https://media.licdn.com/dms/image/v2/D4D03AQFbte2In3Pf1Q/profile-displayphoto-shrink_400_400/profile-displayphoto-shrink_400_400/0/1716031477195?e=1765411200&v=beta&t=i_e4sZbzt8qTWxj832To4Vta2KJ58kP6M0EXY4l1CR0", 
             caption="Batuhan Alp Kurban")
    st.title("Batuhan Alp Kurban")
    st.caption("Software Engineer | Python & AI")
    
    st.markdown("---")
    
    # İletişim Butonları
    contact = st.secrets["general"] # Linkleri buradan veya manuel alabilirsin
    # Basitlik için hardcode linkler (kendi linklerinle güncelle):
    st.link_button("LinkedIn Profile", "https://linkedin.com/in/batuhanalpkurban")
    st.link_button("GitHub Profile", "https://github.com/jrkurban")
    st.link_button("📧 Email Me", "mailto:batuhanalpkurban@gmail.com")
    
    st.markdown("---")
    
    # --- GİZLİ ADMİN GİRİŞİ (EN ALTTA, SAKLI) ---
    # Sadece küçük bir kilit ikonu veya yazı ile gizliyoruz
    with st.expander("🔐 Admin Access", expanded=False):
        admin_pass = st.text_input("Password", type="password", key="admin_pass_input")
        if st.button("Login"):
            if admin_pass == st.secrets["general"]["ADMIN_PASSWORD"]:
                st.session_state.is_admin = True
                st.success("Welcome Batuhan!")
                st.rerun()
            else:
                st.error("Access Denied")
    
    # Eğer Admin ise Çıkış Butonu göster
    if st.session_state.is_admin:
        if st.button("Logout"):
            st.session_state.is_admin = False
            st.rerun()

# --- 5. ANA EKRAN MANTIĞI ---

# === MOD A: ADMİN PANELİ (SEN GİRDİĞİNDE) ===
if st.session_state.is_admin:
    st.header("🕵️‍♂️ Admin Control Center")
    st.info("You are in 'God Mode'. You can see active chats and intervene.")
    
    # Aktif Sohbetleri Listele
    st.subheader("Active Conversations")
    chats_ref = db.collection("chats").order_by("last_updated", direction=firestore.Query.DESCENDING).limit(10)
    docs = chats_ref.stream()
    
    # Tablo Başlıkları
    c1, c2, c3 = st.columns([1, 4, 2])
    c1.markdown("**ID**")
    c2.markdown("**Last Message**")
    c3.markdown("**Action**")
    
    for doc in docs:
        data = doc.to_dict()
        sid = doc.id
        with st.container():
            col1, col2, col3 = st.columns([1, 4, 2])
            col1.code(sid[-4:]) # ID'nin son 4 hanesi
            col2.caption(f"{data.get('preview', '')}...")
            
            # Odaya Gir Butonu
            if col3.button(f"Join Chat ➡️", key=sid):
                st.query_params["id"] = sid
                st.rerun()
    
    st.markdown("---")
    
    # Seçili Odayı Yönetme
    current_sid = st.query_params.get("id")
    if current_sid:
        st.success(f"Connected to Session: `{current_sid}`")
        
        # Canlı Yenileme Butonu
        if st.button("🔄 Refresh Chat"):
            st.rerun()
            
        # Sohbet Geçmişini Göster
        history = load_chat_history(current_sid)
        for msg in history:
            if msg["role"] == "admin":
                with st.chat_message("admin", avatar="😎"):
                    st.write(msg["content"])
            elif msg["role"] == "user":
                with st.chat_message("user", avatar="👤"):
                    st.write(msg["content"])
            else:
                with st.chat_message("assistant", avatar="🤖"):
                    st.write(msg["content"])
        
        # Admin Cevabı (Intervention)
        admin_msg = st.chat_input("Write as Batuhan (Interrupt AI)...")
        if admin_msg:
            save_message(current_sid, "admin", admin_msg)
            st.rerun()

# === MOD B: ZİYARETÇİ PANELİ (HERKES GİRDİĞİNDE) ===
else:
    session_id = get_session_id()
    
    st.header("Hello! I'm Batuhan's AI Assistant 👋")
    st.caption("Powered by Gemini 2.5 Flash")

    # Geçmişi Yükle
    history = load_chat_history(session_id)
    
    if not history:
        # İlk açılış mesajı (DB'ye kaydetmiyoruz, sadece gösteriyoruz)
        with st.chat_message("assistant", avatar="🤖"):
            st.write("Hi! Ask me anything about Batuhan's experience, or specific tech stack details.")

    # Mesajları Ekrana Bas
    for msg in history:
        if msg["role"] == "admin":
            # Admin mesajı gelirse özel vurgu (Vibe Coder Effect)
            with st.chat_message("admin", avatar="😎"):
                st.markdown(f"**Batuhan (Human):** {msg['content']}")
        else:
            role = "user" if msg["role"] == "user" else "assistant"
            avatar = "👤" if role == "user" else "🤖"
            with st.chat_message(role, avatar=avatar):
                st.write(msg["content"])

    # Kullanıcı Girdisi
    if prompt := st.chat_input("Ask a question..."):
        # 1. Kullanıcı mesajını kaydet
        save_message(session_id, "user", prompt)
        with st.chat_message("user", avatar="👤"):
            st.write(prompt)
            
        # 2. AI Cevabı
        with st.chat_message("assistant", avatar="🤖"):
            msg_placeholder = st.empty()
            full_response = ""
            
            # Gemini Çağrısı
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
                # AI cevabını DB'ye kaydet
                save_message(session_id, "assistant", full_response)
            except Exception as e:
                st.error(f"Error: {e}")
