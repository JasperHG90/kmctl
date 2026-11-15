"""Read a list a model sent as JSON text instead of as a list."""

import json
from typing import Any

STRAY = set("]}") | set(" \t\r\n")


def read_list(value: Any) -> Any:
    """Return the list in ``value`` when it is JSON text, else ``value`` unchanged for validation to judge.

    Some models send a list argument as a string, and some close that string with a stray bracket or brace (seen on
    DeepSeek: 13 sentences, then ``]}``). The list is read up to its own end; anything after it other than closing
    brackets and whitespace means the text is not one list, and it is left as it is.
    """
    if not isinstance(value, str):
        return value
    text = value.strip()
    try:
        found, end = json.JSONDecoder().raw_decode(text)
    except json.JSONDecodeError:
        return value
    if not isinstance(found, list) or not set(text[end:]) <= STRAY:
        return value
    return found
