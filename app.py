import streamlit as st
import google.generativeai as genai
import json
import time
import requests # <--- BU SATIRI EKLEMEYİ UNUTMA

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Batuhan Alp Kurban | AI Portfolio",
    page_icon="👨‍💻",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. API SETUP (Google & Telegram) ---
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
except Exception as e:
    st.error("API Key not found!")
    st.stop()

# --- TELEGRAM FONKSİYONU ---
def send_telegram_notification(message):
    try:
        token = st.secrets["TELEGRAM_TOKEN"]
        chat_id = st.secrets["TELEGRAM_CHAT_ID"]
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message
        }
        requests.post(url, json=payload)
        return True
    except Exception as e:
        return False

# --- 3. YOUR DATA ---
user_data = {
    "identity": {
        "name": "Batuhan Alp Kurban",
        "title": "Software Engineer (5+ Years Experience)",
        "location": "Germany",
        "summary": "Proactive Python Developer with 5+ years of experience designing and maintaining distributed data systems.",
        "contact_note": "Reach out via LinkedIn or email."
    },
    "contact": {
        "linkedin": "https://linkedin.com/in/batuhanalpkurban",
        "github": "https://github.com/batuhanalpkurban", 
        "email": "batuhanalpkurban@gmail.com",
    },
     # ... Diğer verilerin aynı kalabilir ...
}

# System Prompt... (Aynı kalacak)
system_prompt = f"""
You are the AI Assistant for Batuhan Alp Kurban.
DATA SOURCE: {json.dumps(user_data)}
"""
model = genai.GenerativeModel(model_name="gemini-2.5-flash", system_instruction=system_prompt)

# --- 4. SIDEBAR & CONTACT BUTTON ---
with st.sidebar:
    st.image("https://ui-avatars.com/api/?name=Batuhan+Alp&background=0D8ABC&color=fff&size=200", caption="Batuhan Alp Kurban")
    st.title("Batuhan Alp Kurban")
    st.caption("Software Engineer | Python & AI")
    
    st.markdown("---")
    
    # --- BURASI YENİ: CANLI İLETİŞİM BUTONU ---
    st.markdown("### 📞 Quick Contact")
    # Form kullanarak butona basıldığında sayfanın en başına atmasını engelliyoruz
    with st.form(key='contact_form'):
        st.write("Want to hire me? Click below to notify Batuhan instantly.")
        contact_msg = st.text_input("Your Name / Company (Optional):")
        submit_button = st.form_submit_button(label="🚀 Send Instant Notification")
        
        if submit_button:
            sender_info = contact_msg if contact_msg else "Anonymous Recruiter"
            notification_text = f"🚨 DİKKAT BATUHAN! \n\nBir işe alım uzmanı seninle görüşmek istiyor!\n\nKimden: {sender_info}\nLinke bak: https://share.streamlit.io"
            
            if send_telegram_notification(notification_text):
                st.success("Notification sent to Batuhan's phone! He will get back to you.")
            else:
                st.error("Could not send notification. Please use Email.")
    
    st.markdown("---")
    
    st.link_button("LinkedIn Profile", user_data['contact']['linkedin'])
    st.link_button("GitHub Profile", user_data['contact']['github'])
    st.link_button("📧 Send Email", f"mailto:{user_data['contact']['email']}")
    
    st.caption("Powered by Gemini 2.5 Flash")

# --- 5. MAIN INTERFACE ---
# ... (Kodun geri kalanı aynı) ...
# Quick Actions ve Chat Logic kısmı buraya gelecek
# Önceki cevaptaki rewrite kısmını buraya yapıştırabilirsin.
