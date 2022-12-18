"""Utility methods"""
import collections
import re
import unicodedata


def merge_dict(base_dict, new_dict):
    """Merges new_dict into base_dict."""
    for key, value in new_dict.items():
        if key in base_dict:
            old_value = base_dict[key]
            if isinstance(old_value, collections.abc.MutableMapping):
                # Combine dictionary
                assert isinstance(
                    value, collections.abc.Mapping
                ), f"Not a dict: {value}"
                merge_dict(old_value, value)
            elif isinstance(old_value, collections.abc.MutableSequence):
                # Combine list
                assert isinstance(
                    value, collections.abc.Sequence
                ), f"Not a list: {value}"
                old_value.extend(value)
            else:
                # Overwrite
                base_dict[key] = value
        else:
            base_dict[key] = value


def remove_escapes(text: str) -> str:
    """Remove backslash escape sequences."""
    return re.sub(r"\\(.)", r"\1", text)


def remove_quotes(text: str) -> str:
    """Remove double quotes."""
    if (len(text) > 1) and (text[0] == '"') and (text[-1] == '"'):
        text = text[1:-1]

    return text


def normalize_whitespace(text: str) -> str:
    """Makes all whitespace inside a string single spaced."""
    return " ".join(text.split())


def normalize_text(text: str) -> str:
    """Normalize whitespace and unicode forms."""
    text = normalize_whitespace(text)
    text = text.casefold()
    text = unicodedata.normalize("NFC", text)

    return text
