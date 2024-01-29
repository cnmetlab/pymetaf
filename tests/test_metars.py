from pymetaf import parse_text, get_field_text
from .case.metar import GET_FIELD_TEXT_CASE, PARSE_TEXT_CASE


def test_get_field_text():
    for gft in GET_FIELD_TEXT_CASE:
        result = get_field_text(**gft["kwargs"])
        assert result == gft["result"]


def test_parse_text():
    for ptc in PARSE_TEXT_CASE:
        result = parse_text(**ptc["kwargs"])
        assert result == ptc["result"]
