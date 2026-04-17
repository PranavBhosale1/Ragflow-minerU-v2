import cv2
import numpy as np
from typing import List, Dict, Tuple

def detect_shapes(binary: "numpy.ndarray", min_area: int = 1000) -> List[Dict]:
    """Detect rectangular shapes and diamonds in a binary inverted image.

    Returns list of nodes with `bbox` and `type` keys.
    """
    contours, _ = cv2.findContours(
        binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
    )

    nodes: List[Dict] = []

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < min_area:
            continue

        peri = cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)

        x, y, w, h = cv2.boundingRect(cnt)

        # Only consider quadrilaterals as potential nodes
        if len(approx) == 4:
            # compute aspect ratio
            aspect = w / float(h) if h != 0 else 0

            # Determine if diamond (rotated square) by checking bounding box vs contour
            rect = cv2.minAreaRect(cnt)
            (rw, rh) = rect[1]

            if rw == 0 or rh == 0:
                shape = "process"
            else:
                # if near-square but rotated, treat as decision
                if 0.8 < (rw / float(rh)) < 1.2 and abs(rect[2]) > 10:
                    shape = "decision"
                else:
                    # use aspect heuristic
                    shape = "process" if not (0.8 < aspect < 1.2) else "process"

            nodes.append({
                "bbox": (x, y, w, h),
                "type": shape,
            })

    return nodes
