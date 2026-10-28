import azure.cognitiveservices.speech as speechsdk
import os
from dotenv import load_dotenv

load_dotenv()

speech_config = speechsdk.SpeechConfig(
    subscription=os.getenv("AZURE_SPEECH_KEY"),
    region=os.getenv("AZURE_SPEECH_REGION")
)

speech_config.speech_synthesis_voice_name = "ar-EG-SalmaNeural"
audio_config = speechsdk.audio.AudioOutputConfig(filename="test_output.mp3")

synthesizer = speechsdk.SpeechSynthesizer(
    speech_config=speech_config,
    audio_config=audio_config
)

result = synthesizer.speak_text_async("مرحباً أنا منارة").get()

print(f"النتيجة: {result.reason}")

reason = result.properties.get_property(speechsdk.PropertyId.CancellationDetails_Reason)
details = result.properties.get_property(speechsdk.PropertyId.CancellationDetails_ReasonDetailedText)

print(f"السبب: {reason}")
print(f"التفاصيل: {details}")