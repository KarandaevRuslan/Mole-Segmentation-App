import cv2
import numpy as np

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap, QPainter, QColor, QFont

from config import OVERLAY_ALPHA, OVERLAY_COLOR_RGB


def read_rgb_image(image_path: str) -> np.ndarray:
    image_bgr = cv2.imread(image_path)

    if image_bgr is None:
        raise ValueError(f"Could not read image: {image_path}")

    return cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)


def create_overlay(
    image_rgb: np.ndarray,
    mask: np.ndarray,
    alpha: float = OVERLAY_ALPHA,
    color_rgb=OVERLAY_COLOR_RGB,
) -> np.ndarray:
    overlay = image_rgb.copy()
    overlay[mask > 127] = np.array(color_rgb, dtype=np.uint8)

    result = cv2.addWeighted(
        image_rgb,
        1 - alpha,
        overlay,
        alpha,
        0
    )

    return result


def placeholder_qpixmap(
    width: int = 400,
    height: int = 300,
    text: str = "No image",
    text_color: QColor | None = None,
) -> QPixmap:
    pixmap = QPixmap(width, height)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)

    if text_color is None:
        text_color = QColor("#666666")

    painter.setPen(text_color)
    painter.setFont(QFont("Arial", 16))

    painter.drawText(
        pixmap.rect(),
        Qt.AlignCenter,
        text
    )

    painter.end()

    return pixmap


def numpy_to_qpixmap(image: np.ndarray) -> QPixmap:
    if image is None:
        return QPixmap()

    if image.ndim == 2:
        image = np.ascontiguousarray(image)

        h, w = image.shape

        qimage = QImage(
            image.data,
            w,
            h,
            image.strides[0],
            QImage.Format_Grayscale8
        )

        return QPixmap.fromImage(qimage.copy())

    if image.ndim == 3:
        image = np.ascontiguousarray(image)

        h, w, c = image.shape

        if c != 3:
            raise ValueError("RGB image must have 3 channels.")

        qimage = QImage(
            image.data,
            w,
            h,
            image.strides[0],
            QImage.Format_RGB888
        )

        return QPixmap.fromImage(qimage.copy())

    raise ValueError("Unsupported image format.")
