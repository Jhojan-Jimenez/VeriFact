import re
from datetime import UTC, datetime

from src.api.schemas.receipt import ExtractedReceiptData
from src.core.exceptions import ExtractionFailedError
from src.domain.models import BankPlatform
from src.services.extractors.base import BaseReceiptExtractor


class BancolombiaExtractor(BaseReceiptExtractor):
    platform = BankPlatform.BANCOLOMBIA

    def can_handle(self, text: str) -> bool:
        lower = text.lower()
        return ("bancolombia" in lower) or ("comprobante no" in lower and "transferencia" in lower)

    def extract(self, text: str, qr_data: list[str] | None = None) -> ExtractedReceiptData:
        # Reference (Comprobante No. / Recibo)
        ref_match = re.search(r"(?:comprobante\s*(?:no\.?|n[uú]mero)?)\s*:?\s*([A-Za-z0-9\-]{5,20})", text, re.IGNORECASE)
        if not ref_match:
            ref_match = re.search(r"\b(\d{7,12})\b", text)

        if not ref_match:
            raise ExtractionFailedError(
                message="Could not extract Bancolombia receipt number",
                details={"extractor": "BancolombiaExtractor"},
            )
        reference_number = ref_match.group(1).strip()

        # Amount extraction (Valor enviado / Transferido / Valor)
        amount_match = re.search(r"(?:valor\s*(?:transferido|enviado)?|total)\s*:?\s*\$\s*([\d\.,]+)", text, re.IGNORECASE)
        if not amount_match:
            amount_match = re.search(r"\$\s*([\d\.,]+)", text)

        if not amount_match:
            raise ExtractionFailedError(
                message="Could not extract Bancolombia amount",
                details={"extractor": "BancolombiaExtractor"},
            )
        amount_cop = self.parse_cop_amount(amount_match.group(1))

        # Concept / Descripción
        concept_match = re.search(r"(?:descripci[oó]n|concepto|mensaje)\s*:?\s*([^\n\r]+)", text, re.IGNORECASE)
        concept = concept_match.group(1).strip() if concept_match else None

        return ExtractedReceiptData(
            bank_platform=self.platform,
            reference_number=reference_number,
            amount_cop=amount_cop,
            receipt_timestamp=datetime.now(UTC),
            concept=concept,
            raw_text=text,
        )
