import pytest

from backend.agents.clarification import (
    parse_clarification_response
)


def test_valid_clear_response():

    response = """
    {
        "needs_clarification": false,
        "clarification_question": "",
        "suggestions": []
    }
    """

    result = parse_clarification_response(response)

    assert result["needs_clarification"] is False
    assert result["clarification_question"] == ""
    assert result["suggestions"] == []


def test_valid_ambiguous_response():

    response = """
    {
        "needs_clarification": true,
        "clarification_question": "What do you mean by best customer?",
        "suggestions": [
            "Highest revenue",
            "Most orders"
        ]
    }
    """

    result = parse_clarification_response(response)

    assert result["needs_clarification"] is True
    assert len(result["suggestions"]) == 2


def test_invalid_json():

    response = """
    This is not JSON
    """

    with pytest.raises(ValueError):

        parse_clarification_response(response)


def test_missing_field():

    response = """
    {
        "needs_clarification": false
    }
    """

    with pytest.raises(ValueError):

        parse_clarification_response(response)


def test_invalid_boolean():

    response = """
    {
        "needs_clarification": "true",
        "clarification_question": "What do you mean?",
        "suggestions": ["Option 1"]
    }
    """

    with pytest.raises(ValueError):

        parse_clarification_response(response)