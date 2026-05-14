async def _create_product(client, gtin: str = "07350053850010"):
    r = await client.post(
        "/api/products",
        json={"gtin": gtin, "name": "Atelier Tee", "manufacturer": "Atelier"},
    )
    assert r.status_code == 201, r.text
    return r.json()


async def test_create_product(client):
    product = await _create_product(client)
    assert product["gtin"] == "07350053850010"


async def test_create_product_duplicate_gtin_conflicts(client):
    await _create_product(client)
    r = await client.post(
        "/api/products", json={"gtin": "07350053850010", "name": "dup"}
    )
    assert r.status_code == 409


async def test_create_dpp_happy_path(client, textile_dpp_data):
    product = await _create_product(client)
    r = await client.post(
        "/api/dpp",
        json={
            "product_id": product["id"],
            "lot": "ATL-2026-T01",
            "schema_version": "textile-dpp.v1",
            "data": textile_dpp_data,
        },
    )
    assert r.status_code == 201, r.text
    assert r.json()["lot"] == "ATL-2026-T01"


async def test_create_dpp_rejects_invalid_data(client, textile_dpp_data):
    product = await _create_product(client)
    bad = dict(textile_dpp_data)
    bad["identification"] = dict(textile_dpp_data["identification"])
    bad["identification"]["gtin"] = "not-a-gtin"
    r = await client.post(
        "/api/dpp",
        json={"product_id": product["id"], "data": bad},
    )
    assert r.status_code == 422


async def test_create_dpp_requires_existing_product(client, textile_dpp_data):
    r = await client.post(
        "/api/dpp",
        json={
            "product_id": "00000000-0000-0000-0000-000000000000",
            "data": textile_dpp_data,
        },
    )
    assert r.status_code == 404


async def test_list_dpp_returns_created_records(client, textile_dpp_data):
    product = await _create_product(client)
    await client.post(
        "/api/dpp",
        json={"product_id": product["id"], "lot": "ATL-2026-T01", "data": textile_dpp_data},
    )
    r = await client.get("/api/dpp")
    assert r.status_code == 200
    assert len(r.json()) >= 1
