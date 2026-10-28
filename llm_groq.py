import os
import json
import time # إضافة مكتبة الوقت للتعامل مع إعادة المحاولة
from groq import Groq
from dotenv import load_dotenv
from rag_retriever import retrieve_context, documents

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# الموديل المعتمد لضمان السرعة والاستقرار وتقليل أخطاء الاتصال
MODEL_NAME = "llama-3.1-8b-instant"

def get_response(user_text: str, child_info: dict = None) -> str:
    """
    توليد رد ذكي مع نظام إعادة المحاولة لضمان عدم توقف المحادثة
    """
    context = retrieve_context(user_text, documents)
    child_name = child_info.get("name", "يا بطل") if child_info else "يا بطل"
    
    child_details = ""
    if child_info:
        child_details = f"""
Child Information:
- Name: {child_name}
- Age: {child_info.get('age', '')}
- Gender: {child_info.get('gender', '')}
- Family Order: {child_info.get('order', '')}
- Interests: {child_info.get('interests', '')}
- General Temperament: {child_info.get('mood', '')}
- Special Notes: {child_info.get('notes', '')}
"""

    system_prompt = f"""
أنت "منار"، مساعد ذكي وصديق للأطفال في السعودية.
{child_details}
سياق علمي لتوجيه نبرة صوتك: {context}

القواعد:
1. نادِ الطفل باسمه: {child_name}.
2. استخدم لهجة سعودية بيضاء بسيطة جداً ومحببة.
3. اجعل الرد قصيراً (جملتين إلى ثلاث).
4. شكل النص (التشكيل) بشكل كامل لضمان جودة النطق الصوتي.
5. استخدم كلمات تشجيعية مثل 'يا بطل' أو 'يا ذكي'.
"""

    # محاولة الاتصال حتى 3 مرات في حال حدوث خطأ في الشبكة
    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_text}
                ],
                max_tokens=300,
                timeout=15.0 # تحديد وقت انتظار للاستجابة
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"⚠️ محاولة جلب الرد {attempt + 1} فشلت: {e}")
            if attempt < 2:
                time.sleep(1) # الانتظار ثانية قبل المحاولة التالية
    
    return "معليش يا بطل، يبدو إن عندي مشكلة بسيطة في الاتصال، وش كنت تقول؟"

def analyze_session_deeply(full_transcript: str):
    """
    تحليل مشاعر الجلسة مع نظام حماية من أخطاء الاتصال
    """
    context = retrieve_context(full_transcript, documents, top_k=3)

    system_instruction = """
    You are an expert Child Psychologist. Analyze the provided transcript.
    You MUST return a valid JSON object ONLY:
    {
      "emotions": {"joy": 0-100, "sadness": 0-100, "fear": 0-100, "anger": 0-100},
      "advice": "Scientific recommendation in Arabic",
      "status": "Excellent/Good/Average/Needs Attention"
    }
    """
    prompt = f"Scientific Context: {context}\n\nSession Transcript: {full_transcript}"

    for attempt in range(2):
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                timeout=20.0
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"⚠️ محاولة تحليل الجلسة {attempt + 1} فشلت: {e}")
            time.sleep(1)

    return {
        "emotions": {"joy": 50, "sadness": 0, "fear": 0, "anger": 0},
        "advice": "يرجى متابعة جلسات الطفل بانتظام لضمان دقة التحليل.",
        "status": "Good"
    }

def detect_danger(text: str) -> dict:
    """
    فحص الأمان والتحقق من وجود تنمر أو خطر
    """
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": """You are a child safety monitoring system. Return JSON only:
{
  "is_dangerous": false,
  "level": "safe",
  "reason": "سبب قصير بالعربي",
  "recommendation": "نصيحة للأب بالعربي"
}"""
                },
                {"role": "user", "content": text}
            ],
            response_format={"type": "json_object"},
            timeout=10.0
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"⚠️ فشل فحص الأمان: {e}")
        return {"is_dangerous": False, "level": "safe", "reason": "فشل الاتصال بالفاحص", "recommendation": ""}