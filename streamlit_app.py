import streamlit as st
from openai import OpenAI
import asyncio
import edge_tts
import os
import base64
from streamlit_mic_recorder import mic_recorder

# --- БАПТАУЛАР ---
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
REPLY_AUDIO = "reply.mp3"
VIDEO_FILE = 'kydyr_ata.mp4'

st.set_page_config(page_title="Қыдыр ата", layout="centered")

# --- СТИЛЬ (CSS) ---
# Батырманы видеоға жақындату және дизайнды әдемілеу
st.markdown("""
    <style>
    .stVideo {
        border-radius: 20px;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.3);
    }
    div[data-testid="stVerticalBlock"] > div:nth-child(3) {
        position: relative;
        text-align: center;
        margin-top: -100px; /* Батырманы видеоның үстіне қарай жылжыту */
        z-index: 10;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🌙 Қыдыр атамен сұхбат")

# 1. ВИДЕО (Дыбыссыз)
if os.path.exists(VIDEO_FILE):
    # muted=True - дыбысты өшіреді
    st.video(VIDEO_FILE, format="video/mp4", autoplay=True, loop=True, muted=True)
else:
    st.error("Видео файлы табылмады!")

# 2. МИКРОФОН (Видеоның астында немесе үстінде тұрады)
st.write("###") # Аздап бос орын
audio_input = mic_recorder(
    start_prompt="🎤 Қыдыр атадан бата сұрау", 
    stop_prompt="🛑 Тоқтату", 
    key='recorder'
)

# --- ЛОГИКА ---
async def generate_voice(text):
    voice = "kk-KZ-DauletNeural"
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(REPLY_AUDIO)

if audio_input:
    with open("temp_audio.wav", "wb") as f:
        f.write(audio_input['bytes'])
    
    with st.spinner("Қыдыр ата ойланып жатыр..."):
        try:
            with open("temp_audio.wav", "rb") as audio_file:
                transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_file)
                user_text = transcript.text
                st.chat_message("user").write(user_text)

            completion = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": "Сен Қыдыр атасың. Қысқа қазақша бата бер."},
                          {"role": "user", "content": user_text}]
            )
            ai_reply = completion.choices[0].message.content
            st.chat_message("assistant").write(ai_reply)

            # Дыбыс жасау
            asyncio.run(generate_voice(ai_reply))
            
            # 3. АУДИОНЫ ЖАСЫРЫН ОЙНАТУ (HTML арқылы)
            if os.path.exists(REPLY_AUDIO):
                audio_file = open(REPLY_AUDIO, "rb")
                audio_bytes = audio_file.read()
                audio_base64 = base64.b64encode(audio_bytes).decode()
                audio_html = f'<audio src="data:audio/mp3;base64,{audio_base64}" autoplay="autoplay"></audio>'
                st.markdown(audio_html, unsafe_allow_html=True)
                
        except Exception as e:
            st.error(f"Қате: {e}")
