"""Constants."""

from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
SENTENCE_DIR = ROOT / "sentences"
RESPONSE_DIR = ROOT / "responses"
TESTS_DIR = ROOT / "tests"
LANGUAGES_FILE = ROOT / "languages.yaml"
INTENTS_FILE = ROOT / "intents.yaml"
LANGUAGES = sorted(p.name for p in SENTENCE_DIR.iterdir() if p.is_dir())
IMPORTANT_INTENTS = {
    "HassTurnOn",
    "HassTurnOff",
    "HassNevermind",
    "HassLightSet",
    "HassClimateGetTemperature",
    "HassListAddItem",
    "HassStartTimer",
    "HassCancelTimer",
    "HassTimerStatus",
}
