import re


def normalise_spaces(text: str) -> str:
    """Intl number formats use NBSP / narrow NBSP as group separators; normalise for assertions."""
    return re.sub(r"[  ]", " ", text).strip()
