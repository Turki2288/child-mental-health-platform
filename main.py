from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from whisper_stt import transcribe_audio
from llm_groq import get_response, analyze_session_deeply, detect_danger
from tts_openai import text_to_speech
from db_helper import save_message, save_alert, get_parent_email
from email_alert import send_alert_email
from pydantic import BaseModel
import uvicorn
import shutil
import os
import qrcode
import io
import json
import hashlib
from datetime import datetime

app = FastAPI(title="Manarah")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

if not os.path.exists("static/uploads"):
    os.makedirs("static/uploads")


class NoteRequest(BaseModel):
    note: str


class UserCreate(BaseModel):
    username: str
    password: str
    email: str


class UserLogin(BaseModel):
    username: str
    password: str


class ChildCreate(BaseModel):
    user_id: int
    name: str
    gender: str = "male"
    age: str = ""
    interests: str = ""


@app.get("/")
async def root():
    return FileResponse("static/index.html")


@app.post("/register")
async def register(user: UserCreate):
    from database import SessionLocal, User

    db = SessionLocal()
    try:
        existing_user = db.query(User).filter(User.Username == user.username).first()
        if existing_user:
            return JSONResponse({"success": False, "message": "اسم المستخدم موجود مسبقاً"})

        new_user = User(
            Username=user.username,
            PasswordHash=hashlib.sha256(user.password.encode()).hexdigest(),
            Email=user.email,
            Role="parent"
        )

        db.add(new_user)
        db.commit()

        return {"success": True, "message": "تم التسجيل بنجاح"}

    finally:
        db.close()


@app.post("/login")
async def login(user: UserLogin):
    from database import SessionLocal, User

    db = SessionLocal()
    try:
        pass_hash = hashlib.sha256(user.password.encode()).hexdigest()

        db_user = db.query(User).filter(
            User.Username == user.username,
            User.PasswordHash == pass_hash
        ).first()

        if db_user:
            return {
                "success": True,
                "user_id": db_user.UserID,
                "username": db_user.Username
            }

        return JSONResponse(
            {"success": False, "message": "بيانات الدخول غير صحيحة"},
            status_code=401
        )

    finally:
        db.close()


@app.post("/add_child")
async def add_child(child: ChildCreate):
    from database import SessionLocal, Profile

    db = SessionLocal()
    try:
        new_profile = Profile(
            UserID=child.user_id,
            DisplayName=child.name,
            Gender=child.gender,
            Age=child.age,
            Interests=child.interests
        )

        db.add(new_profile)
        db.commit()
        db.refresh(new_profile)

        return {
            "success": True,
            "message": "تمت إضافة الطفل بنجاح",
            "child_id": new_profile.ProfileID
        }

    except Exception as e:
        print(f"Error adding child: {e}")
        return JSONResponse(
            {"success": False, "message": "فشل في إضافة الطفل"},
            status_code=500
        )

    finally:
        db.close()


@app.get("/get_all_users")
async def get_all_users():
    from database import SessionLocal, User

    db = SessionLocal()
    try:
        users = db.query(User).all()
        return [
            {
                "id": u.UserID,
                "username": u.Username,
                "email": u.Email
            }
            for u in users
        ]

    finally:
        db.close()


@app.get("/get_user_children/{user_id}")
async def get_user_children(user_id: int):
    from database import SessionLocal, Profile

    db = SessionLocal()
    try:
        children = db.query(Profile).filter(Profile.UserID == user_id).all()

        return [
            {
                "id": c.ProfileID,
                "name": c.DisplayName,
                "gender": c.Gender,
                "age": c.Age,
                "interests": c.Interests
            }
            for c in children
        ]

    finally:
        db.close()


@app.get("/get_children")
async def get_children(user_id: int):
    from database import SessionLocal, Profile, Session

    db = SessionLocal()
    try:
        children = db.query(Profile).filter(Profile.UserID == user_id).all()
        result = []

        for child in children:
            sessions = db.query(Session).filter(Session.ChildID == child.ProfileID).all()

            valid_scores = []

            for session in sessions:
                if session.EmotionalMap:
                    try:
                        emotions = json.loads(session.EmotionalMap)

                        joy = int(emotions.get("joy", 0))
                        sadness = int(emotions.get("sadness", 0))
                        fear = int(emotions.get("fear", 0))
                        anger = int(emotions.get("anger", 0))

                        score = max(
                            0,
                            min(100, joy - ((sadness + fear + anger) // 3))
                        )

                        valid_scores.append(score)

                    except Exception:
                        pass

            avg_score = sum(valid_scores) // len(valid_scores) if valid_scores else 0

            result.append({
                "id": child.ProfileID,
                "name": child.DisplayName,
                "gender": child.Gender,
                "age": child.Age,
                "interests": child.Interests,
                "mood": child.Mood,
                "notes": child.Notes,
                "score": avg_score
            })

        return result

    finally:
        db.close()


@app.get("/child_info/{child_id}")
async def get_child_info(child_id: int):
    from database import SessionLocal, Profile

    db = SessionLocal()
    try:
        child = db.query(Profile).filter(Profile.ProfileID == child_id).first()

        if child:
            return {
                "found": True,
                "id": child.ProfileID,
                "name": child.DisplayName,
                "age": child.Age,
                "gender": child.Gender,
                "interests": child.Interests,
                "mood": child.Mood,
                "notes": child.Notes
            }

        return {"found": False}

    finally:
        db.close()


@app.get("/qrcode/{child_id}")
async def generate_qrcode(child_id: int):
    computer_ip = "192.168.25.9"
    url = f"http://{computer_ip}:8000/static/child_welcome.html?child_id={child_id}"

    img = qrcode.make(url)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    print(f"✅ تم توليد باركود للرابط: {url}")
    return StreamingResponse(buf, media_type="image/png")


@app.post("/ask")
async def ask(audio: UploadFile = File(...), child_id: int = Form(1)):
    child_audio_filename = f"static/uploads/child_{os.urandom(4).hex()}.wav"

    try:
        with open(child_audio_filename, "wb") as f:
            shutil.copyfileobj(audio.file, f)

        user_text = transcribe_audio(child_audio_filename)

        from database import SessionLocal, Profile

        db = SessionLocal()
        child = db.query(Profile).filter(Profile.ProfileID == child_id).first()

        child_info = {
            "name": child.DisplayName if child else "يا بطل",
            "age": child.Age if child else "",
            "gender": child.Gender if child else "",
            "interests": child.Interests if child else "",
            "mood": child.Mood if child else "",
            "notes": child.Notes if child else ""
        }

        db.close()

        response_text = get_response(user_text, child_info)

        agent_audio_filename = f"static/uploads/response_{os.urandom(4).hex()}.mp3"
        text_to_speech(response_text, agent_audio_filename)

        save_message(
            f"الطفل: {user_text} | منار: {response_text}",
            agent_audio_filename,
            child_id,
            child_audio_filename
        )

        danger = detect_danger(user_text)

        if danger.get("level") in ["warning", "danger"]:
            save_alert(child_id, user_text, danger["level"])
            send_alert_email(
                child_info["name"],
                user_text,
                danger["level"],
                danger.get("reason", ""),
                danger.get("recommendation", ""),
                get_parent_email(child_id)
            )

        return JSONResponse({
            "user_text": user_text,
            "response_text": response_text,
            "audio_url": "/" + agent_audio_filename,
            "child_audio_url": "/" + child_audio_filename
        })

    except Exception as e:
        import traceback
        print(f"❌ خطأ مفصل في /ask:\n{traceback.format_exc()}")
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/end_session/{child_id}")
async def end_session(child_id: int):
    from database import SessionLocal, Session, Message

    db = SessionLocal()
    try:
        session = db.query(Session).filter(
            Session.ChildID == child_id,
            Session.EndTime == None
        ).order_by(Session.SessionID.desc()).first()

        if not session:
            return {"success": False, "message": "لا توجد جلسة مفتوحة"}

        messages = db.query(Message).filter(Message.SessionID == session.SessionID).all()

        if messages:
            full_transcript = "\n".join([m.Transcript_Text for m in messages])
            analysis = analyze_session_deeply(full_transcript)

            session.Advice = analysis.get("advice", "لا توجد توصية.")
            session.EmotionalMap = json.dumps(
                analysis.get(
                    "emotions",
                    {"joy": 50, "sadness": 0, "fear": 0, "anger": 0}
                ),
                ensure_ascii=False
            )

        session.EndTime = datetime.utcnow()
        db.commit()

        return {
            "success": True,
            "session_id": session.SessionID,
            "message": "تم إنهاء الجلسة وحفظ التحليل"
        }

    except Exception as e:
        import traceback
        print(f"❌ خطأ في end_session:\n{traceback.format_exc()}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

    finally:
        db.close()


@app.get("/analyze_session/{session_id}")
async def analyze_session(session_id: int):
    from database import SessionLocal, Session, Message

    db = SessionLocal()
    try:
        session = db.query(Session).filter(Session.SessionID == session_id).first()

        if not session:
            return JSONResponse({"error": "Session not found"}, status_code=404)

        messages = db.query(Message).filter(Message.SessionID == session_id).all()

        if not messages:
            return JSONResponse({"error": "No data"})

        if session.EmotionalMap and session.Advice:
            try:
                emotions = json.loads(session.EmotionalMap)
            except Exception:
                emotions = {"joy": 50, "sadness": 0, "fear": 0, "anger": 0}

            advice = session.Advice

        else:
            full_transcript = "\n".join([m.Transcript_Text for m in messages])
            analysis = analyze_session_deeply(full_transcript)

            emotions = analysis.get(
                "emotions",
                {"joy": 50, "sadness": 0, "fear": 0, "anger": 0}
            )
            advice = analysis.get("advice", "يرجى متابعة جلسات الطفل بانتظام.")

            session.Advice = advice
            session.EmotionalMap = json.dumps(emotions, ensure_ascii=False)
            db.commit()

        script_data = []

        for m in messages:
            script_data.append({
                "text": m.Transcript_Text,
                "audio_url": "/" + m.Audio_File_URL if m.Audio_File_URL else None,
                "child_audio_url": "/" + m.Child_Audio_URL if m.Child_Audio_URL else None
            })

        return JSONResponse({
            "emotions": emotions,
            "advice": advice,
            "script": script_data,
            "notes": session.ParentNotes or ""
        })

    finally:
        db.close()


@app.post("/save_note/{session_id}")
async def save_note(session_id: int, request: NoteRequest):
    from database import SessionLocal, Session

    db = SessionLocal()
    try:
        session = db.query(Session).filter(Session.SessionID == session_id).first()

        if session:
            session.ParentNotes = request.note
            db.commit()
            return {"success": True}

        return {"success": False}

    finally:
        db.close()


@app.get("/sessions")
async def get_sessions_list(user_id: int = None, child_id: int = None):
    from database import SessionLocal, Profile, Session, Message

    db = SessionLocal()

    try:
        query = db.query(Session)

        if child_id:
            query = query.filter(Session.ChildID == child_id)

        elif user_id:
            children = db.query(Profile).filter(Profile.UserID == user_id).all()
            child_ids = [child.ProfileID for child in children]

            if not child_ids:
                return []

            query = query.filter(Session.ChildID.in_(child_ids))

        sessions = query.order_by(Session.StartTime.desc()).all()

        result = []

        for s in sessions:
            child = db.query(Profile).filter(Profile.ProfileID == s.ChildID).first()
            messages = db.query(Message).filter(Message.SessionID == s.SessionID).all()

            emotions = None

            if s.EmotionalMap:
                try:
                    emotions = json.loads(s.EmotionalMap)
                except Exception:
                    emotions = None

            result.append({
                "session_id": s.SessionID,
                "child_id": s.ChildID,
                "child_name": child.DisplayName if child else "غير معروف",
                "start_time": s.StartTime.strftime("%Y-%m-%d %H:%M") if s.StartTime else "",
                "end_time": s.EndTime.strftime("%Y-%m-%d %H:%M") if s.EndTime else None,
                "advice": s.Advice if s.Advice else "بانتظار التحليل...",
                "emotions": emotions,
                "notes": s.ParentNotes if s.ParentNotes else "",
                "messages": [
                    {
                        "message_id": m.MessageID,
                        "text": m.Transcript_Text,
                        "audio_url": "/" + m.Audio_File_URL if m.Audio_File_URL else None,
                        "child_audio_url": "/" + m.Child_Audio_URL if m.Child_Audio_URL else None,
                        "timestamp": m.Timestamp.strftime("%Y-%m-%d %H:%M") if m.Timestamp else ""
                    }
                    for m in messages
                ]
            })

        return result

    finally:
        db.close()


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)