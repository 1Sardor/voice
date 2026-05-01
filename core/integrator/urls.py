from django.urls import path
from .views import VoiceToTextView, VoiceToAnswerView, TextToVoiceView

urlpatterns = [
    path("voice/voice-to-text/", VoiceToTextView.as_view(),   name="voice-to-text"),
    path("voice/voice-to-answer/", VoiceToAnswerView.as_view(), name="voice-to-answer"),
    path("voice/text-to-voice/",  TextToVoiceView.as_view(),  name="text-to-voice"),
]
