# ShortLink API

URL shortener kecil tapi production-realistic. Bikin short link, redirect, hitung klik.
Ini app dari "tim dev" — tugas lu (DevOps) yang bikin dia jalan dengan benar di server.

---

## Arsitektur (high level)

```
client ──> [ ShortLink API ] ──> [ PostgreSQL ]   (penyimpanan link + counter klik)
                  │
                  └──────────────> [ Redis ]        (cache lookup + rate limiting)
```

3 komponen: **api** (app ini), **PostgreSQL**, **Redis**.

---

## Struktur direktori

```
shortlink/
├── app/
│   ├── __init__.py
│   ├── main.py            # FastAPI app + semua endpoint (health, api, redirect)
│   ├── config.py          # baca env, fail-fast kalau env wajib kosong
│   ├── db.py              # engine + session SQLAlchemy
│   ├── models.py          # tabel links
│   ├── cache.py           # client Redis
│   └── schemas.py         # pydantic request/response
├── scripts/
│   └── migrate.py         # bikin tabel — LANGKAH TERPISAH, jalanin sebelum app start
├── tests/
│   ├── conftest.py        # fixture: setup tabel + TestClient (set env sebelum import app)
│   └── test_smoke.py      # smoke test: health, create, redirect, click count, validasi, 404
├── requirements.txt       # dependency runtime (udah dipin versinya)
├── requirements-dev.txt   # dependency test (pytest, httpx)
├── pytest.ini             # config pytest (pythonpath + testpaths)
├── .env.example           # contoh config — copy jadi .env, JANGAN commit .env
├── .gitignore
└── README.md
```

> Entry point app: `app.main:app` (dipakai uvicorn).
> Migrasi: `python scripts/migrate.py` (dipanggil dari root project).

---

## Kontrak teknis (yang HARUS lu penuhi)

### Cara build & run (dari sisi app)
- Bahasa: Python 3.11+
- Install deps: `pip install -r requirements.txt`
- Migrasi DB (langkah TERPISAH, jalanin sebelum app start):
  ```
  python scripts/migrate.py
  ```
- Start app (produksi):
  ```
  uvicorn app.main:app --host 0.0.0.0 --port 8000
  ```
- App listen di port `8000` (bisa lu mapping sesuka lu).

### Config — SEMUA via environment variable
App baca config dari **environment**, bukan dari file di dalam image.
Lihat `.env.example`.

| Env var                 | Wajib? | Default                 | Keterangan                          |
|-------------------------|--------|-------------------------|-------------------------------------|
| `DATABASE_URL`          | ✅ ya  | —                       | `postgresql+psycopg2://user:pass@host:5432/db` |
| `REDIS_URL`             | ✅ ya  | —                       | `redis://host:6379/0`               |
| `APP_PORT`              | ❌     | `8000`                  | informasi aja                       |
| `BASE_URL`              | ❌     | `http://localhost:8000` | dipakai buat nyusun short_url        |
| `RATE_LIMIT_PER_MINUTE` | ❌     | `20`                    | batas create link / IP / menit      |
| `SHORT_CODE_LENGTH`     | ❌     | `7`                     | panjang kode                        |

> ⚠️ Kalau `DATABASE_URL` atau `REDIS_URL` kosong, app **sengaja crash saat start**
> dengan error jelas. Ini behavior 12-factor, bukan bug.

### Endpoint
| Method | Path                              | Fungsi                              |
|--------|-----------------------------------|-------------------------------------|
| POST   | `/api/links`                      | bikin short link (body: `{"url": "..."}`) |
| GET    | `/{short_code}`                   | redirect 302 ke url asli + hitung klik |
| GET    | `/api/links/{short_code}/stats`   | lihat jumlah klik                   |
| GET    | `/healthz`                        | **liveness** — selalu 200 kalau app hidup |
| GET    | `/readyz`                         | **readiness** — 200 kalau DB+Redis OK, 503 kalau enggak |
| GET    | `/docs`                           | Swagger UI (auto)                   |

### Karakteristik runtime
- Log keluar ke **stdout/stderr** (jangan ke file).
- Stateless: semua state ada di PostgreSQL + Redis. App-nya bisa di-restart kapan aja.
- Butuh PostgreSQL siap **sebelum** migrasi jalan; butuh DB+Redis siap sebelum `/readyz` hijau.

---

## Testing (smoke test)

```bash
pip install -r requirements.txt -r requirements-dev.txt
pytest
```

> ⚠️ Smoke test **butuh PostgreSQL + Redis beneran jalan** (test-nya nyentuh DB & cache
> via `/readyz`, create link, redirect). Set `DATABASE_URL` & `REDIS_URL` dulu.
> Tabel dibikin otomatis oleh `tests/conftest.py` (`create_all`), jadi nggak perlu
> jalanin `migrate.py` manual buat test.

Di CI: sediain Postgres + Redis lewat `services:`, set env-nya, baru `pytest`.
Cakupan: health/readiness, create link (201), tolak URL invalid (422), redirect +
counter klik, dan 404 buat kode nggak dikenal.

---

## Contoh test manual
```bash
# bikin link
curl -X POST http://localhost:8000/api/links \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://www.google.com"}'
# -> {"short_code":"aB3xK9z","short_url":"...","original_url":"..."}

# redirect (ikutin)
curl -iL http://localhost:8000/aB3xK9z

# stats
curl http://localhost:8000/api/links/aB3xK9z/stats

# health
curl http://localhost:8000/healthz
curl http://localhost:8000/readyz
```
