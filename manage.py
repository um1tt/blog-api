import os
from pathlib import Path

from decouple import Config, RepositoryEnv
from django.core.management import execute_from_command_line

BASE_DIR = Path(__file__).resolve().parent
env_file = BASE_DIR / "settings" / ".env"

if env_file.exists():
    config = Config(RepositoryEnv(str(env_file)))
    env_id = config("BLOG_ENV_ID", default="local")
else:
    env_id = "local"

os.environ.setdefault("DJANGO_SETTINGS_MODULE", f"settings.env.{env_id}")

execute_from_command_line(os.sys.argv)
