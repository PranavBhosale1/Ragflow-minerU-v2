import sys
from pathlib import Path
import cv2

from flowchart.pdf_converter import pdf_to_images
from flowchart.preprocess import preprocess, mask_shapes
from flowchart.shapes import detect_shapes
from flowchart import lines as detector


def draw_overlay(image_path: str, nodes: list, edges: list, out_path: str):
    img = cv2.imread(image_path)
    if img is None:
        raise RuntimeError(f"Unable to open image: {image_path}")

    # Draw nodes
    for i, node in enumerate(nodes):
        x, y, w, h = node['bbox']
        cv2.rectangle(img, (int(x), int(y)), (int(x + w), int(y + h)), (0, 255, 0), 2)
        cx = int(x + w / 2)
        cy = int(y + h / 2)
        cv2.putText(img, str(i), (cx - 8, cy + 6), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    # Draw directed edges
    for edge in edges:
        try:
            src = nodes[edge['src']]['bbox']
            dst = nodes[edge['dst']]['bbox']
        except Exception:
            continue

        sx = int(src[0] + src[2] / 2)
        sy = int(src[1] + src[3] / 2)
        dx = int(dst[0] + dst[2] / 2)
        dy = int(dst[1] + dst[3] / 2)

        cv2.arrowedLine(img, (sx, sy), (dx, dy), (255, 0, 0), 2, tipLength=0.2)

    cv2.imwrite(out_path, img)


def run(pdf_path: str, poppler_path: str = None, page_index: int = 0, out="overlay_output.png"):
    images = pdf_to_images(pdf_path, poppler_path=poppler_path)
    if page_index >= len(images):
        raise SystemExit(f"PDF has {len(images)} pages, requested page {page_index}")

    page_path = images[page_index]

    img, binary = preprocess(page_path)
    nodes = detect_shapes(binary)

    masked = mask_shapes(binary, nodes, padding=5)

    # Run detector (will also write debug image if supported)
    edges = detector.detect_edges_and_arrows(masked, nodes, debug_path="debug_detector.png")

    # Detect arrowheads (simple contour-based detector for visualization)
    arrows = detect_arrows_from_mask(masked)

    # Ensure bbox format
    for n in nodes:
        if isinstance(n.get('bbox'), list):
            n['bbox'] = tuple(n['bbox'])

    draw_overlay(page_path, nodes, edges, out)
    print(f"Overlay saved: {out}")


def detect_arrows_from_mask(binary: "cv2.UMat|np.ndarray", min_area: int = 20, max_area: int = 800):
    img = binary.copy()
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    img = cv2.dilate(img, kernel, iterations=1)
    contours, _ = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    arrows = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < min_area or area > max_area:
            continue

        peri = cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, 0.04 * peri, True)
        if not (3 <= len(approx) <= 5):
            continue

        hull = cv2.convexHull(cnt)
        hull_area = cv2.contourArea(hull)
        solidity = float(area) / hull_area if hull_area > 0 else 0
        if solidity < 0.5:
            continue

        M = cv2.moments(cnt)
        if M.get('m00', 0) == 0:
            continue
        cx = int(M['m10'] / M['m00'])
        cy = int(M['m01'] / M['m00'])

        pts = approx.reshape(-1, 2)
        dists = np.linalg.norm(pts - np.array([cx, cy]), axis=1)
        tip = tuple(pts[np.argmax(dists)])
        angle = np.degrees(np.arctan2(tip[1] - cy, tip[0] - cx))

        arrows.append({
            'tip': tip,
            'position': (cx, cy),
            'direction': float(angle),
            'confidence': float(solidity),
            'method': 'contour'
        })

    return arrows


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python run_comparison.py <pdf-path> [--poppler PATH] [--page N] [--out FILE]")
        raise SystemExit(1)

    pdf = sys.argv[1]
    poppler = None
    page = 0
    out = 'comparison_output.png'

    argv = sys.argv[2:]
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == '--poppler' and i + 1 < len(argv):
            poppler = argv[i+1]
            i += 2
        elif a == '--page' and i + 1 < len(argv):
            page = int(argv[i+1])
            i += 2
        elif a == '--out' and i + 1 < len(argv):
            out = argv[i+1]
            i += 2
        else:
            i += 1

    run(pdf, poppler_path=poppler, page_index=page, out=out)
