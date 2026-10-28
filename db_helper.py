from database import SessionLocal, Session, Message, User, Profile, Alert, init_db
from datetime import datetime
import hashlib

init_db()

def save_message(transcript: str, audio_url: str, child_id: int, child_audio_url: str = None) -> int:
    """حفظ رسالة الحوار مع روابط الصوت للطفل ومنار """
    db = SessionLocal()
    try:
        # البحث عن جلسة نشطة
        session = db.query(Session).filter(
            Session.ChildID == child_id,
            Session.EndTime == None
        ).first()

        if not session:
            session = Session(ChildID=child_id, StartTime=datetime.utcnow())
            db.add(session)
            db.commit()
            db.refresh(session)

        message = Message(
            SessionID=session.SessionID,
            Transcript_Text=transcript,
            Audio_File_URL=audio_url,
            Child_Audio_URL=child_audio_url, # حفظ صوت الطفل الأصلي للمراجعة
            Timestamp=datetime.utcnow()
        )
        db.add(message)
        db.commit()
        return message.MessageID
    finally:
        db.close()

def save_alert(child_id: int, message_text: str, level: str):
    db = SessionLocal()
    try:
        alert = Alert(
            ChildID=child_id,
            MessageText=message_text,
            Level=level,
            Timestamp=datetime.utcnow(),
            IsRead="false"
        )
        db.add(alert)
        db.commit()
    finally:
        db.close()

def get_all_sessions(child_id: int = 1):
    db = SessionLocal()
    try:
        sessions = db.query(Session).filter(
            Session.ChildID == child_id
        ).order_by(Session.StartTime.desc()).all()

        result = []
        for s in sessions:
            result.append({
                "session_id": s.SessionID,
                "start_time": s.StartTime.strftime("%Y-%m-%d %H:%M"),
                "notes": s.ParentNotes if hasattr(s, 'ParentNotes') else "",
                "advice": s.Advice if s.Advice else "بانتظار التحليل..."
            })
        return result
    finally:
        db.close()

def get_parent_email(child_id: int) -> str:
    db = SessionLocal()
    try:
        child = db.query(Profile).filter(Profile.ProfileID == child_id).first()
        if not child: return None
        user = db.query(User).filter(User.UserID == child.UserID).first()
        return user.Email if user else None
    finally:
        db.close()

def create_default_child():
    db = SessionLocal()
    try:
        child = db.query(Profile).filter(Profile.ProfileID == 1).first()
        if not child:
            user = db.query(User).filter(User.UserID == 1).first()
            if not user:
                user = User(
                    Username="parent",
                    PasswordHash=hashlib.sha256("1234".encode()).hexdigest(),
                    Role="parent",
                    Email="parent@example.com"
                )
                db.add(user)
                db.commit()
                db.refresh(user)

            child = Profile(UserID=user.UserID, DisplayName="الطفل")
            db.add(child)
            db.commit()
    finally:
        db.close()

create_default_child()