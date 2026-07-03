import secrets
import string

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from .cache import r
from .config import settings
from .db import SessionLocal, engine
from .models import Link
from .schemas import CreateLinkRequest, LinkResponse, StatsResponse

app = FastAPI(title="ShortLink API", version="1.0.0")

ALPHABET = string.ascii_letters + string.digits


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def gen_code(n: int) -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(n))


def check_rate_limit(ip: str) -> None:
    """Batasi jumlah pembuatan link per IP per menit, pakai Redis."""
    key = f"ratelimit:create:{ip}"
    current = r.incr(key)
    if current == 1:
        r.expire(key, 60)
    if current > settings.rate_limit_per_minute:
        raise HTTPException(status_code=429, detail="Rate limit exceeded, coba lagi nanti")


# --- Health endpoints ---

@app.get("/healthz")
def healthz():
    """Liveness: app hidup atau nggak. TIDAK ngecek dependency."""
    return {"status": "ok"}


@app.get("/readyz")
def readyz():
    """Readiness: app siap nerima traffic? Cek DB + Redis."""
    try:
        with engine.connect() as conn:
            conn.exec_driver_sql("SELECT 1")
    except Exception:
        raise HTTPException(status_code=503, detail="database not ready")
    try:
        r.ping()
    except Exception:
        raise HTTPException(status_code=503, detail="redis not ready")
    return {"status": "ready"}


# --- API ---

@app.post("/api/links", response_model=LinkResponse, status_code=201)
def create_link(
    payload: CreateLinkRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    check_rate_limit(request.client.host)

    code = gen_code(settings.short_code_length)
    for _ in range(5):  # retry kalau bentrok (sangat jarang)
        exists = db.execute(
            select(Link).where(Link.short_code == code)
        ).scalar_one_or_none()
        if not exists:
            break
        code = gen_code(settings.short_code_length)

    link = Link(short_code=code, original_url=str(payload.url))
    db.add(link)
    db.commit()

    r.set(f"link:{code}", str(payload.url), ex=3600)

    return LinkResponse(
        short_code=code,
        short_url=f"{settings.base_url}/{code}",
        original_url=str(payload.url),
    )


@app.get("/api/links/{short_code}/stats", response_model=StatsResponse)
def stats(short_code: str, db: Session = Depends(get_db)):
    link = db.execute(
        select(Link).where(Link.short_code == short_code)
    ).scalar_one_or_none()
    if not link:
        raise HTTPException(status_code=404, detail="link not found")
    return StatsResponse(
        short_code=link.short_code,
        original_url=link.original_url,
        clicks=link.clicks,
    )


# Catch-all 1-segmen. WAJIB di-declare paling bawah biar nggak nelan
# /healthz, /readyz, /api/...
@app.get("/{short_code}")
def redirect(short_code: str, db: Session = Depends(get_db)):
    url = r.get(f"link:{short_code}")  # cache dulu
    if not url:
        link = db.execute(
            select(Link).where(Link.short_code == short_code)
        ).scalar_one_or_none()
        if not link:
            raise HTTPException(status_code=404, detail="link not found")
        url = link.original_url
        r.set(f"link:{short_code}", url, ex=3600)

    db.execute(
        Link.__table__.update()
        .where(Link.short_code == short_code)
        .values(clicks=Link.clicks + 1)
    )
    db.commit()

    return RedirectResponse(url=url, status_code=302)
