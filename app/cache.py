import redis

from .config import settings

# decode_responses=True -> hasil get() langsung str, bukan bytes.
# Koneksi sifatnya lazy: baru konek pas perintah pertama dijalankan.
r = redis.from_url(settings.redis_url, decode_responses=True)
