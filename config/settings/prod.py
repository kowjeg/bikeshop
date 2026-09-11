from .base import *


DEBUG = False

ALLOWED_HOSTS = [h.strip() for h in os.getenv('DJANGO_ALLOWED_HOSTS', '').split(',') if h.strip()]
