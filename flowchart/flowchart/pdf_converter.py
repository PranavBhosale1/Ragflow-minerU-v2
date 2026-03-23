from pdf2image import convert_from_path, exceptions
from typing import List, Optional
import os
import shutil


def resolve_poppler_path(poppler_path: Optional[str]) -> Optional[str]:
    """Resolve and validate the poppler path.

    If `poppler_path` is None, check whether `pdfinfo` is on PATH and return None
    (meaning use PATH). If a path is provided, validate it contains `pdfinfo` or
    `pdftoppm` (or that its `bin` subfolder does) and return the folder to pass
    to `pdf2image`. Raises `RuntimeError` with guidance if not found.
    """
    executables = ["pdfinfo", "pdftoppm"]

    # check PATH first
    if not poppler_path:
        for exe in executables:
            if shutil.which(exe) or shutil.which(exe + ".exe"):
                return None

        raise RuntimeError(
            "Poppler executables not found on PATH. Provide `--poppler-path` or set POPPLER_PATH."
        )

    # user provided a path: check a few likely locations
    p = os.path.abspath(poppler_path)

    candidates = [p, os.path.join(p, "bin")]

    # if user accidentally passed to the exe directly, accept its parent
    if os.path.isfile(p):
        candidates.insert(0, os.path.dirname(p))

    found = None
    for c in candidates:
        for exe in executables:
            exe_name = exe + ".exe" if os.name == "nt" else exe
            if os.path.exists(os.path.join(c, exe_name)):
                found = c
                break
        if found:
            break

    if not found:
        tried = "\n".join(candidates)
        raise RuntimeError(
            f"Poppler executables not found in the provided path. Tried:\n{tried}\n"
            "Make sure you pointed to the folder containing the poppler binaries (the folder\n"
            "that contains pdfinfo.exe and pdftoppm.exe). See README for download instructions."
        )

    return found


def pdf_to_images(pdf_path: str, dpi: int = 300, poppler_path: Optional[str] = None) -> List[str]:
    """Convert a PDF into PNG images (one per page). Returns list of paths.

    On Windows, `poppler_path` should point to the folder containing the poppler
    binaries (the folder that contains `pdftoppm.exe` / `pdfinfo.exe`). If not
    provided, pdf2image will try to find poppler on PATH and will raise a helpful
    error if it's missing.
    """
    # Resolve and validate poppler path (may raise helpful RuntimeError)
    resolved = None
    try:
        resolved = resolve_poppler_path(poppler_path)
    except RuntimeError:
        # re-raise with same message to keep API
        raise

    try:
        pages = convert_from_path(pdf_path, dpi=dpi, poppler_path=resolved)
    except exceptions.PDFInfoNotInstalledError as e:
        hint = (
            "Poppler not found or not usable. On Windows download poppler binaries from:\n"
            "  https://github.com/oschwartz10612/poppler-windows/releases\n"
            "Unzip and either add the `bin` folder to PATH or pass its path to the\n"
            "`pdf_to_images(..., poppler_path=...)`/CLI `--poppler-path` option."
        )
        raise RuntimeError(f"Unable to convert PDF: {e}\n{hint}") from e

    images = []

    for i, page in enumerate(pages):
        path = os.path.abspath(f"page_{i}.png")
        page.save(path, "PNG")
        images.append(path)

    return images
