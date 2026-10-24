import hashlib
import logging

from src.api.schemas.receipt import ExtractedReceiptData
from src.core.exceptions import ExtractionFailedError
from src.services.extractors.bancolombia import BancolombiaExtractor
from src.services.extractors.base import BaseReceiptExtractor
from src.services.extractors.bre_b import BreBExtractor
from src.services.extractors.daviplata import DaviplataExtractor
from src.services.extractors.dian_invoice import DianInvoiceExtractor
from src.services.extractors.nequi import NequiExtractor
from src.services.vision.ocr_engine import OCREngine
from src.services.vision.preprocessor import ImagePreprocessor
from src.services.vision.qr_decoder import QRDecoder

logger = logging.getLogger(__name__)


class VisionService:
    """Orchestrates QR code detection, image enhancement, and OCR extraction."""

    def __init__(self):
        self.extractors: list[BaseReceiptExtractor] = [
            DianInvoiceExtractor(),
            NequiExtractor(),
            DaviplataExtractor(),
            BancolombiaExtractor(),
            BreBExtractor(),
        ]

    @staticmethod
    def calculate_sha256(data: bytes) -> str:
        """Compute cryptographic SHA-256 hash of the receipt image bytes."""
        return hashlib.sha256(data).hexdigest()

    def process_receipt(self, image_bytes: bytes) -> tuple[ExtractedReceiptData, str]:
        """Process image bytes and return extracted financial data and SHA-256 hash."""
        sha256_hash = self.calculate_sha256(image_bytes)

        # 1. Decode bytes into CV2 image
        try:
            cv2_img = ImagePreprocessor.bytes_to_cv2(image_bytes)
        except Exception as e:
            raise ExtractionFailedError(
                message="Invalid image payload: unable to decode into image buffer",
                details={"error": str(e)},
            ) from e

        # 2. Priority Phase: Attempt QR Code Detection
        qr_results = QRDecoder.decode(cv2_img)
        if qr_results:
            # Check if QR belongs to DIAN or structured payment
            dian_ext = DianInvoiceExtractor()
            for qr_item in qr_results:
                if dian_ext.can_handle(qr_item):
                    data = dian_ext.extract(qr_item, qr_data=qr_results)
                    return data, sha256_hash

        # 3. Pre-process Image for OCR (deskew + Otsu binarization)
        preprocessed = ImagePreprocessor.preprocess_for_ocr(cv2_img)

        # 4. Extract text using Tesseract
        raw_text = OCREngine.extract_text(preprocessed)

        if not raw_text and not qr_results:
            raise ExtractionFailedError(
                message="No readable text or QR codes detected in receipt image",
                details={"sha256": sha256_hash},
            )

        # 5. Route to Matching Bank Extractor
        for extractor in self.extractors:
            if extractor.can_handle(raw_text):
                try:
                    data = extractor.extract(raw_text, qr_data=qr_results)
                    return data, sha256_hash
                except ExtractionFailedError:
                    continue

        # If no specialized extractor matched
        raise ExtractionFailedError(
            message="Unrecognized slip format: could not match Nequi, Daviplata, Bancolombia, Bre-B, or DIAN",
            details={"raw_snippet": raw_text[:300] if raw_text else "empty"},
        )
