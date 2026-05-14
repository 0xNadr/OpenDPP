from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from opendpp.content_negotiation import JSONLD_MEDIA_TYPE, prefers_jsonld
from opendpp.db import get_session
from opendpp.jsonld.context import wrap_jsonld
from opendpp.models import DPPRecord, Product

router = APIRouter(tags=["resolver"])

View = Literal["consumer", "recycler", "regulator"]
Lang = Literal["en", "de", "fr", "ar"]


async def _resolve(
    session: AsyncSession,
    gtin: str,
    lot: str | None = None,
    serial: str | None = None,
) -> DPPRecord:
    stmt = (
        select(DPPRecord)
        .join(Product, DPPRecord.product_id == Product.id)
        .where(Product.gtin == gtin)
    )
    if lot is not None:
        stmt = stmt.where(DPPRecord.lot == lot)
    else:
        stmt = stmt.where(DPPRecord.lot.is_(None))
    if serial is not None:
        stmt = stmt.where(DPPRecord.serial == serial)
    else:
        stmt = stmt.where(DPPRecord.serial.is_(None))

    record = (await session.execute(stmt)).scalar_one_or_none()
    if record is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "DPP record not found")
    return record


def _render_response(
    request: Request,
    record: DPPRecord,
    view: View,
    lang: Lang,
) -> JSONResponse | HTMLResponse:
    canonical_id = str(request.url.remove_query_params(["view", "lang"]))
    if prefers_jsonld(request):
        body = wrap_jsonld(record.data, id_uri=canonical_id)
        return JSONResponse(content=body, media_type=JSONLD_MEDIA_TYPE)
    # HTML placeholder until Phase 2 viewer ships.
    html = (
        "<!doctype html>"
        f"<title>OpenDPP — {view} view</title>"
        f"<h1>OpenDPP — {view} view ({lang})</h1>"
        f"<p>Viewer for {canonical_id} ships in Phase 2.</p>"
        f"<p>Request <code>Accept: {JSONLD_MEDIA_TYPE}</code> for the JSON-LD payload.</p>"
    )
    return HTMLResponse(content=html)


@router.api_route(methods=["GET", "HEAD"], path="/01/{gtin}", response_model=None, include_in_schema=True)
async def resolve_gtin(
    gtin: str,
    request: Request,
    view: View = Query(default="consumer"),
    lang: Lang = Query(default="en"),
    session: AsyncSession = Depends(get_session),
) -> JSONResponse | HTMLResponse:
    record = await _resolve(session, gtin)
    return _render_response(request, record, view, lang)


@router.api_route(methods=["GET", "HEAD"], path="/01/{gtin}/10/{lot}", response_model=None, include_in_schema=True)
async def resolve_gtin_lot(
    gtin: str,
    lot: str,
    request: Request,
    view: View = Query(default="consumer"),
    lang: Lang = Query(default="en"),
    session: AsyncSession = Depends(get_session),
) -> JSONResponse | HTMLResponse:
    record = await _resolve(session, gtin, lot=lot)
    return _render_response(request, record, view, lang)


@router.api_route(methods=["GET", "HEAD"], path="/01/{gtin}/10/{lot}/21/{serial}", response_model=None, include_in_schema=True)
async def resolve_gtin_lot_serial(
    gtin: str,
    lot: str,
    serial: str,
    request: Request,
    view: View = Query(default="consumer"),
    lang: Lang = Query(default="en"),
    session: AsyncSession = Depends(get_session),
) -> JSONResponse | HTMLResponse:
    record = await _resolve(session, gtin, lot=lot, serial=serial)
    return _render_response(request, record, view, lang)
