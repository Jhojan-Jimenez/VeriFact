import logging

import numpy as np
import pytesseract

logger = logging.getLogger(__name__)


class OCREngine:
    """Wrapper around pytesseract with Spanish language support."""

    @classmethod
    def extract_text(cls, image: np.ndarray, lang: str = "spa+eng") -> str:
        """Extract text from preprocessed image."""
        try:
            # Custom Tesseract config: PSM 6 (Assume a single uniform block of text) or PSM 4
            custom_config = r"--oem 3 --psm 6"
            text = pytesseract.image_to_string(image, lang=lang, config=custom_config)
            return text.strip()
        except pytesseract.TesseractNotFoundError:
            logger.warning("Tesseract binary not found in host PATH. Running in fallback mode.")
            return ""
        except Exception as e:
            logger.error(f"OCR extraction error: {e}")
            # Try with default psm if custom config fails
            try:
                return pytesseract.image_to_string(image).strip()
            except Exception:
                return ""
