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

# Экран баптаулары
st.set_page_config(page_title="Қыдыр ата AI", layout="wide", initial_sidebar_state="collapsed")

# --- FULLSCREEN CSS ---
st.markdown(f"""
    <style>
    /* Streamlit-тің стандартты элементтерін жасыру */
    #MainMenu, footer, header {{visibility: hidden;}}
    .stApp {{
        background-color: black;
    }}
    
    /* Видеоны бүкіл экранға жаю */
    .fullscreen-bg {{
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        overflow: hidden;
        z-index: -1;
    }}
    .fullscreen-bg video {{
        width: 100%;
        height: 100%;
        object-fit: cover; /* Видеоны экранға толық толтыру */
    }}

    /* Микрофон контейнері */
    .mic-overlay {{
        position: fixed;
        bottom: 10%;
        left: 50%;
        transform: translateX(-50%);
        z-index: 100;
        text-align: center;
    }}

    /* Жауап мәтінінің стилі (Видео үстіндегі субтитр сияқты) */
    .response-box {{
        position: fixed;
        top: 10%;
        left: 50%;
        transform: translateX(-50%);
        width: 80%;
        background: rgba(0, 0, 0, 0.6);
        color: white;
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        font-size: 24px;
        z-index: 99;
        border: 1px solid gold;
    }}
    </style>
    
    <div class="fullscreen-bg">
        <video autoplay loop muted playsinline>
            <source src="data:video/mp4;base64,{base64.b64encode(open(VIDEO_FILE, 'rb').read()).decode()}" type="video/mp4">
        </video>
    </div>
    """, unsafe_allow_html=True)

# --- ЛОГИКА ---
async def generate_voice(text):
    voice = "kk-KZ-DauletNeural"
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(REPLY_AUDIO)

# Микрофонды экранның ортасына шығару
st.markdown('<div class="mic-overlay">', unsafe_allow_html=True)
audio_input = mic_recorder(
    start_prompt="🎤 Атадан бата сұрау", 
    stop_prompt="🛑 Тоқтату", 
    key='recorder'
)
st.markdown('</div>', unsafe_allow_html=True)

if audio_input:
    with open("temp_audio.wav", "wb") as f:
        f.write(audio_input['bytes'])
    
    try:
        with open("temp_audio.wav", "rb") as audio_file:
            transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_file)
            user_text = transcript.text

        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": "Сен Қыдыр атасың. Даналықпен, өте қысқа қазақша бата бер."},
                      {"role": "user", "content": user_text}]
        )
        ai_reply = completion.choices[0].message.content
        
        # Жауапты экранның жоғарғы жағына шығару
        st.markdown(f'<div class="response-box">{ai_reply}</div>', unsafe_allow_html=True)

        # Дыбыс жасау және жасырын ойнату
        asyncio.run(generate_voice(ai_reply))
        if os.path.exists(REPLY_AUDIO):
            audio_base64 = base64.b64encode(open(REPLY_AUDIO, "rb").read()).decode()
            st.markdown(f'<audio src="data:audio/mp3;base64,{audio_base64}" autoplay></audio>', unsafe_allow_html=True)
                
    except Exception as e:
        st.error(f"Қате: {e}")
