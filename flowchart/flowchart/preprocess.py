import cv2
import numpy as np
from typing import Tuple, List, Dict

def preprocess(image_path: str) -> Tuple["numpy.ndarray", "numpy.ndarray"]:
    """Read image, convert to grayscale, blur and adaptive threshold.

    Returns original BGR image and the binary inverted image used for contours/lines.
    """
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Image not found: {image_path}")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    _, thresh = cv2.threshold(
        blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    )

    return img, thresh


def mask_shapes(binary: np.ndarray, nodes: List[Dict], padding: int = 10) -> np.ndarray:
    """Create a copy of the binary image with detected shapes masked out.
    
    This helps isolate connecting lines from shape edges.
    
    Args:
        binary: Binary image
        nodes: List of detected nodes with bbox
        padding: Extra pixels to remove around each shape
        
    Returns:
        Binary image with shapes masked (set to 0/black)
    """
    masked = binary.copy()
    
    for node in nodes:
        x, y, w, h = node["bbox"]
        # Expand bbox by padding
        x1 = max(0, x - padding)
        y1 = max(0, y - padding)
        x2 = min(binary.shape[1], x + w + padding)
        y2 = min(binary.shape[0], y + h + padding)
        
        # Mask this region
        masked[y1:y2, x1:x2] = 0
    
    return masked
