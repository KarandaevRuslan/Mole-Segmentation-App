from dataclasses import dataclass, field
from settings_service import AppSettings
from typing import Optional

import numpy as np

from config import METHOD_OPENCV


@dataclass
class AppState:
    image_path: Optional[str] = None
    selected_method: str = METHOD_OPENCV

    original_image: Optional[np.ndarray] = None
    predicted_mask: Optional[np.ndarray] = None
    overlay_image: Optional[np.ndarray] = None

    status_text: str = "Ready"
    is_running: bool = False

    settings: AppSettings = field(default_factory=AppSettings)
