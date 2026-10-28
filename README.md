# Manara: AI Voice Companion for Children's Mental Health

Manara is a voice-based AI friend that talks with children in Saudi dialect, understands their emotions, and keeps parents informed through a monitoring dashboard.

Graduation project, Computer Science, Prince Sattam bin Abdulaziz University (2026).

## The problem
- Children often struggle to express anxiety through typing.
- Most mental health apps support only English or formal Arabic.
- Existing apps hide conversations from parents.

## Features
- **Voice conversation:** the child speaks naturally and the AI replies by voice in Saudi dialect.
- **Emotion analysis:** each conversation is analyzed to detect the child's emotional state.
- **Parent dashboard:** daily mood tracking, audio recordings, and conversation transcripts.

## Tech stack
| Part | Technology |
| --- | --- |
| Backend | Python, FastAPI |
| Database | PostgreSQL |
| Speech-to-text | OpenAI Whisper |
| Language model | Llama 3.1 |
| Text-to-speech | OpenAI TTS |
| Child app | Unity (Windows) |
| Parent app | SwiftUI (iOS) |

## Setup
Create a `.env` file in the project folder with your own API key:

```
OPENAI_API_KEY=your_key_here
```

## Team
- Turki
- Nawaf
- Mohammed
