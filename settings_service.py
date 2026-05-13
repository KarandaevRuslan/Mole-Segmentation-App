import json
from dataclasses import asdict, dataclass
from pathlib import Path

from ui_manager import ThemeId


SETTINGS_PATH = Path(__file__).resolve().parent / "settings.json"
DEFAULT_STYLE = "Fusion"
DEFAULT_THEME = ThemeId.SYSTEM.value
DEFAULT_LANGUAGE = "en"


@dataclass
class AppSettings:
    style: str = DEFAULT_STYLE
    theme: str = DEFAULT_THEME
    language: str = DEFAULT_LANGUAGE


class SettingsService:
    def __init__(self, path: Path = SETTINGS_PATH):
        self.path = path

    def load(self) -> AppSettings:
        if not self.path.exists():
            return AppSettings()

        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return AppSettings(
                style=data.get("style", DEFAULT_STYLE),
                theme=data.get("theme", DEFAULT_THEME),
                language=data.get("language", DEFAULT_LANGUAGE),
            )
        except Exception:
            return AppSettings()

    def save(self, settings: AppSettings):
        self.path.write_text(
            json.dumps(asdict(settings), indent=4, ensure_ascii=False),
            encoding="utf-8"
        )
