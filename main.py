import sys

from PyQt5.QtWidgets import QApplication

from view import MainWindow
from presenter import MainPresenter
from segmentation_service import SegmentationService
from settings_service import SettingsService
from ui_manager import UiManager


def main():
    app = QApplication(sys.argv)

    settings_service = SettingsService()
    settings = settings_service.load()

    ui_manager = UiManager(app)
    ui_manager.apply(settings)

    window = MainWindow()

    segmentation_service = SegmentationService()

    presenter = MainPresenter(
        view=window,
        segmentation_service=segmentation_service,
        settings_service=settings_service,
        ui_manager=ui_manager,
    )

    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
