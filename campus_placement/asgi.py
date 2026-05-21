"""
ASGI config for campus_placement project.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'campus_placement.settings')

application = get_asgi_application()
