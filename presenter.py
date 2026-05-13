import os

from PyQt5.QtCore import QObject, QThread, pyqtSignal
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QDialog

from app_state import AppState
from image_utils import create_overlay, read_rgb_image
from segmentation_service import SegmentationService
from settings_service import AppSettings, SettingsService
from ui_manager import UiManager
from view import SettingsDialog
import cv2


class SegmentationWorker(QObject):
    finished = pyqtSignal(object, object, object)
    failed = pyqtSignal(str)

    def __init__(
        self,
        segmentation_service: SegmentationService,
        method: str,
        image_path: str,
    ):
        super().__init__()

        self.segmentation_service = segmentation_service
        self.method = method
        self.image_path = image_path

    def run(self):
        try:
            mask = self.segmentation_service.segment(
                method=self.method,
                image_path=self.image_path,
            )

            original = read_rgb_image(self.image_path)
            overlay = create_overlay(original, mask)

            self.finished.emit(original, mask, overlay)

        except Exception as exc:
            self.failed.emit(str(exc))


class MainPresenter:
    def __init__(
        self,
        view,
        segmentation_service: SegmentationService,
        settings_service: SettingsService,
        ui_manager: UiManager,
    ):
        self.view = view
        self.segmentation_service = segmentation_service
        self.settings_service = settings_service
        self.ui_manager = ui_manager

        self.segmentation_thread = None
        self.segmentation_worker = None

        settings = self.settings_service.load()
        self.state = AppState(
            status_text=self.view.tr("Ready"),
            settings=settings,
        )

        self.view.set_presenter(self)
        self.view.render(self.state)

    # Callbacks for view events

    def select_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self.view,
            self.view.tr("Choose image"),
            "",
            self.view.tr("Images (*.png *.jpg *.jpeg *.bmp)")
        )

        if not file_path:
            return

        try:
            image = read_rgb_image(file_path)

            self.state.image_path = file_path
            self.state.original_image = image
            self.state.predicted_mask = None
            self.state.overlay_image = None
            self.state.status_text = (
                f"{self.view.tr('Image loaded')}: "
                f"{os.path.basename(file_path)}"
            )

            self.view.render(self.state)

        except Exception as exc:
            self._show_error(str(exc))

    def save_mask(self):
        if self.state.predicted_mask is None:
            self._show_error(self.view.tr("No mask to save"))
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self.view,
            self.view.tr("Save mask"),
            "mask.png",
            self.view.tr(
                "PNG image (*.png);;JPEG image (*.jpg *.jpeg);;"
                "BMP image (*.bmp)")
        )

        if not file_path:
            return

        try:
            success = cv2.imwrite(file_path, self.state.predicted_mask)

            if not success:
                raise ValueError(self.view.tr("Could not save file"))

            self.state.status_text = (
                f"{self.view.tr('Mask saved')}: {os.path.basename(file_path)}"
            )
            self.view.render(self.state)

        except Exception as exc:
            self.state.status_text = f"{self.view.tr('Error')}: {exc}"
            self.view.render(self.state)
            self._show_error(str(exc))

    def save_overlay(self):
        if self.state.overlay_image is None:
            self._show_error(self.view.tr("No overlay to save"))
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self.view,
            self.view.tr("Save overlay"),
            "overlay.png",
            self.view.tr(
                "PNG image (*.png);;JPEG image (*.jpg *.jpeg);;"
                "BMP image (*.bmp)")
        )

        if not file_path:
            return

        try:
            overlay_bgr = cv2.cvtColor(
                self.state.overlay_image,
                cv2.COLOR_RGB2BGR
            )

            success = cv2.imwrite(file_path, overlay_bgr)

            if not success:
                raise ValueError(self.view.tr("Could not save file"))

            self.state.status_text = (
                f"{self.view.tr('Overlay saved')}: "
                f"{os.path.basename(file_path)}"
            )
            self.view.render(self.state)

        except Exception as exc:
            self.state.status_text = f"{self.view.tr('Error')}: {exc}"
            self.view.render(self.state)
            self._show_error(str(exc))

    def change_method(self, method: str):
        self.state.selected_method = method
        self.state.predicted_mask = None
        self.state.overlay_image = None

        self.view.render(self.state)

    def run_segmentation(self):
        if self.state.image_path is None:
            self._show_error(self.view.tr("No image selected"))
            return

        if self.state.is_running:
            return

        self.state.is_running = True
        self.state.status_text = self.view.tr("Running segmentation...")
        self.view.render(self.state)

        self.segmentation_thread = QThread()
        self.segmentation_worker = SegmentationWorker(
            segmentation_service=self.segmentation_service,
            method=self.state.selected_method,
            image_path=self.state.image_path,
        )

        self.segmentation_worker.moveToThread(self.segmentation_thread)

        self.segmentation_thread.started.connect(
            self.segmentation_worker.run
        )

        self.segmentation_worker.finished.connect(
            self._on_segmentation_finished
        )
        self.segmentation_worker.failed.connect(
            self._on_segmentation_failed
        )

        self.segmentation_worker.finished.connect(
            self.segmentation_thread.quit
        )
        self.segmentation_worker.failed.connect(
            self.segmentation_thread.quit
        )

        self.segmentation_thread.finished.connect(
            self.segmentation_worker.deleteLater
        )
        self.segmentation_thread.finished.connect(
            self.segmentation_thread.deleteLater
        )
        self.segmentation_thread.finished.connect(
            self._clear_segmentation_worker
        )

        self.segmentation_thread.start()

    def apply_current_ui_settings(self):
        self.ui_manager.apply(self.state.settings)
        self.view.retranslate_ui()
        self.view.refresh_ui_style()
        self.view.render(self.state)

    # Settings management

    def open_settings(self):
        if self.state.is_running:
            return

        new_settings = self._show_settings_dialog()

        if new_settings is None:
            return

        self.apply_settings(new_settings)

    def apply_settings(self, settings: AppSettings):
        self.state.settings = settings
        self.settings_service.save(settings)

        self.ui_manager.apply(settings)

        self.view.retranslate_ui()
        self.view.refresh_ui_style()

        self.state.status_text = self.view.tr("Settings saved")
        self.view.render(self.state)

    def apply_settings_including_dialog(
        self,
        dialog: SettingsDialog,
        settings: AppSettings
    ):
        self.apply_settings(settings)
        dialog.retranslate_ui()

    def _show_settings_dialog(self) -> AppSettings | None:
        dialog = SettingsDialog(self.state.settings, self.view)

        dialog.settings_applied.connect(
            lambda settings: self.apply_settings_including_dialog(
                dialog, settings)
        )

        if dialog.exec_() == QDialog.Accepted:
            return dialog.get_settings()

        return None

    # Error handling

    def _show_error(self, message: str):
        QMessageBox.critical(
            self.view,
            self.view.tr("Error"),
            message
        )

    # Segmentation worker callbacks

    def _on_segmentation_finished(self, original, mask, overlay):
        self.state.original_image = original
        self.state.predicted_mask = mask
        self.state.overlay_image = overlay
        self.state.status_text = (
            f"{self.view.tr('Done')}. "
            f"{self.view.tr('Method')}: {self.state.selected_method}"
        )

        self.state.is_running = False
        self.view.render(self.state)

    def _on_segmentation_failed(self, message: str):
        self.state.status_text = f"{self.view.tr('Error')}: {message}"
        self.state.is_running = False

        self.view.render(self.state)
        self._show_error(message)

    def _clear_segmentation_worker(self):
        self.segmentation_thread = None
        self.segmentation_worker = None
