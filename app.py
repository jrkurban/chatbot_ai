import streamlit as st
import google.generativeai as genai
import firebase_admin
from firebase_admin import credentials, firestore
import uuid
import time
from datetime import datetime

# --- 1. AYARLAR VE BAĞLANTILAR ---
st.set_page_config(page_title="Batuhan | AI & Live Chat", layout="wide", page_icon="⚡")

# Firebase Bağlantısı (Singleton Pattern - Sadece 1 kere bağlanır)
if not firebase_admin._apps:
    cred = credentials.Certificate(dict(st.secrets["firebase"]))
    firebase_admin.initialize_app(cred)

db = firestore.client()

# Gemini Ayarı
genai.configure(api_key=st.secrets["general"]["GOOGLE_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

# --- 2. FONKSİYONLAR ---

def get_session_id():
    """Her ziyaretçiye benzersiz bir ID verir."""
    if "session_id" not in st.session_state:
        # URL'den session alma (Admin belirli bir session'a girmek isterse)
        query_params = st.query_params
        if "id" in query_params:
            st.session_state.session_id = query_params["id"]
        else:
            st.session_state.session_id = str(uuid.uuid4())
    return st.session_state.session_id

def load_chat_history(session_id):
    """Firestore'dan mesajları çeker."""
    messages_ref = db.collection("chats").document(session_id).collection("messages").order_by("timestamp")
    docs = messages_ref.stream()
    return [{"role": doc.to_dict()["role"], "content": doc.to_dict()["content"]} for doc in docs]

def save_message(session_id, role, content):
    """Mesajı veritabanına kaydeder."""
    db.collection("chats").document(session_id).collection("messages").add({
        "role": role,
        "content": content,
        "timestamp": datetime.now()
    })
    # Son güncellenme zamanını ana dokümana işle (Admin listesinde sıralamak için)
    db.collection("chats").document(session_id).set({
        "last_updated": datetime.now(),
        "preview": content[:50]
    }, merge=True)

# --- 3. SİSTEM PROMPT (BATUHAN KİMLİĞİ) ---
SYSTEM_PROMPT = """
Sen Batuhan Alp Kurban'ın AI asistanısın.
5+ yıllık Yazılım Mühendisisin. Python, Backend ve AI uzmanısın.
Kısa, net ve profesyonel cevap ver.
Eğer teknik detay sorulursa (FastAPI, AWS vs) bilgini konuştur.
"""

# --- 4. ARAYÜZ MANTIĞI ---

# Sidebar'da Admin Girişi
with st.sidebar:
    st.title("⚡ Vibe Coder Mode")
    mode = st.radio("Mod Seç", ["Recruiter (Ziyaretçi)", "Admin (Batuhan)"])
    
    if mode == "Admin (Batuhan)":
        password = st.text_input("Admin Şifresi", type="password")
        if password == st.secrets["general"]["ADMIN_PASSWORD"]:
            st.success("Giriş Başarılı! Panele Geçiliyor...")
            is_admin = True
        else:
            st.warning("Şifre Yanlış")
            is_admin = False
    else:
        is_admin = False

# === SENARYO A: ADMİN PANELİ (SENİN EKRANIN) ===
if is_admin:
    st.header("🕵️‍♂️ Admin Kontrol Merkezi")
    
    # 1. Aktif Sohbetleri Listele
    st.subheader("Aktif Görüşmeler")
    chats_ref = db.collection("chats").order_by("last_updated", direction=firestore.Query.DESCENDING).limit(10)
    docs = chats_ref.stream()
    
    cols = st.columns([1, 3, 2])
    cols[0].write("**ID (Son 4 hane)**")
    cols[1].write("**Son Mesaj**")
    cols[2].write("**İşlem**")
    
    selected_session = None
    
    for doc in docs:
        data = doc.to_dict()
        sid = doc.id
        with st.container():
            c1, c2, c3 = st.columns([1, 3, 2])
            c1.write(f"`..{sid[-4:]}`")
            c2.write(f"_{data.get('preview', '')}_")
            if c3.button(f"Odaya Gir ➡️", key=sid):
                st.query_params["id"] = sid
                st.rerun()

    st.markdown("---")
    
    # Seçili bir odaya girdiyse odayı göster
    current_sid = st.query_params.get("id")
    if current_sid:
        st.info(f"Şu an bağlısın: `{current_sid}`")
        
        # Mesajları Canlı Göster (Basit Polling ile)
        if st.button("🔄 Yenile"):
            st.rerun()
            
        history = load_chat_history(current_sid)
        for msg in history:
            avatar = "👤" if msg["role"] == "user" else "🤖"
            if msg["role"] == "admin": avatar = "😎"
            
            with st.chat_message(msg["role"], avatar=avatar):
                st.write(msg["content"])
        
        # Admin Olarak Cevap Yaz
        admin_input = st.chat_input("Batuhan olarak cevap ver...")
        if admin_input:
            save_message(current_sid, "admin", admin_input)
            st.rerun()

# === SENARYO B: ZİYARETÇİ PANELİ (RECRUITER EKRANI) ===
else:
    session_id = get_session_id()
    
    st.title("Batuhan Alp Kurban | AI Chat")
    st.caption("Ben Batuhan'ın AI asistanıyım. Bazen Batuhan'ın kendisi de sohbete dahil olabilir! 😉")

    # Geçmişi yükle
    history = load_chat_history(session_id)
    
    # Ekrana Bas
    for msg in history:
        # Admin mesajı gelirse özel vurgu yap
        if msg["role"] == "admin":
            with st.chat_message("admin", avatar="😎"):
                st.markdown(f"**Batuhan (Human):** {msg['content']}")
        else:
            role = "user" if msg["role"] == "user" else "assistant"
            avatar = "👤" if role == "user" else "🤖"
            with st.chat_message(role, avatar=avatar):
                st.write(msg["content"])

    # Kullanıcı Girdisi
    if prompt := st.chat_input("Bir soru sorun..."):
        # 1. Kullanıcı mesajını kaydet ve göster
        save_message(session_id, "user", prompt)
        with st.chat_message("user", avatar="👤"):
            st.write(prompt)
            
        # 2. AI Cevabı (Sadece son mesaj admin'den DEĞİLSE cevap ver)
        # Buradaki mantık: Sen araya girdiysen AI sussun istersen buraya bir 'ai_active' kontrolü eklenebilir.
        # Şimdilik AI her zaman cevap veriyor, sen üstüne yazıyorsun.
        
        with st.chat_message("assistant", avatar="🤖"):
            msg_placeholder = st.empty()
            full_response = ""
            
            # Bağlam oluştur
            chat = model.start_chat(history=[])
            # Sistem promptunu ekle
            final_prompt = f"{SYSTEM_PROMPT}\n\nUser: {prompt}"
            
            response = chat.send_message(final_prompt, stream=True)
            for chunk in response:
                if chunk.text:
                    full_response += chunk.text
                    msg_placeholder.write(full_response + "▌")
                    time.sleep(0.01)
            
            msg_placeholder.write(full_response)
            save_message(session_id, "assistant", full_response)
            
        # Sayfayı yenilemeye gerek yok, stream zaten yazdı.
        # Ama veritabanı senkronu için arka planda işliyor.
