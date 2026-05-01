
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    AudioUploadSerializer,
    TextInputSerializer,
    VoiceAnswerResponseSerializer,
    VoiceToTextResponseSerializer,
)
from .utils import transcribe_audio, generate_answer, synthesize_speech, save_audio_and_get_url
from .models import Voice


class VoiceToTextView(APIView):

    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = AudioUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        audio_file = serializer.validated_data["audio"]
        Voice.objects.create(audio_file=audio_file)

        try:
            transcript = transcribe_audio(audio_file)
            print(transcript)
        except NotImplementedError:
            return Response(
                {"detail": "transcribe_audio() is not implemented yet."},
                status=status.HTTP_501_NOT_IMPLEMENTED,
            )
        except Exception as exc:
            return Response(
                {"detail": f"Transcription failed: {str(exc)}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        response_data = {"text": transcript}
        out = VoiceToTextResponseSerializer(response_data)

        return Response(out.data, status=status.HTTP_200_OK)


class VoiceToAnswerView(APIView):
    """
    POST /api/voice/voice-to-answer/

    Accepts:  multipart/form-data  { audio: <file> }
    Returns:  { voice_text: "<answer>", voice_file: "<url>" }

    Pipeline: audio → transcript → LLM answer → TTS audio → saved file URL
    """
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = AudioUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        audio_file = serializer.validated_data["audio"]
        try:
            transcript = transcribe_audio(audio_file)
            print(transcript)
            answer_text = generate_answer(transcript)
            print(answer_text)
            audio_bytes, ext = synthesize_speech(answer_text)
        except NotImplementedError:
            return Response(
                {"detail": "Service not implemented."},
                status=status.HTTP_501_NOT_IMPLEMENTED,
            )
        except Exception as exc:
            print(exc)
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        voice_file_url = save_audio_and_get_url(
            audio_bytes,
            request,
            extension=ext
        )

        return Response(
            {
                "appeal_text": transcript,
                "voice_text": answer_text,
                "voice_file": voice_file_url,
            },
            status=status.HTTP_200_OK
        )


class TextToVoiceView(APIView):
    def post(self, request):
        serializer = TextInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user_text = serializer.validated_data["text"]
        try:
            answer_text = generate_answer(user_text)
            audio_bytes, ext = synthesize_speech(answer_text)

        except NotImplementedError:
            return Response(
                {"detail": "One or more service stubs are not implemented yet."},
                status=status.HTTP_501_NOT_IMPLEMENTED,
            )
        except Exception as exc:
            return Response(
                {"detail": f"Processing failed: {str(exc)}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        voice_file_url = save_audio_and_get_url(
            audio_bytes,
            request,
            extension=ext
        )

        response_data = {
            "voice_text": answer_text,
            "voice_file": voice_file_url,
        }
        out = VoiceAnswerResponseSerializer(response_data)
        return Response(out.data, status=status.HTTP_200_OK)
