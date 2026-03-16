import streamlit as st
from openai import OpenAI
import asyncio
import edge_tts
import os
from streamlit_mic_recorder import mic_recorder

# --- БАПТАУЛАР ---
# API кілтін Streamlit Cloud Secrets-тен қауіпсіз түрде аламыз
try:
    client = OpenAI(api_key=st.secrets["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"])
except Exception:
    st.error("Қате: OpenAI API кілті Secrets бөлімінде табылмады!")

REPLY_AUDIO = "reply.mp3"
VIDEO_PATH = 'kydyr_ata.mp4'

st.set_page_config(page_title="Наурыз AI - Қыдыр ата", layout="centered")

# --- ИНТЕРФЕЙС ---
st.title("🌙 Қыдыр атамен сұхбат")
st.write("Ұлыстың ұлы күні құтты болсын! Төмендегі батырманы басып, Қыдыр атаға сұрақ қойыңыз.")

# Видеоны көрсету (Аутоплей және циклмен)
if os.path.exists(VIDEO_PATH):
    st.video(video_path, format="video/mp4", autoplay=True, loop=True)
else:
    st.warning(f"Видео файлы табылмады: {VIDEO_PATH}. Файлды GitHub-қа жүктегеніңізге көз жеткізіңіз.")

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
    start_prompt="🎤 Сөйлеуді бастау (Space орнына)", 
    stop_prompt="🛑 Тоқтату", 
    key='recorder'
)

if audio_input:
    # 1. Дауысты уақытша файлға сақтау
    with open("temp_audio.wav", "wb") as f:
        f.write(audio_input['bytes'])
    
    with st.spinner("Қыдыр ата сізді тыңдап жатыр..."):
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
                    {"role": "system", "content": "Сен Наурыз мерекесінде қонақтарға бата беретін Қыдыр атасың. Қазақ тілінде қысқа, даналыққа толы, 2-3 сөйлемнен аспайтын жауап бер."},
                    {"role": "user", "content": user_text}
                ]
            )
            ai_reply = completion.choices[0].message.content
            st.success(f"👴 **Қыдыр ата:** {ai_reply}")

            # 4. Edge-TTS арқылы қазақша дыбыстау
            if os.path.exists(REPLY_AUDIO):
                os.remove(REPLY_AUDIO) # Ескі файлды өшіру
            
            asyncio.run(generate_voice(ai_reply))
            
            # 5. Аудионы ойнату
            if os.path.exists(REPLY_AUDIO):
                st.audio(REPLY_AUDIO, format='audio/mp3', autoplay=True)
                
        except Exception as e:
            st.error(f"Қате орын алды: {e}")
