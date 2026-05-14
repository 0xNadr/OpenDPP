from fastapi import Request

JSONLD_MEDIA_TYPE = "application/ld+json"
JSON_MEDIA_TYPE = "application/json"
HTML_MEDIA_TYPE = "text/html"


def prefers_jsonld(request: Request) -> bool:
    """Return True if the client prefers JSON-LD (or generic JSON) over HTML."""
    accept = request.headers.get("accept", "").lower()
    if not accept or "*/*" in accept:
        return False
    if JSONLD_MEDIA_TYPE in accept or JSON_MEDIA_TYPE in accept:
        # If both JSON and HTML are present, prefer the first explicit listing.
        if HTML_MEDIA_TYPE in accept:
            return accept.index(JSON_MEDIA_TYPE.split("/")[0]) < accept.index("html")
        return True
    return False
