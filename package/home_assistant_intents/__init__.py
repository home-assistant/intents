import json
import os
import typing
from pathlib import Path
from typing import Any, Dict, Optional

import importlib.resources

_PACKAGE = "home_assistant_intents"
_DIR = Path(typing.cast(os.PathLike, importlib.resources.files(_PACKAGE)))
_DATA_DIR = _DIR / "data"


def get_intents(domain: str, language: str) -> Optional[Dict[str, Any]]:
    """Load intents by domain/language."""
    intents_path = _DATA_DIR / domain / f"{language}.json"
    if intents_path.exists():
        with intents_path.open(encoding="utf-8") as intents_file:
            return json.load(intents_file)

    return None
