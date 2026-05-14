from opendpp.validation import validate_dpp_data


def test_minimal_valid_textile_dpp(textile_dpp_data):
    assert validate_dpp_data("textile-dpp.v1", textile_dpp_data) == []


def test_bad_gtin_rejected(textile_dpp_data):
    bad = dict(textile_dpp_data)
    bad["identification"] = dict(textile_dpp_data["identification"])
    bad["identification"]["gtin"] = "abc"
    errors = validate_dpp_data("textile-dpp.v1", bad)
    assert len(errors) >= 1


def test_missing_required_field_rejected(textile_dpp_data):
    bad = dict(textile_dpp_data)
    bad.pop("authority")
    errors = validate_dpp_data("textile-dpp.v1", bad)
    assert any("authority" in str(e.path) or "authority" in e.message for e in errors)
