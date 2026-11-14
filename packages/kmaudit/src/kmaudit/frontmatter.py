"""Read a markdown file's YAML front matter, so kmaudit needs nothing from kmctl to read a page."""

from typing import Any

import yaml


class BadFrontMatter(Exception):
    """A page whose front matter is not readable YAML."""


def split_front_matter(text: str) -> tuple[dict[str, Any], str]:
    """The YAML front matter of a page's ``text`` (empty when it has none) and the text after it.

    Raises
    ------
    BadFrontMatter
        When the front matter does not parse.
    """
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end == -1:
        return {}, text
    try:
        data = yaml.safe_load(text[4:end])
    except yaml.YAMLError as error:
        raise BadFrontMatter(
            f"front matter does not parse ({error.__class__.__name__})"
        ) from error
    return (data if isinstance(data, dict) else {}), text[end:]


def field(meta: dict[str, Any], path: str, default: Any = None) -> Any:
    """Read one front matter key by path.

    ``a`` reads a key, ``a.b`` a key of a mapping, and ``a[].b`` returns a list
    with ``b`` of each item; in ``sources`` a plain string item is its own
    resource. Any other non-list reads as ``[]``. Missing values give
    ``default`` (or ``[]`` for a list path).
    """
    if "[]." in path:
        head, sub = path.split("[].", 1)
        value = meta.get(head)
        items = value if isinstance(value, list) else []
        out = []
        for item in items:
            if isinstance(item, dict) and item.get(sub) is not None:
                out.append(item[sub])
            elif isinstance(item, str) and head == "sources":
                out.append(item)
        return out
    if "." in path:
        head, sub = path.split(".", 1)
        value = meta.get(head)
        return value.get(sub, default) if isinstance(value, dict) else default
    return meta.get(path, default)
