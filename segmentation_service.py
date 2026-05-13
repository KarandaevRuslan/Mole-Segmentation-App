from pathlib import Path
from typing import Dict

import cv2
import numpy as np
import torch

from config import (
    CHECKPOINTS,
    IMAGE_SIZE,
    MEAN,
    METHOD_DEEPLAB,
    METHOD_OPENCV,
    METHOD_UNET,
    STD,
    THRESHOLD,
)


class SegmentationService:
    def __init__(self):
        self.device = torch.device(
            "cuda" if torch.cuda.is_available() else "cpu")
        self.models: Dict[str, torch.nn.Module] = {}

    def segment(self, method: str, image_path: str) -> np.ndarray:
        if method == METHOD_OPENCV:
            return self._opencv_segment(image_path)

        if method in {METHOD_UNET, METHOD_DEEPLAB}:
            return self._ml_segment(method, image_path)

        raise ValueError(f"Unknown segmentation method: {method}")

    def _opencv_segment(self, image_path: str) -> np.ndarray:
        image_bgr = cv2.imread(image_path)

        if image_bgr is None:
            raise ValueError(f"Could not read image: {image_path}")

        image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)

        blur = cv2.GaussianBlur(gray, (7, 7), 0)

        _, mask = cv2.threshold(
            blur,
            0,
            255,
            cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
        )

        kernel = np.ones((9, 9), np.uint8)

        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(mask)

        if num_labels > 1:
            largest_label = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
            mask = (labels == largest_label).astype(np.uint8) * 255

        return mask

    def _ml_segment(self, model_name: str, image_path: str) -> np.ndarray:
        model = self._get_model(model_name)

        image_bgr = cv2.imread(image_path)

        if image_bgr is None:
            raise ValueError(f"Could not read image: {image_path}")

        image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)

        original_h, original_w = image_rgb.shape[:2]

        resized = cv2.resize(
            image_rgb,
            (IMAGE_SIZE, IMAGE_SIZE),
            interpolation=cv2.INTER_AREA
        )

        image_float = resized.astype(np.float32) / 255.0
        image_float = (image_float - np.array(MEAN)) / np.array(STD)

        tensor = torch.from_numpy(image_float)
        tensor = tensor.permute(2, 0, 1).unsqueeze(
            0).float()  # [H, W, C] -> [1, C, H, W]
        tensor = tensor.to(self.device)

        with torch.no_grad():
            logits = model(tensor)
            probs = torch.sigmoid(logits)  # [1, 1, H, W]
            prob_mask = probs.squeeze().cpu().numpy()  # [H, W]

        mask = (prob_mask > THRESHOLD).astype(np.uint8) * 255

        mask = cv2.resize(
            mask,
            (original_w, original_h),
            interpolation=cv2.INTER_NEAREST
        )

        return mask

    def _get_model(self, model_name: str) -> torch.nn.Module:
        if model_name in self.models:
            return self.models[model_name]

        model = self._load_model(model_name)
        self.models[model_name] = model

        return model

    def _load_model(self, model_name: str) -> torch.nn.Module:
        import segmentation_models_pytorch as smp

        checkpoint_path = CHECKPOINTS[model_name]

        if not Path(checkpoint_path).exists():
            raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")

        if model_name == METHOD_UNET:
            model = smp.Unet(
                encoder_name="resnet34",
                encoder_weights=None,
                in_channels=3,
                classes=1,
            )
        elif model_name == METHOD_DEEPLAB:
            model = smp.DeepLabV3Plus(
                encoder_name="resnet34",
                encoder_weights=None,
                in_channels=3,
                classes=1,
            )
        else:
            raise ValueError(f"Unknown model: {model_name}")

        checkpoint = torch.load(
            checkpoint_path,
            map_location=self.device
        )

        if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
            model.load_state_dict(checkpoint["model_state_dict"])
        else:
            model.load_state_dict(checkpoint)

        model = model.to(self.device)
        model.eval()

        return model
