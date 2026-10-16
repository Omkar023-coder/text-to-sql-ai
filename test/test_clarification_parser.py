import pytest

from backend.agents.clarification import (
    parse_clarification_response,
    extract_json
)


# ============================================================
# extract_json tests
# ============================================================

def test_extract_json_clean():
    text = '{"needs_clarification": false, "clarification_question": "", "suggestions": []}'
    assert extract_json(text) == text


def test_extract_json_with_fences():
    text = '```json\n{"needs_clarification": false, "clarification_question": "", "suggestions": []}\n```'
    result = extract_json(text)
    assert result.startswith("{")
    assert result.endswith("}")


def test_extract_json_with_prose_before():
    text = 'Here is my answer:\n{"needs_clarification": true, "clarification_question": "What do you mean?", "suggestions": ["Option 1"]}'
    result = extract_json(text)
    assert result.startswith("{")
    assert '"needs_clarification"' in result


def test_extract_json_with_prose_around():
    text = 'The question is ambiguous. {"needs_clarification": true, "clarification_question": "Clarify?", "suggestions": ["A"]} Hope this helps.'
    result = extract_json(text)
    assert result.startswith("{")
    assert result.endswith("}")


def test_extract_json_empty_string():
    result = extract_json("")
    assert result == ""


def test_extract_json_no_json():
    result = extract_json("This is just plain text with no JSON.")
    assert result == ""


# ============================================================
# parse_clarification_response — valid responses
# ============================================================

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


def test_response_with_markdown_fences():
    """LLM wraps JSON in markdown code fences."""

    response = """```json
{
    "needs_clarification": true,
    "clarification_question": "What do you mean by best?",
    "suggestions": ["Highest revenue", "Most orders"]
}
```"""

    result = parse_clarification_response(response)

    assert result["needs_clarification"] is True
    assert len(result["suggestions"]) == 2


def test_response_with_prose_before_json():
    """LLM writes explanation before the JSON block."""

    response = """The question is ambiguous. Here is my response:
{
    "needs_clarification": true,
    "clarification_question": "What do you mean by best customer?",
    "suggestions": ["Highest revenue", "Most orders"]
}"""

    result = parse_clarification_response(response)

    assert result["needs_clarification"] is True
    assert result["clarification_question"] == "What do you mean by best customer?"


def test_response_with_extra_whitespace():
    """LLM adds extra blank lines and spaces."""

    response = """


    {
        "needs_clarification": false,
        "clarification_question": "",
        "suggestions": []
    }


    """

    result = parse_clarification_response(response)

    assert result["needs_clarification"] is False


# ============================================================
# parse_clarification_response — fallback behavior
# (invalid/non-JSON responses must NOT crash)
# ============================================================

def test_empty_response_returns_fallback():
    """Empty string returns safe clarification_required fallback."""

    result = parse_clarification_response("")

    assert result["needs_clarification"] is True
    assert len(result["suggestions"]) > 0
    assert isinstance(result["clarification_question"], str)


def test_pure_prose_returns_fallback():
    """Plain prose with no JSON returns safe fallback."""

    response = "The question is ambiguous. Please clarify what you mean."

    result = parse_clarification_response(response)

    assert result["needs_clarification"] is True
    assert len(result["suggestions"]) > 0


def test_none_like_response_returns_fallback():
    """Whitespace-only response returns safe fallback."""

    result = parse_clarification_response("   \n\n   ")

    assert result["needs_clarification"] is True
    assert len(result["suggestions"]) > 0


# ============================================================
# parse_clarification_response — structural errors still raise
# ============================================================

def test_missing_field_returns_safe_fallback():
    """
    JSON with missing required field returns safe fallback with
    generic suggestions rather than raising ValueError.
    """
    response = '{"needs_clarification": false}'
    result = parse_clarification_response(response)
    # Should not raise; should return a valid response
    assert "needs_clarification" in result
    assert isinstance(result["needs_clarification"], bool)


def test_invalid_boolean_returns_safe_fallback():
    """
    String instead of bool for needs_clarification returns safe
    fallback (treating as clear) rather than raising ValueError.
    """
    response = """
    {
        "needs_clarification": "true",
        "clarification_question": "What do you mean?",
        "suggestions": ["Option 1"]
    }
    """
    result = parse_clarification_response(response)
    # Should not raise; should treat as clear
    assert result["needs_clarification"] is False


def test_ambiguous_with_no_suggestions_adds_generic_suggestions():
    """
    needs_clarification=true but empty suggestions adds generic
    suggestions rather than raising ValueError.
    """
    response = """
    {
        "needs_clarification": true,
        "clarification_question": "What do you mean?",
        "suggestions": []
    }
    """
    result = parse_clarification_response(response)
    # Should not raise; should add generic suggestions
    assert result["needs_clarification"] is True
    assert len(result["suggestions"]) >= 1
