#!/bin/sh
set -e

echo "Waiting for Redis..."

REDIS_HOST=$(python - <<'PY'
import os
from urllib.parse import urlparse

url = os.getenv("BLOG_REDIS_URL", "redis://redis:6379/0")
print(urlparse(url).hostname or "redis")
PY
)

REDIS_PORT=$(python - <<'PY'
import os
from urllib.parse import urlparse

url = os.getenv("BLOG_REDIS_URL", "redis://redis:6379/0")
print(urlparse(url).port or 6379)
PY
)

while ! nc -z "$REDIS_HOST" "$REDIS_PORT"; do
  sleep 1
done

echo "Redis is up"

python manage.py migrate
# python manage.py collectstatic --noinput
python manage.py compilemessages

if [ "$BLOG_SEED_DB" = "true" ]; then
  python manage.py seed
fi

exec "$@"