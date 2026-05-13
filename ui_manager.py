from enum import Enum
from pathlib import Path
import sys

import qdarktheme

from PyQt5.QtCore import QTranslator
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QStyleFactory

from typing import TYPE_CHECKING

from config import APP_ICON_PATH

if TYPE_CHECKING:
    from settings_service import AppSettings


TRANSLATIONS_DIR = Path(__file__).resolve().parent / "translations"


class ThemeId(str, Enum):
    SYSTEM = "system"
    LIGHT = "light"
    DARK = "dark"


def theme_display_name(theme: ThemeId, tr) -> str:
    names = {
        ThemeId.SYSTEM: tr("System"),
        ThemeId.LIGHT: tr("Light"),
        ThemeId.DARK: tr("Dark"),
    }

    return names[theme]


class StyleManager:
    def __init__(self, app: QApplication):
        self.app = app

    def apply(self, style_name: str):
        available_styles = {
            style.lower(): style
            for style in QStyleFactory.keys()
        }

        key = style_name.lower()

        if key in available_styles:
            self.app.setStyle(available_styles[key])

    def available_styles(self) -> list[str]:
        return QStyleFactory.keys()


class ThemeManager:
    def __init__(self, app: QApplication):
        self.app = app
        self.default_stylesheet = app.styleSheet()
        self.default_palette = app.palette()

    def apply(self, theme: str):
        theme_id = self._normalize_theme(theme)
        resolved_theme_id = self._resolve_theme(theme_id)

        self.app.setPalette(self.default_palette)
        self.app.setStyleSheet(self.default_stylesheet)

        self.app.setStyleSheet(
            qdarktheme.load_stylesheet(theme=resolved_theme_id.value)
        )

    def available_themes(self) -> list[ThemeId]:
        return [
            ThemeId.SYSTEM,
            ThemeId.LIGHT,
            ThemeId.DARK,
        ]

    def _normalize_theme(self, theme: str) -> ThemeId:
        for theme_id in ThemeId:
            if theme == theme_id.value:
                return theme_id

        return ThemeId.SYSTEM

    def _resolve_theme(self, theme_id: ThemeId) -> ThemeId:
        if theme_id != ThemeId.SYSTEM:
            return theme_id

        if self._is_system_dark_theme():
            return ThemeId.DARK

        return ThemeId.LIGHT

    def _is_system_dark_theme(self) -> bool:
        if sys.platform == "win32":
            return self._is_windows_dark_theme()

        return self._is_qt_palette_dark()

    def _is_windows_dark_theme(self) -> bool:
        try:
            import winreg

            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
            )

            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")

            return value == 0

        except Exception:
            return self._is_qt_palette_dark()

    def _is_qt_palette_dark(self) -> bool:
        color = self.default_palette.window().color()
        return color.lightness() < 128


class TranslationManager:
    def __init__(
        self,
        app: QApplication,
        translations_dir: Path = TRANSLATIONS_DIR
    ):
        self.app = app
        self.translations_dir = translations_dir
        self.translator = QTranslator()

    def apply(self, language: str):
        self.app.removeTranslator(self.translator)

        if language == "en":
            return

        qm_path = self.translations_dir / f"app_{language}.qm"

        if self.translator.load(str(qm_path)):
            self.app.installTranslator(self.translator)


class IconManager:
    def __init__(self, app: QApplication):
        self.app = app

    def apply(self, icon_path: Path):
        if not icon_path.exists():
            return

        icon = QIcon(str(icon_path))
        self.app.setWindowIcon(icon)


class UiManager:
    def __init__(self, app: QApplication):
        self.app = app

        self.style_manager = StyleManager(app)
        self.theme_manager = ThemeManager(app)
        self.translation_manager = TranslationManager(app)
        self.icon_manager = IconManager(app)

    def apply(self, settings: "AppSettings"):
        self.style_manager.apply(settings.style)
        self.theme_manager.apply(settings.theme)
        self.translation_manager.apply(settings.language)
        self.icon_manager.apply(APP_ICON_PATH)

    def available_styles(self) -> list[str]:
        return self.style_manager.available_styles()

    def available_themes(self) -> list[ThemeId]:
        return self.theme_manager.available_themes()
