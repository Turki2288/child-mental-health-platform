import openai
import os
from dotenv import load_dotenv

load_dotenv()

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def text_to_speech(text: str, output_path: str = "response.mp3") -> str:
    """
    تحويل النص لصوت باستخدام OpenAI TTS
    """
    response = client.audio.speech.create(
        model="tts-1",
        voice="nova",  # صوت أنثى طبيعي مناسب لمنار
        input=text,
        speed=0.9  # سرعة أبطأ قليلاً للأطفال
    )

    response.stream_to_file(output_path)
    return output_path