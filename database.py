from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime

# إعداد قاعدة البيانات
engine = create_engine("sqlite:///manarah.db", echo=False)
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)

class User(Base):
    __tablename__ = "users"
    UserID = Column(Integer, primary_key=True, index=True)
    Username = Column(String, unique=True, nullable=False)
    PasswordHash = Column(String, nullable=False)
    Role = Column(String, default="parent")
    Email = Column(String, nullable=True)
    profiles = relationship("Profile", back_populates="user")

class Profile(Base):
    __tablename__ = "profiles"
    ProfileID = Column(Integer, primary_key=True, index=True)
    UserID = Column(Integer, ForeignKey("users.UserID"), nullable=False)
    DisplayName = Column(String, nullable=False)
    Age = Column(String, nullable=True)
    Gender = Column(String, nullable=True)
    FamilyOrder = Column(String, nullable=True)
    Interests = Column(Text, nullable=True)
    Mood = Column(String, nullable=True)
    Notes = Column(Text, nullable=True)
    user = relationship("User", back_populates="profiles")
    sessions = relationship("Session", back_populates="child")

class Session(Base):
    __tablename__ = "sessions"
    SessionID = Column(Integer, primary_key=True, index=True)
    ChildID = Column(Integer, ForeignKey("profiles.ProfileID"), nullable=False)
    StartTime = Column(DateTime, default=datetime.utcnow)
    EndTime = Column(DateTime, nullable=True)
    
    # حقول التحليل
    Advice = Column(Text, nullable=True)
    EmotionalMap = Column(Text, nullable=True)
    
    # الحقل الجديد: ملاحظات ولي الأمر
    ParentNotes = Column(Text, nullable=True)
    
    child = relationship("Profile", back_populates="sessions")
    messages = relationship("Message", back_populates="session")

class Message(Base):
    __tablename__ = "messages"
    MessageID = Column(Integer, primary_key=True, index=True)
    SessionID = Column(Integer, ForeignKey("sessions.SessionID"), nullable=False)
    Transcript_Text = Column(Text, nullable=False)
    
    # روابط الملفات الصوتية
    Audio_File_URL = Column(Text, nullable=True) # صوت منارة (الرد)
    # الحقل الجديد: صوت الطفل الأصلي للمراجعة
    Child_Audio_URL = Column(Text, nullable=True) 
    
    Timestamp = Column(DateTime, default=datetime.utcnow)
    session = relationship("Session", back_populates="messages")

class Alert(Base):
    __tablename__ = "alerts"
    AlertID = Column(Integer, primary_key=True, index=True)
    ChildID = Column(Integer, ForeignKey("profiles.ProfileID"), nullable=False)
    MessageText = Column(Text, nullable=False)
    Level = Column(String, nullable=False)
    Timestamp = Column(DateTime, default=datetime.utcnow)
    IsRead = Column(String, default="false")

def init_db():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db()