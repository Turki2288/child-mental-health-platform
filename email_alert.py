import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

def send_alert_email(child_name: str, message_text: str, level: str, reason: str, recommendation: str, parent_email: str = None):
    sender = os.getenv("ALERT_EMAIL_FROM")
    password = os.getenv("ALERT_EMAIL_PASSWORD")
    receiver = parent_email or os.getenv("ALERT_EMAIL_TO")

    if not sender or not password or not receiver:
        print("⚠️ إعدادات الإيميل غير مكتملة")
        return False

    level_ar = "⚠️ تحذير" if level == "warning" else "🚨 خطر"
    level_color = "#f59e0b" if level == "warning" else "#ef4444"

    html = f"""
    <div dir="rtl" style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #0d1b4b, #1e1b4b); padding: 30px; border-radius: 15px 15px 0 0; text-align: center;">
            <h1 style="color: #a78bfa; margin: 0; font-size: 28px;">🌟 منارة</h1>
            <p style="color: rgba(255,255,255,0.6); margin: 8px 0 0;">نظام حماية الطفل</p>
        </div>

        <div style="background: #1e1b4b; padding: 30px; border-radius: 0 0 15px 15px;">
            <div style="background: {level_color}20; border: 2px solid {level_color}; border-radius: 12px; padding: 20px; margin-bottom: 20px; text-align: center;">
                <h2 style="color: {level_color}; margin: 0; font-size: 22px;">{level_ar}</h2>
            </div>

            <div style="background: rgba(255,255,255,0.05); border-radius: 12px; padding: 20px; margin-bottom: 15px;">
                <h3 style="color: #c4b5fd; margin: 0 0 10px;">👧 الطفل</h3>
                <p style="color: #fff; margin: 0; font-size: 18px; font-weight: bold;">{child_name}</p>
            </div>

            <div style="background: rgba(255,255,255,0.05); border-radius: 12px; padding: 20px; margin-bottom: 15px;">
                <h3 style="color: #c4b5fd; margin: 0 0 10px;">💬 ما قاله الطفل</h3>
                <p style="color: #fff; margin: 0; font-size: 15px; line-height: 1.6;">{message_text}</p>
            </div>

            <div style="background: rgba(255,255,255,0.05); border-radius: 12px; padding: 20px; margin-bottom: 15px;">
                <h3 style="color: #c4b5fd; margin: 0 0 10px;">🔍 السبب</h3>
                <p style="color: rgba(255,255,255,0.8); margin: 0; font-size: 14px;">{reason}</p>
            </div>

            <div style="background: rgba(52,211,153,0.1); border: 1px solid rgba(52,211,153,0.3); border-radius: 12px; padding: 20px;">
                <h3 style="color: #34d399; margin: 0 0 10px;">💡 نصيحة للوالد</h3>
                <p style="color: rgba(255,255,255,0.8); margin: 0; font-size: 14px; line-height: 1.6;">{recommendation}</p>
            </div>

            <div style="margin-top: 20px; text-align: center;">
                <p style="color: rgba(255,255,255,0.3); font-size: 12px;">
                    في الحالات الخطيرة تواصل فوراً مع الطوارئ 911 أو خط مساندة الطفل 116111
                </p>
            </div>
        </div>
    </div>
    """

    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"{'⚠️ تحذير' if level == 'warning' else '🚨 تنبيه خطر'} - منارة | {child_name}"
    msg['From'] = sender
    msg['To'] = receiver
    msg.attach(MIMEText(html, 'html'))

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender, password)
            server.sendmail(sender, receiver, msg.as_string())
        print(f"✅ تم إرسال تنبيه لـ {receiver}")
        return True
    except Exception as e:
        print(f"❌ فشل إرسال الإيميل: {e}")
        return False