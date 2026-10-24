import re
from datetime import UTC, datetime

from src.api.schemas.receipt import ExtractedReceiptData
from src.core.exceptions import ExtractionFailedError
from src.domain.models import BankPlatform
from src.services.extractors.base import BaseReceiptExtractor


class NequiExtractor(BaseReceiptExtractor):
    platform = BankPlatform.NEQUI

    def can_handle(self, text: str) -> bool:
        lower = text.lower()
        return ("nequi" in lower) or ("enviaste" in lower and "referencia" in lower) or ("¡listo!" in lower)

    def extract(self, text: str, qr_data: list[str] | None = None) -> ExtractedReceiptData:
        # 1. Reference Extraction (e.g., M12345678, M 12345678, or alphanumeric ref)
        ref_match = re.search(r"(?:referencia|ref\.?)\s*:?\s*([A-Za-z0-9\-]{5,15})", text, re.IGNORECASE)
        if not ref_match:
            # Try standalone M-number pattern
            ref_match = re.search(r"\b(M\s*\d{7,10})\b", text, re.IGNORECASE)

        if not ref_match:
            raise ExtractionFailedError(
                message="Could not extract Nequi reference number",
                details={"extractor": "NequiExtractor", "text_snippet": text[:200]},
            )
        reference_number = ref_match.group(1).replace(" ", "").upper()

        # 2. Amount Extraction (e.g. $ 50.000, ¿Cuánto? $50.000)
        amount_match = re.search(r"(?:cu[aá]nto\??|total|enviaste)?\s*\$\s*([\d\.,]+)", text, re.IGNORECASE)
        if not amount_match:
            # Fallback to any currency string
            amount_match = re.search(r"\$\s*([\d\.,]+)", text)

        if not amount_match:
            raise ExtractionFailedError(
                message="Could not extract Nequi payment amount",
                details={"extractor": "NequiExtractor", "text_snippet": text[:200]},
            )
        amount_cop = self.parse_cop_amount(amount_match.group(1))

        # 3. Concept / Order extraction
        concept_match = re.search(r"(?:mensaje|para qu[eé] es\??)\s*:?\s*([^\n\r]+)", text, re.IGNORECASE)
        concept = concept_match.group(1).strip() if concept_match else None

        return ExtractedReceiptData(
            bank_platform=self.platform,
            reference_number=reference_number,
            amount_cop=amount_cop,
            receipt_timestamp=datetime.now(UTC),
            concept=concept,
            raw_text=text,
        )
