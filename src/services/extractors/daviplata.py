import re
from datetime import UTC, datetime

from src.api.schemas.receipt import ExtractedReceiptData
from src.core.exceptions import ExtractionFailedError
from src.domain.models import BankPlatform
from src.services.extractors.base import BaseReceiptExtractor


class DaviplataExtractor(BaseReceiptExtractor):
    platform = BankPlatform.DAVIPLATA

    def can_handle(self, text: str) -> bool:
        lower = text.lower()
        return ("daviplata" in lower) or ("aprobaci[oó]n" in lower and "transacci[oó]n exitosa" in lower)

    def extract(self, text: str, qr_data: list[str] | None = None) -> ExtractedReceiptData:
        # Reference (Número de aprobación / Autorización)
        ref_match = re.search(r"(?:aprobaci[oó]n|autorizaci[oó]n|n[uú]mero de aprobaci[oó]n)\s*:?\s*#?\s*([A-Za-z0-9]{4,15})", text, re.IGNORECASE)
        if not ref_match:
            # Fallback to standalone 6-8 digit code
            ref_match = re.search(r"\b(\d{6,8})\b", text)

        if not ref_match:
            raise ExtractionFailedError(
                message="Could not extract Daviplata approval number",
                details={"extractor": "DaviplataExtractor"},
            )
        reference_number = ref_match.group(1).strip()

        # Amount extraction (Valor / ¿Cuánto?)
        amount_match = re.search(r"(?:valor|cu[aá]nto)?\s*\$\s*([\d\.,]+)", text, re.IGNORECASE)
        if not amount_match:
            amount_match = re.search(r"\$\s*([\d\.,]+)", text)

        if not amount_match:
            raise ExtractionFailedError(
                message="Could not extract Daviplata amount",
                details={"extractor": "DaviplataExtractor"},
            )
        amount_cop = self.parse_cop_amount(amount_match.group(1))

        # Concept / Motivo
        concept_match = re.search(r"(?:motivo|mensaje|concepto)\s*:?\s*([^\n\r]+)", text, re.IGNORECASE)
        concept = concept_match.group(1).strip() if concept_match else None

        return ExtractedReceiptData(
            bank_platform=self.platform,
            reference_number=reference_number,
            amount_cop=amount_cop,
            receipt_timestamp=datetime.now(UTC),
            concept=concept,
            raw_text=text,
        )
