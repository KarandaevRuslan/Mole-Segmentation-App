from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QPalette, QPixmap
from PyQt5.QtWidgets import (
    QAction,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QSizePolicy,
    QToolBar,
    QVBoxLayout,
    QWidget,
    QStyleFactory,
)

from i18n_binder import I18nBinder

from settings_service import AppSettings
from app_state import AppState
from config import METHODS
from image_utils import numpy_to_qpixmap, placeholder_qpixmap
from ui_manager import ThemeId, theme_display_name


class SettingsDialog(QDialog):
    settings_applied = pyqtSignal(object)

    def __init__(self, settings: AppSettings, parent=None):
        super().__init__(parent)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        self.i18n = I18nBinder()

        self.setWindowTitle(
            self.i18n(self.setWindowTitle, lambda: self.tr("Settings"))
        )

        self.style_combo = QComboBox()
        self.style_combo.addItems(QStyleFactory.keys())
        self._select_style(settings.style)

        self.theme_combo = QComboBox()
        self._set_theme_items(settings.theme)

        self.language_combo = QComboBox()
        self.language_combo.addItem("English", "en")
        self.language_combo.addItem("Русский", "ru")
        self._select_language(settings.language)

        self.style_label = QLabel()
        self.style_label.setText(
            self.i18n(self.style_label.setText, lambda: self.tr("Style"))
        )

        self.theme_label = QLabel()
        self.theme_label.setText(
            self.i18n(self.theme_label.setText, lambda: self.tr("Theme"))
        )

        self.language_label = QLabel()
        self.language_label.setText(
            self.i18n(
                self.language_label.setText,
                lambda: self.tr("Language")
            )
        )

        self.form_layout = QFormLayout()
        self.form_layout.addRow(self.style_label, self.style_combo)
        self.form_layout.addRow(self.theme_label, self.theme_combo)
        self.form_layout.addRow(self.language_label, self.language_combo)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok |
            QDialogButtonBox.Apply |
            QDialogButtonBox.Cancel
        )

        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        self.ok_button = self.buttons.button(QDialogButtonBox.Ok)
        self.apply_button = self.buttons.button(QDialogButtonBox.Apply)
        self.cancel_button = self.buttons.button(QDialogButtonBox.Cancel)

        self.ok_button.setText(
            self.i18n(self.ok_button.setText, lambda: self.tr("OK"))
        )
        self.apply_button.setText(
            self.i18n(self.apply_button.setText, lambda: self.tr("Apply"))
        )
        self.cancel_button.setText(
            self.i18n(self.cancel_button.setText, lambda: self.tr("Cancel"))
        )

        self.apply_button.clicked.connect(self._on_apply_clicked)

        layout = QVBoxLayout()
        layout.addLayout(self.form_layout)
        layout.addWidget(self.buttons)

        self.setLayout(layout)

    def get_settings(self) -> AppSettings:
        return AppSettings(
            style=self.style_combo.currentText(),
            theme=self.theme_combo.currentData(),
            language=self.language_combo.currentData(),
        )

    def retranslate_ui(self):
        self.i18n.update()
        self._set_theme_items(self.theme_combo.currentData())

    def _select_style(self, style: str):
        current_style = style.lower()

        for index in range(self.style_combo.count()):
            if self.style_combo.itemText(index).lower() == current_style:
                self.style_combo.setCurrentIndex(index)
                return

    def _select_language(self, language: str):
        language_index = self.language_combo.findData(language)

        if language_index >= 0:
            self.language_combo.setCurrentIndex(language_index)

    def _set_theme_items(self, selected_theme: str | None = None):
        if selected_theme is None:
            selected_theme = ThemeId.SYSTEM.value

        self.theme_combo.blockSignals(True)
        self.theme_combo.clear()

        for theme_id in ThemeId:
            self.theme_combo.addItem(
                theme_display_name(theme_id, self.tr),
                theme_id.value
            )

        theme_index = self.theme_combo.findData(selected_theme)
        if theme_index >= 0:
            self.theme_combo.setCurrentIndex(theme_index)

        self.theme_combo.blockSignals(False)

    def _on_apply_clicked(self):
        self.settings_applied.emit(self.get_settings())


class ImagePanel(QFrame):
    def __init__(self, title_getter):
        super().__init__()

        self.i18n = I18nBinder()
        self._source_pixmap = QPixmap()
        self._current_image = None

        self.setFrameShape(QFrame.StyledPanel)
        self.setObjectName("ImagePanel")

        self.title_label = QLabel()
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setObjectName("ImagePanelTitle")
        self.title_label.setText(
            self.i18n(self.title_label.setText, title_getter)
        )

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(280, 280)
        self.image_label.setObjectName("ImageLabel")
        self.image_label.setFrameShape(QFrame.NoFrame)

        self._apply_image_label_style()

        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        layout.addWidget(self.title_label)
        layout.addWidget(self.image_label, 1)

        self.setLayout(layout)

        self.set_image(None)

    def set_image(self, image):
        self._current_image = image

        if image is None:
            text_color = self.palette().color(
                QPalette.Disabled,
                QPalette.WindowText
            )

            self._source_pixmap = placeholder_qpixmap(
                text=self.tr("No image"),
                text_color=text_color
            )
        else:
            self._source_pixmap = numpy_to_qpixmap(image)

        self._update_scaled_pixmap()

    def retranslate_ui(self):
        self.i18n.update()

        if self._current_image is None:
            self.set_image(None)

    def refresh_ui_style(self):
        self._apply_image_label_style()

        if self._current_image is None:
            self.set_image(None)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_scaled_pixmap()

    def _apply_image_label_style(self):
        palette = self.palette()

        base_color = palette.color(QPalette.Base)

        if base_color.lightness() < 128:
            bg_color = base_color.lighter(150)
        else:
            bg_color = base_color.darker(112)

        border_color = palette.color(QPalette.Mid)

        self.image_label.setStyleSheet(f"""
            QLabel#ImageLabel {{
                background-color: rgb({bg_color.red()}, {bg_color.green()}, {bg_color.blue()});
                border: 1px dashed rgb({border_color.red()}, {border_color.green()}, {border_color.blue()});
                border-radius: 6px;
            }}
        """)

    def _update_scaled_pixmap(self):
        if self._source_pixmap.isNull():
            self.image_label.clear()
            return

        target_size = self.image_label.size()

        if target_size.width() <= 0 or target_size.height() <= 0:
            return

        scaled = self._source_pixmap.scaled(
            target_size,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )

        self.image_label.setPixmap(scaled)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.presenter = None
        self.i18n = I18nBinder()
        self._first_show_style_refresh_done = False

        self.setWindowTitle(
            self.i18n(
                self.setWindowTitle,
                lambda: self.tr("Mole Segmentation App")
            )
        )

        self.resize(1200, 650)
        self.setMinimumSize(1000, 600)

        self.setStyleSheet("""
            QFrame#ImagePanel {
                border: 1px solid palette(mid);
                border-radius: 8px;
            }

            QLabel#ImagePanelTitle {
                font-weight: 600;
                padding: 4px;
            }

            QToolBar {
                spacing: 8px;
                padding: 6px;
            }

            QStatusBar {
                border-top: 1px solid palette(mid);
            }
        """)

        self.method_label = QLabel()
        self.method_label.setText(
            self.i18n(
                self.method_label.setText,
                lambda: self.tr("Segmentation method")
            )
        )

        self.method_combo = QComboBox()
        self.method_combo.addItems(METHODS)

        self.original_panel = ImagePanel(lambda: self.tr("Original image"))
        self.mask_panel = ImagePanel(lambda: self.tr("Predicted mask"))
        self.overlay_panel = ImagePanel(lambda: self.tr("Overlay"))

        self._create_menu_bar()
        self._create_tool_bar()
        self._create_status_bar()
        self._create_central_widget()

    def set_presenter(self, presenter):
        self.presenter = presenter

    # UI update methods
    def retranslate_ui(self):
        self.i18n.update()

        self.original_panel.retranslate_ui()
        self.mask_panel.retranslate_ui()
        self.overlay_panel.retranslate_ui()

    def refresh_ui_style(self):
        self.original_panel.refresh_ui_style()
        self.mask_panel.refresh_ui_style()
        self.overlay_panel.refresh_ui_style()

    def render(self, state: AppState):
        self.method_combo.blockSignals(True)
        self.method_combo.setCurrentText(state.selected_method)
        self.method_combo.blockSignals(False)

        self.original_panel.set_image(state.original_image)
        self.mask_panel.set_image(state.predicted_mask)
        self.overlay_panel.set_image(state.overlay_image)

        self.status_text_label.setText(state.status_text)

        can_run = state.image_path is not None and not state.is_running
        can_save_mask = (
            state.predicted_mask is not None and not state.is_running
        )
        can_save_overlay = (
            state.overlay_image is not None and not state.is_running
        )

        self.run_action.setEnabled(can_run)
        self.select_action.setEnabled(not state.is_running)
        self.settings_action.setEnabled(not state.is_running)

        self.save_mask_action.setEnabled(can_save_mask)
        self.save_overlay_action.setEnabled(can_save_overlay)

        self.method_combo.setEnabled(not state.is_running)

    # View init methods
    def _create_menu_bar(self):
        # File menu
        self.file_menu = QMenu(self)
        self.file_menu.setTitle(
            self.i18n(self.file_menu.setTitle, lambda: self.tr("File"))
        )
        self.menuBar().addMenu(self.file_menu)

        # 1. Select action
        self.select_action = QAction(self)
        self.select_action.setText(
            self.i18n(
                self.select_action.setText,
                lambda: self.tr("Select image")
            )
        )
        self.select_action.triggered.connect(self._on_select_image)
        self.file_menu.addAction(self.select_action)

        # 2. Save mask action
        self.save_mask_action = QAction(self)
        self.save_mask_action.setText(
            self.i18n(
                self.save_mask_action.setText,
                lambda: self.tr("Save mask")
            )
        )
        self.save_mask_action.triggered.connect(self._on_save_mask)
        self.file_menu.addAction(self.save_mask_action)

        # 3. Save overlay action
        self.save_overlay_action = QAction(self)
        self.save_overlay_action.setText(
            self.i18n(
                self.save_overlay_action.setText,
                lambda: self.tr("Save overlay")
            )
        )
        self.save_overlay_action.triggered.connect(self._on_save_overlay)
        self.file_menu.addAction(self.save_overlay_action)

        self.file_menu.addSeparator()

        # 4. Exit action
        self.exit_action = QAction(self)
        self.exit_action.setText(
            self.i18n(self.exit_action.setText, lambda: self.tr("Exit"))
        )
        self.exit_action.triggered.connect(self.close)
        self.file_menu.addAction(self.exit_action)

        # Run menu
        self.run_menu = QMenu(self)
        self.run_menu.setTitle(
            self.i18n(self.run_menu.setTitle, lambda: self.tr("Run"))
        )
        self.menuBar().addMenu(self.run_menu)

        # Run action
        self.run_action = QAction(self)
        self.run_action.setText(
            self.i18n(
                self.run_action.setText,
                lambda: self.tr("Run segmentation")
            )
        )
        self.run_action.triggered.connect(self._on_run_segmentation)
        self.run_menu.addAction(self.run_action)

        # Settings menu
        self.settings_menu = QMenu(self)
        self.settings_menu.setTitle(
            self.i18n(
                self.settings_menu.setTitle,
                lambda: self.tr("Settings")
            )
        )
        self.menuBar().addMenu(self.settings_menu)

        # Settings action
        self.settings_action = QAction(self)
        self.settings_action.setText(
            self.i18n(
                self.settings_action.setText,
                lambda: self.tr("Preferences")
            )
        )
        self.settings_action.triggered.connect(self._on_settings)
        self.settings_menu.addAction(self.settings_action)

    def _create_tool_bar(self):
        self.toolbar = QToolBar()
        self.toolbar.setWindowTitle(
            self.i18n(
                self.toolbar.setWindowTitle,
                lambda: self.tr("Commands")
            )
        )
        self.toolbar.setMovable(False)

        self.toolbar.addAction(self.select_action)
        self.toolbar.addAction(self.run_action)
        self.toolbar.addSeparator()
        self.toolbar.addWidget(self.method_label)
        self.toolbar.addWidget(self.method_combo)

        self.addToolBar(Qt.TopToolBarArea, self.toolbar)

        self.method_combo.currentTextChanged.connect(self._on_method_changed)

    def _create_status_bar(self):
        self.status_text_label = QLabel()
        self.status_text_label.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Preferred
        )

        self.statusBar().addWidget(self.status_text_label, 1)

    def _create_central_widget(self):
        images_layout = QGridLayout()
        images_layout.setContentsMargins(12, 12, 12, 12)
        images_layout.setSpacing(12)

        images_layout.addWidget(self.original_panel, 0, 0)
        images_layout.addWidget(self.mask_panel, 0, 1)
        images_layout.addWidget(self.overlay_panel, 0, 2)

        images_layout.setColumnStretch(0, 1)
        images_layout.setColumnStretch(1, 1)
        images_layout.setColumnStretch(2, 1)

        central_widget = QWidget()
        central_widget.setLayout(images_layout)

        self.setCentralWidget(central_widget)

    # View event handlers
    def _on_select_image(self):
        if self.presenter is not None:
            self.presenter.select_image()

    def _on_save_mask(self):
        if self.presenter is not None:
            self.presenter.save_mask()

    def _on_save_overlay(self):
        if self.presenter is not None:
            self.presenter.save_overlay()

    def _on_run_segmentation(self):
        if self.presenter is not None:
            self.presenter.run_segmentation()

    def _on_method_changed(self, method: str):
        if self.presenter is not None:
            self.presenter.change_method(method)

    def _on_settings(self):
        if self.presenter is not None:
            self.presenter.open_settings()

    # Override showEvent to refresh UI style on first show
    def showEvent(self, event):
        super().showEvent(event)

        if self._first_show_style_refresh_done:
            return

        self._first_show_style_refresh_done = True

        if self.presenter is not None:
            QTimer.singleShot(0, self.presenter.apply_current_ui_settings)
        else:
            QTimer.singleShot(0, self.refresh_ui_style)
