import uuid
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from google import genai
from openai import OpenAI

from .models import LLM
x_api_key = "3uk-Kol437yszua7pYCQ3lvc_7-27v0kOWPdRPsA"

import requests
import tempfile
import subprocess
import os

def transcribe_audio(audio_file) -> str:
    url = "https://service.muxlisa.uz/api/v2/stt"
    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp_in:
        for chunk in audio_file.chunks():
            tmp_in.write(chunk)
        input_path = tmp_in.name
    output_path = input_path.replace(".webm", ".wav")

    subprocess.run([
        "ffmpeg",
        "-i", input_path,
        "-ar", "16000",        # recommended sample rate
        "-ac", "1",            # mono
        output_path
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    with open(output_path, "rb") as f:
        files = [
            ("audio", ("audio.wav", f, "audio/wav"))
        ]
        headers = {
            "x-api-key": x_api_key
        }
        response = requests.post(url, headers=headers, files=files)
    os.remove(input_path)
    os.remove(output_path)
    if response.status_code != 200:
        raise Exception(response.text)
    data = response.json()
    return data.get("text", "")


def generate_answer(transcript: str) -> str:
    llm = LLM.objects.filter(is_active=True).first()
    if not llm:
        return "AI service is not configured."
    if llm.type == 1:
        return generate_with_chatgpt(transcript, llm.token)
    if llm.type == 2:
        return generate_with_gemini(transcript, llm.token)
    return "Unsupported AI service."


def generate_with_chatgpt(transcript: str, token: str) -> str:
    client = OpenAI(api_key=token)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """
Siz rasmiy tashkilotning virtual yordamchisiz. Sizning asosiy vazifangiz foydalanuvchidan murojaat matnini qabul qilish va uni rasmiy tarzda tasdiqlashdir.
Qoidalar:
- Har doim o‘zbek tilida, hurmat bilan va rasmiy ohangda javob bering.
- Javoblar qisqa, aniq va tushunarli bo‘lsin.
- Faqat murojaat qabul qilish vazifasini bajaring.
Murojaatni aniqlash:
- Murojaat — bu muammo, shikoyat, hodisa yoki ehtiyojni bildiruvchi gap.
  Masalan:
  - "svet o‘chdi"
  - "gaz yo‘q"
  - "meni mashina urib ketdi"
  - "menga kurs kerak"
- Agar gapda muammo yoki talab bo‘lmasa (masalan: "salom", "mening ismim Sardor", "rahmat"):
  → bu murojaat hisoblanmaydi.
Xulq-atvor:
- Agar foydalanuvchi salomlashsa yoki o‘zini tanishtirsa:
  "Assalomu alaykum. Murojaatingizni yozib qoldirishingiz mumkin."
- Agar foydalanuvchi murojaatga aloqasiz gap yozsa:
  "Iltimos, murojaatingizni yozib qoldiring."
- Agar foydalanuvchi noaniq yoki juda qisqa yozsa:
  "Iltimos, murojaatingizni batafsilroq bayon qiling."
- Agar foydalanuvchi yozuvi muammo yoki ehtiyojni bildirsa (murojaat bo‘lsa):
  "Rahmat. Sizning murojaatingiz qabul qilindi. Tez orada ko‘rib chiqilib, natijasi bo‘yicha sizga ma’lumot beriladi."
Cheklovlar:
- Murojaat bo‘lmagan matnni murojaat sifatida qabul qilmang.
- Hech qachon ortiqcha izoh bermang.
- Hazil yoki norasmiy uslubdan foydalanmang.
- Qo‘shimcha shaxsiy ma’lumot so‘ramang.
                """
            },
            {
                "role": "user",
                "content": transcript
            }
        ],
    )
    return response.choices[0].message.content.strip()


def generate_with_gemini(transcript: str, token: str) -> str:
    client = genai.Client(api_key=token)
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=transcript,
        config={
            "system_instruction": """
Siz tashkilotning rasmiy vakilisiz.
Rasmiy, muloyim va professional javob yozing.
Apellyatsiya qabul qilinganini tasdiqlang.
    """
        }
    )
    return response.text.strip()


def synthesize_speech(text: str) -> tuple[bytes, str]:
    url = "https://service.muxlisa.uz/api/v2/tts"
    headers = {
        "x-api-key": x_api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "text": text,
        "speaker": 0
    }
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code != 200:
        raise Exception(response.text)
    content_type = response.headers.get("Content-Type", "audio/mpeg")
    if "wav" in content_type:
        ext = "wav"
    else:
        ext = "mp3"
    return response.content, ext


# ── Shared utility ────────────────────────────────────────────────────────────


def save_audio_and_get_url(audio_bytes: bytes, request, extension: str) -> str:
    filename = f"voice/{uuid.uuid4().hex}.{extension}"
    path = default_storage.save(filename, ContentFile(audio_bytes))
    url = default_storage.url(path)
    return request.build_absolute_uri(url)