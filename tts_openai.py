import openai
import os
import re
from dotenv import load_dotenv

load_dotenv()

# إعداد العميل بنفس الطريقة البسيطة التي نجحت عندك
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def clean_arabic_text(text: str) -> str:
    """تنظيف النص لضمان نطق سليم بدون تجاوز الكلمات"""
    # 1. إزالة كافة الحركات (التشكيل) لأنها تسبب ارتباكاً للمحرك أحياناً
    tashkeel_pattern = re.compile(r'[\u064B-\u0652]')
    text = re.sub(tashkeel_pattern, '', text)
    
    # 2. استبدال النقاط المتكررة بفاصلة لضمان وقفة مريحة للمحرك
    text = text.replace("...", "، ").replace("..", "، ")
    
    # 3. إزالة الرموز الغريبة والاكتفاء بالنص والمسافات
    text = " ".join(text.split())
    return text

def text_to_speech(text: str, output_path: str) -> str:
    # تنظيف النص لضمان عدم "بلع" الحروف
    processed_text = clean_arabic_text(text)
    
    try:
        # سنستخدم tts-1 (السريع) لتجنب انقطاع الاتصال
        # لكن سنضبط السرعة على 0.95 ليكون النطق واضحاً ومخارج الحروف دقيقة
        response = client.audio.speech.create(
            model="tts-1", 
            voice="nova",
            input=processed_text,
            speed=0.7  # تقليل السرعة قليلاً يمنع "تجاوز الكلمات" ويجعلها أوضح
        )
        
        # حفظ الملف باستخدام الطريقة التي نجحت عندك
        with open(output_path, "wb") as f:
            f.write(response.content)
            
        return output_path
        
    except Exception as e:
        print(f"TTS Error: {e}")
        return ""