from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Sengaja TIDAK baca .env file di dalam app.
    # Di container, config harus datang dari environment beneran.
    model_config = SettingsConfigDict(env_file=None, case_sensitive=False)

    # --- WAJIB ADA (tidak ada default) -> app crash kalau kosong ---
    database_url: str
    redis_url: str

    # --- Opsional (ada default) ---
    app_port: int = 8000
    base_url: str = "http://localhost:8000"
    rate_limit_per_minute: int = 20
    short_code_length: int = 7


# Di-instantiate saat import -> kalau DATABASE_URL / REDIS_URL kosong,
# app langsung gagal start dengan error yang jelas. Ini disengaja.
settings = Settings()
