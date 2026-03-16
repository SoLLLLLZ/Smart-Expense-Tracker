"""OCR module for extracting text from receipt images."""
from pathlib import Path
from typing import Union

from config import SUPPORTED_IMAGE_EXTENSIONS


def is_tesseract_available() -> bool:
    """Check whether the Tesseract binary is accessible. Returns True/False without raising."""
    try:
        import pytesseract
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False


def preprocess_image(image_path: Union[str, Path]):
    """Return a preprocessed PIL Image ready for OCR.

    Steps: convert to grayscale, apply binary threshold to improve
    character recognition on receipt photos.
    """
    from PIL import Image, ImageFilter, ImageEnhance

    img = Image.open(image_path)

    # Convert to grayscale
    img = img.convert("L")

    # Scale up small images — Tesseract works better at higher resolution
    width, height = img.size
    if width < 1000:
        scale = 1000 / width
        img = img.resize((int(width * scale), int(height * scale)), Image.LANCZOS)

    # Sharpen slightly to improve edge detection on blurry photos
    img = img.filter(ImageFilter.SHARPEN)

    # Increase contrast
    img = ImageEnhance.Contrast(img).enhance(2.0)

    return img


def extract_text_from_image(image_path: Union[str, Path]) -> str:
    """Run pytesseract OCR on the given image file.

    Raises FileNotFoundError if image_path does not exist.
    Raises ValueError if the file extension is not supported.
    Raises RuntimeError if the Tesseract binary is not found.
    Returns raw extracted text as a string (may be empty).
    """
    try:
        import pytesseract
    except ImportError:
        raise ImportError(
            "pytesseract is not installed. Run: pip install pytesseract Pillow"
        )

    path = Path(image_path)

    if not path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")

    if path.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type '{path.suffix}'. "
            f"Supported: {', '.join(SUPPORTED_IMAGE_EXTENSIONS)}"
        )

    try:
        img = preprocess_image(path)
        # PSM 6: assume a single uniform block of text (good for receipts)
        config = "--psm 6"
        text = pytesseract.image_to_string(img, config=config)
        return text
    except pytesseract.pytesseract.TesseractNotFoundError:
        raise RuntimeError(
            "Tesseract binary not found. Install it with:\n"
            "  macOS:  brew install tesseract\n"
            "  Linux:  sudo apt install tesseract-ocr\n"
            "  Windows: https://github.com/UB-Mannheim/tesseract/wiki"
        )
