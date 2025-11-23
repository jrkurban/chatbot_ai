import streamlit as st
import google.generativeai as genai
import time

# --- SAYFA AYARLARI ---
st.set_page_config(
    page_title="Batuhan AI | Dijital Asistan",
    page_icon="👨‍💻",
    layout="centered"
)

# --- API AYARLARI ---
# Güvenlik Notu: API anahtarını kodun içine direkt yazmak yerine
# Streamlit Secrets kullanacağız. Aşağıda detayını anlattım.
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
except Exception as e:
    st.error("API Key bulunamadı. Lütfen ..streamlit/secrets.toml dosyasını kontrol et.")
    st.stop()

# --- SENİN VERİTABANIN (BEYİN) ---
# Burayı kendi gerçek bilgilerinle doldurmalısın.
# Ne kadar detay verirsen, asistan o kadar iyi konuşur.
MY_DATA = """
İsim: Batuhan
Rol: Senior Backend Developer (5 Yıl Deneyim)
Lokasyon: İstanbul / Uzaktan çalışabilir
Teknolojiler: Python (Django, FastAPI), Go, Docker, Kubernetes, AWS, PostgreSQL.
Öne Çıkan Proje 1: E-ticaret Altyapısı. Mikroservis mimarisiyle saniyede 10k istek karşılayan sistem kurdu. (github.com/batuhan/ecommerce)
Öne Çıkan Proje 2: AI Chatbot Entegrasyonu. RAG mimarisi kullanarak şirket içi doküman asistanı yazdı.
Hobiler: No Man's Sky oynamak, yeni teknolojileri kurcalamak.
Kişilik: Profesyonel, çözüm odaklı ama samimi. Kısa ve net cevaplar vermeyi sever.
Özel Talimat: Eğer kullanıcı "görüşmek istiyorum", "mülakat", "işe alım" gibi şeyler derse, onlara Batuhan'a hemen bildirim gönderdiğini söyle ve mail adresini (batuhan@mail.com) ver.
"""

# --- MODEL AYARLARI ---
# System Instruction: Modele kim olduğunu öğretiyoruz.
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=f"Sen Batuhan'ın yapay zeka asistanısın. Amacın işe alım uzmanlarına Batuhan'ı tanıtmak. Aşağıdaki bilgilere dayanarak cevap ver. Bilmediğin bir şey sorulursa dürüstçe 'Bu konuda bilgim yok ama Batuhan'a sorabilirim' de. Asla kendi başına bilgi uydurma. \n\nVeri: {MY_DATA}"
)

# --- ARAYÜZ TASARIMI ---
st.title("Merhaba, ben Batuhan'ın AI Asistanı 👋")
st.markdown("""
> *"Projelerimi incelemek için Github linklerine tıklayabilir veya bana doğrudan soru sorabilirsiniz."*
""")

# Sohbet Geçmişini Başlat
if "messages" not in st.session_state:
    st.session_state.messages = []
    # İlk karşılama mesajı
    st.session_state.messages.append({"role": "model", "parts": [
        "Selam! Batuhan şu an kod yazıyor olabilir. Onun hakkında ne bilmek istersin? Projeleri, tecrübesi veya kullandığı teknolojiler?"]})

# Mesajları Ekrana Bas
for message in st.session_state.messages:
    role = "user" if message["role"] == "user" else "assistant"
    with st.chat_message(role):
        st.markdown(message["parts"][0])

# --- KULLANICI GİRDİSİ VE CEVAP ---
if prompt := st.chat_input("Sorunuzu buraya yazın..."):
    # Kullanıcı mesajını ekle
    st.session_state.messages.append({"role": "user", "parts": [prompt]})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Asistan cevabını oluştur
    with st.chat_message("assistant"):
        message_placeholder = st.empty()

        try:
            # Gemini'ye sohbet geçmişini göndererek bağlamı koruyoruz
            chat = model.start_chat(history=st.session_state.messages[:-1])
            response = chat.send_message(prompt, stream=True)

            full_response = ""
            for chunk in response:
                if chunk.text:
                    full_response += chunk.text
                    # Daktilo efekti için ufak gecikme (Vibe için önemli)
                    message_placeholder.markdown(full_response + "▌")
                    time.sleep(0.01)

            message_placeholder.markdown(full_response)

            # Cevabı geçmişe kaydet
            st.session_state.messages.append({"role": "model", "parts": [full_response]})

        except Exception as e:
            st.error(f"Bir hata oluştu: {str(e)}")