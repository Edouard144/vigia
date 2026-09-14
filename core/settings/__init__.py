import os

ENVIRONMENT = os.environ.get('ENVIRONMENT', 'production' if 'RENDER' in os.environ else 'development')

if ENVIRONMENT == 'production':
    from .production import *
else:
    from .base import *