"""Shared configuration for the desktop client and database tools."""
import os
from pathlib import Path
from redis.backoff import NoBackoff
from redis.retry import Retry

ROOT = Path(__file__).resolve().parent
env_file = ROOT / '.env'
if env_file.exists():
    for raw in env_file.read_text(encoding='utf-8-sig').splitlines():
        if not raw.strip() or raw.lstrip().startswith('#') or '=' not in raw:
            continue
        key, value = raw.split('=', 1)
        if key.strip().startswith(('DOG_DB_', 'DOG_REDIS_')):
            os.environ.setdefault(key.strip(), value.strip().strip('"\''))

DB_CONFIG = {
    'dbname': os.getenv('DOG_DB_NAME', 'dog_walking_demo'),
    'user': os.getenv('DOG_DB_USER', 'dog_demo'),
    'password': os.getenv('DOG_DB_PASSWORD', 'dog_demo'),
    'host': os.getenv('DOG_DB_HOST', '127.0.0.1'),
    'port': int(os.getenv('DOG_DB_PORT', '15432')),
    'connect_timeout': 5,
}
REDIS_CONFIG = {
    'host': os.getenv('DOG_REDIS_HOST', '127.0.0.1'),
    'port': int(os.getenv('DOG_REDIS_PORT', '16379')),
    'decode_responses': True,
    'socket_connect_timeout': .2,
    'socket_timeout': .2,
    'retry': Retry(NoBackoff(), 0),
}
