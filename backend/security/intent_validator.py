"""
Destructive Intent Detection

This module detects user requests that express destructive intent
in natural language, BEFORE they reach clarification or SQL generation.

Purpose:
    - Reject DELETE, DROP, UPDATE, INSERT requests phrased naturally
    - Prevent clarification questions that would help execute destruction
    - Complement the SQL validator (which validates generated SQL syntax)

Examples of rejected requests:
    - "Delete the first row"
    - "Remove all customers from Mumbai"
    - "Drop the orders table"
    - "Update customer emails"
    - "Insert a new product"
    - "Clear all data"

This is an early-stage safety check. The SQL validator remains
the mandatory final security layer that validates actual SQL syntax.
"""

import re


# ============================================================
# Destructive Intent Patterns
#
# These patterns match natural language expressions of
# destructive operations. They are intentionally broad to
# catch variations and misspellings.
#
# Pattern rules:
#   - Case-insensitive matching
#   - Word boundaries (\b) to avoid false positives
#   - Matches both "verb + noun" and "noun + verb" orders
# ============================================================

DESTRUCTIVE_PATTERNS = [
    # DELETE operations (broad matching)
    r"\b(delete|remove|erase|clear|wipe|purge|destroy)\b",
    
    # DROP operations
    r"\b(drop)\b.*\b(table|database|schema|index|view)\b",
    r"\b(table|database|schema|index|view)\b.*\b(drop)\b",
    
    # UPDATE operations (with context)
    r"\b(update|modify|change|edit|alter)\b.*\b(customer|product|order|user|price|email|name|data|field|column|value|record|row|entry)\b",
    r"\b(set)\b.*\b(to|=)\b",  # "set price to 100" or "set email = ..."
    
    # INSERT operations (with "new" or "add")
    r"\b(insert|add|create|append)\b.*\b(new|another|a)\b",
    r"\b(new|another)\b.{0,30}\b(customer|product|order|user|row|entry|record)\b",
    
    # TRUNCATE/RESET operations
    r"\b(truncate|empty|reset)\b.*\b(table|data|database|all)\b",
    r"\b(table|data)\b.*\b(truncate|empty|reset)\b",
    
    # Generic destructive verbs (require destructive context)
    r"\b(destroy|obliterate|nuke|trash)\b",
    
    # "Get rid of" phrase
    r"\bget\s+rid\s+of\b",
]


def is_destructive_intent(question: str) -> tuple[bool, str]:
    """
    Detect whether a natural language question expresses
    destructive intent (DELETE, DROP, UPDATE, INSERT, etc.).

    Parameters
    ----------
    question : str
        User's natural language question.

    Returns
    -------
    (True, reason)   — destructive intent detected; reason explains why
    (False, "")      — no destructive intent; safe to proceed

    Examples
    --------
    >>> is_destructive_intent("Show me all customers")
    (False, "")

    >>> is_destructive_intent("Delete the first row")
    (True, "Request contains destructive operation: delete")

    >>> is_destructive_intent("Remove customers from Mumbai")
    (True, "Request contains destructive operation: remove")

    >>> is_destructive_intent("Update customer email addresses")
    (True, "Request contains destructive operation: update")

    >>> is_destructive_intent("Add a new product to the catalog")
    (True, "Request contains destructive operation: insert/add")
    """

    if not question or not question.strip():
        return False, ""

    question_lower = question.lower().strip()

    # Check each destructive pattern
    for pattern in DESTRUCTIVE_PATTERNS:
        match = re.search(pattern, question_lower, re.IGNORECASE)
        if match:
            # Extract the destructive verb from the match
            matched_text = match.group(0)
            
            # Common destructive verbs for clear error messages
            if any(word in matched_text for word in ["delete", "remove", "erase", "clear", "wipe", "purge", "destroy"]):
                verb = "delete/remove"
            elif any(word in matched_text for word in ["drop"]):
                verb = "drop"
            elif any(word in matched_text for word in ["update", "modify", "change", "edit", "alter", "set"]):
                verb = "update/modify"
            elif any(word in matched_text for word in ["insert", "add", "create", "append"]):
                verb = "insert/add"
            elif any(word in matched_text for word in ["truncate", "empty"]):
                verb = "truncate"
            else:
                verb = "destructive operation"
            
            return True, (
                f"This application only supports read-only SELECT queries. "
                f"Requests to {verb} data are not allowed."
            )

    return False, ""
