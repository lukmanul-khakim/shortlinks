"""
Migration sederhana: bikin tabel kalau belum ada.

Jalanin sebagai langkah terpisah SEBELUM app start:
    python scripts/migrate.py

Di dunia DevOps lu, ini langkah yang nanti jadi:
  - service one-shot di docker-compose (depends_on), atau
  - init container / Job di Kubernetes, atau
  - step di pipeline CI/CD sebelum deploy.

Sengaja dipisah dari app start biar lu kepikiran soal urutan init.
"""
import os
import sys

# biar 'import app.*' jalan walaupun script dipanggil dari mana aja
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import Base, engine  # noqa: E402
from app import models  # noqa: E402,F401  (import biar tabel keregister di metadata)


def main():
    print("[migrate] creating tables if not exist...")
    Base.metadata.create_all(bind=engine)
    print("[migrate] done.")


if __name__ == "__main__":
    main()
