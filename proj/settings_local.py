from .settings import DEBUG, BASE_DIR

DEBUG = True
STATIC_ROOT = None
STATICFILES_DIRS = [
  BASE_DIR / "static",
]