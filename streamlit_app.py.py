import cv2
import speech_recognition as sr
import os
import pygame
from openai import OpenAI
import asyncio
import edge_tts

# --- БАПТАУЛАР ---
client = OpenAI(api_key="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")
LANGUAGE = "kk-KZ"
BASE_DIR = r"C:\Users\User\Documents\nauryz_ai"
TALK_VIDEO = os.path.join(BASE_DIR, "kydyr_ata.mp4")
REPLY_AUDIO = os.path.join(BASE_DIR, "reply.mp3")

pygame.mixer.init()

async def generate_voice(text):
    """Қазақша дауыс шығару (Microsoft Edge)"""
    voice = "kk-KZ-DauletNeural" # Немесе kk-KZ-AigulNeural
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(REPLY_AUDIO)

def main():
    r = sr.Recognizer()
    window_name = 'Nauryz_AI_Panel'
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    print("=== ПАНЕЛЬ ДАЙЫН: SPACE - сөйлеу | ESC - өшіру ===")

    while True:
        wait_cap = cv2.VideoCapture(TALK_VIDEO)
        ret, frame = wait_cap.read()
        if ret:
            cv2.imshow(window_name, frame)
        
        key = cv2.waitKey(10) & 0xFF
        if key == 27: break
        
        if key == 32: # SPACE
            print("Тыңдап тұрмын...")
            with sr.Microphone() as source:
                r.adjust_for_ambient_noise(source)
                try:
                    audio = r.listen(source, timeout=5)
                    user_text = r.recognize_google(audio, language=LANGUAGE)
                    print(f"Сұрақ: {user_text}")

                    completion = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[{"role": "system", "content": "Сен Қыдыр атасың. Қазақша қысқа бата бер."},
                                  {"role": "user", "content": user_text}]
                    )
                    ai_reply = completion.choices[0].message.content
                    print(f"Қыдыр ата: {ai_reply}")

                    # АУДИОНЫ ЖАСАУ (Edge-TTS)
                    pygame.mixer.music.unload()
                    asyncio.run(generate_voice(ai_reply))
                    
                    # ОЙНАТУ
                    if os.path.exists(REPLY_AUDIO):
                        talk_cap = cv2.VideoCapture(TALK_VIDEO)
                        pygame.mixer.music.load(REPLY_AUDIO)
                        pygame.mixer.music.play()
                        
                        while talk_cap.isOpened() and pygame.mixer.music.get_busy():
                            t_ret, t_frame = talk_cap.read()
                            if not t_ret: talk_cap.set(cv2.CAP_PROP_POS_FRAMES, 0); continue
                            cv2.imshow(window_name, t_frame)
                            if cv2.waitKey(20) & 0xFF == 27: break
                        talk_cap.release()

                except Exception as e:
                    print(f"Қате: {e}")
        
        wait_cap.release()

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
