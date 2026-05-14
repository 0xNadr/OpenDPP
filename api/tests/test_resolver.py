async def _seed(client, textile_dpp_data, *, gtin="07350053850010", lot="ATL-2026-T01"):
    p = await client.post("/api/products", json={"gtin": gtin, "name": "Atelier Tee"})
    await client.post(
        "/api/dpp",
        json={"product_id": p.json()["id"], "lot": lot, "data": textile_dpp_data},
    )


async def test_resolver_returns_html_by_default(client, textile_dpp_data):
    await _seed(client, textile_dpp_data)
    r = await client.get("/01/07350053850010/10/ATL-2026-T01")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]


async def test_resolver_returns_jsonld_on_accept(client, textile_dpp_data):
    await _seed(client, textile_dpp_data)
    r = await client.get(
        "/01/07350053850010/10/ATL-2026-T01",
        headers={"Accept": "application/ld+json"},
    )
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("application/ld+json")
    body = r.json()
    assert "@context" in body
    assert body["identification"]["gtin"] == "07350053850010"


async def test_resolver_404_on_unknown_gtin(client):
    r = await client.get("/01/99999999999999")
    assert r.status_code == 404


async def test_resolver_view_and_lang_query_params_accepted(client, textile_dpp_data):
    await _seed(client, textile_dpp_data)
    for view in ("consumer", "recycler", "regulator"):
        for lang in ("en", "de", "fr", "ar"):
            r = await client.get(
                f"/01/07350053850010/10/ATL-2026-T01?view={view}&lang={lang}"
            )
            assert r.status_code == 200, (view, lang, r.text)
