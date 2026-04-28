from django.core.management.utils import get_random_secret_key

secret_key = get_random_secret_key()
print("Your Django secret key is:")
print(f'django-insecure-{secret_key}')
