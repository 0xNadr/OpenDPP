"""QR code generation for GS1 Digital Link URIs.

Returns a QR image encoding the canonical product URL. The URL is built from
the configured `base_url` (or the request's host) so the printed QR points at
wherever this OpenDPP instance is served.
"""

import io
from typing import Literal

import qrcode
import qrcode.image.svg
from fastapi import APIRouter, Query, Request
from fastapi.responses import Response

router = APIRouter(prefix="/api/qr", tags=["qr"])

Format = Literal["svg", "png"]


def _digital_link_path(gtin: str, lot: str | None = None, serial: str | None = None) -> str:
    parts = [f"/01/{gtin}"]
    if lot is not None:
        parts.append(f"/10/{lot}")
    if serial is not None:
        parts.append(f"/21/{serial}")
    return "".join(parts)


def _render(uri: str, fmt: Format, box_size: int) -> Response:
    if fmt == "svg":
        img = qrcode.make(
            uri,
            image_factory=qrcode.image.svg.SvgPathImage,
            box_size=box_size,
            border=2,
        )
        buf = io.BytesIO()
        img.save(buf)
        return Response(content=buf.getvalue(), media_type="image/svg+xml")

    img = qrcode.make(uri, box_size=box_size, border=2)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return Response(content=buf.getvalue(), media_type="image/png")


def _canonical_url(request: Request, path: str) -> str:
    base = str(request.base_url).rstrip("/")
    return f"{base}{path}"


@router.api_route(methods=["GET", "HEAD"], path="/01/{gtin}")
def qr_gtin(
    gtin: str,
    request: Request,
    format: Format = Query(default="svg"),
    size: int = Query(default=8, ge=2, le=32),
) -> Response:
    uri = _canonical_url(request, _digital_link_path(gtin))
    return _render(uri, format, size)


@router.api_route(methods=["GET", "HEAD"], path="/01/{gtin}/10/{lot}")
def qr_gtin_lot(
    gtin: str,
    lot: str,
    request: Request,
    format: Format = Query(default="svg"),
    size: int = Query(default=8, ge=2, le=32),
) -> Response:
    uri = _canonical_url(request, _digital_link_path(gtin, lot=lot))
    return _render(uri, format, size)


@router.api_route(methods=["GET", "HEAD"], path="/01/{gtin}/10/{lot}/21/{serial}")
def qr_gtin_lot_serial(
    gtin: str,
    lot: str,
    serial: str,
    request: Request,
    format: Format = Query(default="svg"),
    size: int = Query(default=8, ge=2, le=32),
) -> Response:
    uri = _canonical_url(request, _digital_link_path(gtin, lot=lot, serial=serial))
    return _render(uri, format, size)
