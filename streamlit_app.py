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
# Батырманы видеоның үстіне дәл ортаға немесе төменірек қою
st.markdown("""
    <style>
    /* Видео контейнері */
    .video-container {
        position: relative;
        width: 100%;
        max-width: 500px;
        margin: auto;
    }
    
    /* Видеоның астындағы бос орындарды алу */
    iframe, video {
        border-radius: 15px;
    }

    /* Микрофон батырмасын қозғалту */
    /* Streamlit-тің mic_recorder элементін нысанаға аламыз */
    div[data-testid="stVerticalBlock"] > div:nth-child(2) {
        position: absolute;
        bottom: 15%; /* Видеоның төменгі жағынан биіктігі */
        left: 50%;
        transform: translateX(-50%);
        z-index: 99;
    }
    
    /* Батырманың стилін өзгерту (опционально) */
    button {
        background-color: #ff4b4b !important;
        color: white !important;
        border-radius: 50px !important;
        padding: 10px 25px !important;
        border: 2px solid white !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- ИНТЕРФЕЙС ---
st.title("🌙 Қыдыр атамен сұхбат")

# 1. ВИДЕО (Дыбыссыз фон)
if os.path.exists(VIDEO_FILE):
    st.video(VIDEO_FILE, format="video/mp4", autoplay=True, loop=True, muted=True)
else:
    st.error("Видео файлы табылмады!")

# 2. МИКРОФОН (CSS арқылы жоғары жылжытылған)
audio_input = mic_recorder(
    start_prompt="🎤 Атаға сұрақ қою", 
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
    
    with st.spinner("Қыдыр ата тыңдап тұр..."):
        try:
            with open("temp_audio.wav", "rb") as audio_file:
                transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_file)
                user_text = transcript.text
                st.chat_message("user").write(user_text)

            completion = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": "Сен Қыдыр атасың. Даналықпен, өте қысқа қазақша бата бер."},
                          {"role": "user", "content": user_text}]
            )
            ai_reply = completion.choices[0].message.content
            st.chat_message("assistant").write(ai_reply)

            # Дыбыс жасау
            asyncio.run(generate_voice(ai_reply))
            
            # 3. АУДИОНЫ ЖАСЫРЫН ОЙНАТУ
            if os.path.exists(REPLY_AUDIO):
                audio_file = open(REPLY_AUDIO, "rb")
                audio_bytes = audio_file.read()
                audio_base64 = base64.b64encode(audio_bytes).decode()
                audio_html = f'<audio src="data:audio/mp3;base64,{audio_base64}" autoplay="autoplay"></audio>'
                st.markdown(audio_html, unsafe_allow_html=True)
                
        except Exception as e:
            st.error(f"Қате: {e}")
