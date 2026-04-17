from typing import List, Dict

def get_reader(languages=None):
    # Lazy import to avoid startup cost
    import easyocr

    if languages is None:
        languages = ["en"]

    return easyocr.Reader(languages, verbose=False)

def extract_text(img, nodes: List[Dict]):
    """Run OCR on crops for each node and attach `text` to node dicts."""
    reader = get_reader()

    for node in nodes:
        x, y, w, h = node["bbox"]
        crop = img[y : y + h, x : x + w]

        result = reader.readtext(crop)
        text = " ".join([r[1] for r in result])

        node["text"] = text

    return nodes
