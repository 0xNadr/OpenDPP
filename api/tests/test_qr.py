async def test_qr_svg_default(client):
    r = await client.get("/api/qr/01/07350053850010")
    assert r.status_code == 200
    assert r.headers["content-type"] == "image/svg+xml"
    assert b"<svg" in r.content


async def test_qr_png_format(client):
    r = await client.get("/api/qr/01/07350053850010?format=png")
    assert r.status_code == 200
    assert r.headers["content-type"] == "image/png"
    # PNG magic bytes
    assert r.content[:8] == b"\x89PNG\r\n\x1a\n"


async def test_qr_with_lot_and_serial(client):
    r = await client.get("/api/qr/01/07350053850034/10/SOR-2026-J03/21/SOR-J03-000142")
    assert r.status_code == 200
    assert b"<svg" in r.content


async def test_qr_rejects_invalid_size(client):
    r = await client.get("/api/qr/01/07350053850010?size=999")
    assert r.status_code == 422
