"""JSON-LD context for OpenDPP responses.

Aligns OpenDPP field names to the GS1 Web Vocabulary where applicable.
Reference: https://www.gs1.org/voc/
"""

GS1_VOCAB = "https://gs1.org/voc/"

DPP_CONTEXT: dict = {
    "@vocab": "https://opendpp.org/vocab/",
    "gs1": GS1_VOCAB,
    "schema": "https://schema.org/",
    "gtin": "gs1:gtin",
    "brand": "gs1:brand",
    "productName": "gs1:productName",
    "model": "gs1:model",
    "countryOfManufacture": "gs1:countryOfOrigin",
    "manufacturingDate": "gs1:productionDate",
}


def wrap_jsonld(data: dict, *, id_uri: str | None = None, types: list[str] | None = None) -> dict:
    """Wrap a DPP data dict with JSON-LD context and metadata."""
    doc = {
        "@context": DPP_CONTEXT,
        "@type": types or ["gs1:Product", "DigitalProductPassport"],
    }
    if id_uri:
        doc["@id"] = id_uri
    doc.update(data)
    return doc
