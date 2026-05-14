from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from opendpp.db import Base, get_session
from opendpp.main import app


@pytest_asyncio.fixture
async def engine():
    eng = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield eng
    finally:
        await eng.dispose()


@pytest_asyncio.fixture
async def session_factory(engine):
    return async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


@pytest_asyncio.fixture
async def client(session_factory) -> AsyncIterator[AsyncClient]:
    async def override_get_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def textile_dpp_data() -> dict:
    return {
        "schemaVersion": "textile-dpp.v1",
        "identification": {
            "gtin": "07350053850010",
            "lot": "ATL-2026-T01",
            "brand": "Atelier",
            "productName": "Atelier Organic Cotton Tee",
        },
        "composition": {
            "materials": [{"name": "Organic Cotton", "percentage": 100}],
        },
        "origin": {"countryOfManufacture": "PT"},
        "manufacturing": {"manufacturingDate": "2026-02-12"},
        "compliance": {"certifications": []},
        "lifecycleGuidance": {
            "careInstructions": ["Wash at 30C"],
            "endOfLifeOptions": ["recycle"],
        },
        "authority": {
            "economicOperator": {"name": "Atelier Textiles SA", "country": "PT"},
        },
    }
