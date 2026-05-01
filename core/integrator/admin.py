from django.contrib import admin
from .models import LLM, Voice

admin.site.register(LLM)
admin.site.register(Voice)