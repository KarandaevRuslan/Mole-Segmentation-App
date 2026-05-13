from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

ASSETS_DIR = BASE_DIR / "assets"
APP_ICON_PATH = ASSETS_DIR / "app_icon.ico"


IMAGE_SIZE = 256

THRESHOLD = 0.5

OVERLAY_ALPHA = 0.4
OVERLAY_COLOR_RGB = (255, 0, 0)

MEAN = [0.7518, 0.5733, 0.4877]
STD = [0.1616, 0.1568, 0.1569]

METHOD_OPENCV = "OpenCV"
METHOD_UNET = "U-Net"
METHOD_DEEPLAB = "DeepLabV3+"

METHODS = [
    METHOD_OPENCV,
    METHOD_UNET,
    METHOD_DEEPLAB,
]

CHECKPOINTS = {
    METHOD_UNET: BASE_DIR / "segmentation_models" / "unet_resnet34_best.pt",
    METHOD_DEEPLAB: (
        BASE_DIR
        / "segmentation_models"
        / "deeplabv3plus_resnet34_best.pt"
    ),
}
