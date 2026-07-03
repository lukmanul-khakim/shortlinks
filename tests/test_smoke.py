"""
Smoke test: cek fungsi-fungsi inti app masih hidup. BUKAN unit test lengkap.
Butuh Postgres + Redis beneran jalan (readyz, create, redirect nyentuh keduanya).
Di CI: sediain lewat `services:` di job, set DATABASE_URL & REDIS_URL, baru pytest.
"""


def test_healthz(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_readyz(client):
    r = client.get("/readyz")
    assert r.status_code == 200
    assert r.json()["status"] == "ready"


def test_create_link(client):
    r = client.post("/api/links", json={"url": "https://example.com"})
    assert r.status_code == 201
    body = r.json()
    assert body["short_code"]
    assert body["original_url"].startswith("https://example.com")


def test_create_link_rejects_bad_url(client):
    r = client.post("/api/links", json={"url": "not-a-url"})
    assert r.status_code == 422


def test_redirect_and_click_count(client):
    code = client.post(
        "/api/links", json={"url": "https://example.com"}
    ).json()["short_code"]

    r1 = client.get(f"/{code}", follow_redirects=False)
    assert r1.status_code == 302
    assert r1.headers["location"].startswith("https://example.com")

    client.get(f"/{code}", follow_redirects=False)  # klik kedua

    stats = client.get(f"/api/links/{code}/stats").json()
    assert stats["clicks"] >= 2


def test_unknown_code_stats_404(client):
    r = client.get("/api/links/doesnotexist/stats")
    assert r.status_code == 404
