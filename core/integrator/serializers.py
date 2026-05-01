from rest_framework import serializers


# ── Request serializers ───────────────────────────────────────────────────────

class AudioUploadSerializer(serializers.Serializer):
    """
    Used by both /api/voice/voice-to-text/ and /api/voice/voice-to-answer/
    Expects a multipart/form-data POST with an 'audio' file field.
    """
    audio = serializers.FileField()

    def validate_audio(self, value):
        allowed_types = [
            "audio/webm",
            "audio/wav",
            "audio/wave",
            "audio/mp4",
            "audio/ogg",
            "audio/mpeg",
            "application/octet-stream",  # some browsers send this for webm
        ]
        content_type = getattr(value, "content_type", "")
        if content_type and content_type not in allowed_types:
            raise serializers.ValidationError(
                f"Unsupported audio format: {content_type}"
            )

        max_size_mb = 5
        if value.size > max_size_mb * 1024 * 1024:
            raise serializers.ValidationError(
                f"Audio file too large. Maximum size is {max_size_mb} MB."
            )
        return value


class TextInputSerializer(serializers.Serializer):
    """
    Used by /api/voice/text-to-voice/
    Expects a JSON POST with a 'text' field.
    """
    text = serializers.CharField(max_length=4000, allow_blank=False)

    def validate_text(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Text must not be empty.")
        return value


# ── Response serializers ──────────────────────────────────────────────────────

class VoiceToTextResponseSerializer(serializers.Serializer):
    """
    Response shape for /api/voice/voice-to-text/
    Returns the transcribed text.
    """
    text = serializers.CharField()


class VoiceAnswerResponseSerializer(serializers.Serializer):
    """
    Response shape for /api/voice/voice-to-answer/ and /api/voice/text-to-voice/
    Returns the AI text answer and a URL to the generated audio file.
    """
    voice_text = serializers.CharField()
    voice_file = serializers.URLField()
