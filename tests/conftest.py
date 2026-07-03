import os

# App sengaja fail-fast tanpa env ini, jadi HARUS di-set sebelum import app.
# Di CI, nilai ini di-override lewat env yang nunjuk ke service container
# (Postgres & Redis) yang lu sediain di job.
os.environ.setdefault(
    "DATABASE_URL", "postgresql+psycopg2://shortlink:shortlink@localhost:5432/shortlink"
)
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.db import Base, engine  # noqa: E402
from app import models  # noqa: E402,F401  (import biar tabel keregister di metadata)
from app.main import app  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _setup_db():
    # Bikin tabel di DB test — setara langkah migrate lu.
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def client():
    return TestClient(app)
