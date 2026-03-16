import streamlit as st
from openai import OpenAI
import asyncio
import edge_tts
import os
from streamlit_mic_recorder import mic_recorder

# --- БАПТАУЛАР ---
# API кілтін Streamlit Cloud Secrets-тен қауіпсіз түрде аламыз
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception:
    st.error("Қате: OpenAI API кілті Secrets бөлімінде табылмады! Streamlit Settings -> Secrets бөліміне кілтті қосыңыз.")

REPLY_AUDIO = "reply.mp3"
VIDEO_FILE = 'kydyr_ata.mp4'

st.set_page_config(page_title="Наурыз AI - Қыдыр ата", layout="centered")

# --- ИНТЕРФЕЙС ---
st.title("🌙 Қыдыр атамен сұхбат")
st.write("Ұлыстың ұлы күні құтты болсын! Төмендегі батырманы басып, Қыдыр атаға сұрақ қойыңыз немесе бата сұраңыз.")

# Видеоны көрсету (Аутоплей және циклмен)
if os.path.exists(VIDEO_FILE):
    st.video(VIDEO_FILE, format="video/mp4", autoplay=True, loop=True)
else:
    st.warning(f"Видео файлы табылмады: {VIDEO_FILE}. Файлды GitHub-қа дәл осы атпен жүктегеніңізге көз жеткізіңіз.")

# --- ФУНКЦИЯЛАР ---
async def generate_voice(text):
    """Microsoft Edge арқылы қазақша дауыс жасау"""
    voice = "kk-KZ-DauletNeural"
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(REPLY_AUDIO)

# --- МИКРОФОН ЖӘНЕ ЛОГИКА ---
st.write("---")
# Сөйлеуді жазу батырмасы
audio_input = mic_recorder(
    start_prompt="🎤 Сөйлеуді бастау", 
    stop_prompt="🛑 Тоқтату", 
    key='recorder'
)

if audio_input:
    # 1. Дауысты уақытша файлға сақтау
    with open("temp_audio.wav", "wb") as f:
        f.write(audio_input['bytes'])
    
    with st.spinner("Қыдыр ата сізді тыңдап, ойланып жатыр..."):
        try:
            # 2. Whisper арқылы дауысты мәтінге айналдыру
            with open("temp_audio.wav", "rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=audio_file
                )
                user_text = transcript.text
                st.info(f"🗨 **Сіз:** {user_text}")

            # 3. GPT-4 арқылы Қыдыр атаның жауабын алу
            completion = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Сен Наурыз мерекесінде қонақтарға бата беретін ақылды Қыдыр атасың. Қазақ тілінде қысқа (2-3 сөйлем), даналыққа толы жауап бер немесе бата бер."},
                    {"role": "user", "content": user_text}
                ]
            )
            ai_reply = completion.choices[0].message.content
            st.success(f"👴 **Қыдыр ата:** {ai_reply}")

            # 4. Edge-TTS арқылы қазақша дыбыстау
            if os.path.exists(REPLY_AUDIO):
                try:
                    os.remove(REPLY_AUDIO)
                except:
                    pass
            
            asyncio.run(generate_voice(ai_reply))
            
            # 5. Аудионы ойнату
            if os.path.exists(REPLY_AUDIO):
                st.audio(REPLY_AUDIO, format='audio/mp3', autoplay=True)
                
        except Exception as e:
            st.error(f"Қате орын алды: {e}")
