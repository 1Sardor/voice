from django.db import models


class LLM(models.Model):
    type = models.IntegerField(choices=(
        (1, "ChatGPT"),
        (2, "Gemini")
    ))
    token = models.TextField()
    is_active = models.BooleanField(default=True, unique=True)


class Voice(models.Model):
    audio_file = models.FileField(upload_to="voices/")

