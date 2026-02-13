from pathlib import Path
from decouple import Config, RepositoryEnv

BASE_DIR = Path(__file__).resolve().parent.parent

ENV_PATH = Path(__file__).resolve().parent / ".env"
config = Config(RepositoryEnv(str(ENV_PATH)))

BLOG_SECRET_KEY: str = config("BLOG_SECRET_KEY")
BLOG_DEBUG: bool = config("BLOG_DEBUG", cast=bool, default=False)

BLOG_ALLOWED_HOSTS_RAW: str = config("BLOG_ALLOWED_HOSTS", default="")
BLOG_ALLOWED_HOSTS: list[str] = [h.strip() for h in BLOG_ALLOWED_HOSTS_RAW.split(",") if h.strip()]

BLOG_REDIS_URL: str = config("BLOG_REDIS_URL", default="redis://127.0.0.1:6379/1")
