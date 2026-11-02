import re
from datetime import UTC, datetime

from src.api.schemas.receipt import ExtractedReceiptData
from src.core.exceptions import ExtractionFailedError
from src.domain.models import BankPlatform
from src.services.extractors.base import BaseReceiptExtractor


class GenericSlipExtractor(BaseReceiptExtractor):
    """Universal fallback extractor for unrecognized slips.

    Extracts financial figures (amount, reference, timestamp) even when the bank
    template is degraded, partial, or from an unlisted banking platform.
    """

    platform = BankPlatform.UNKNOWN

    def can_handle(self, text: str) -> bool:
        # Catch-all: handles any text that contains currency signs or digits
        return bool(re.search(r"[\$\d]", text))

    def extract(self, text: str, qr_data: list[str] | None = None) -> ExtractedReceiptData:
        lower = text.lower()

        # 1. Deduce Bank Platform flexibly
        platform = BankPlatform.UNKNOWN
        if "nequi" in lower or "@" in lower or "envio realizado" in lower or "enviaste" in lower or "¡listo!" in lower:
            platform = BankPlatform.NEQUI
        elif "daviplata" in lower or "davivienda" in lower:
            platform = BankPlatform.DAVIPLATA
        elif "bancolombia" in lower:
            platform = BankPlatform.BANCOLOMBIA
        elif "bre-b" in lower or "bre_b" in lower or "breb" in lower:
            platform = BankPlatform.BRE_B
        elif "dian" in lower or "factura electr" in lower:
            platform = BankPlatform.DIAN_INVOICE

        # 2. Extract Amount (COP)
        # Match '$ 50.000', 'Total: 50.000', '1.000,00'
        amount_match = re.search(r"\$\s*([\d\.,]+)", text)
        if not amount_match:
            amount_match = re.search(r"(?:cu[aá]nto\??|total|monto|valor|abono)\s*[:#\.\s]?\s*([\d\.,]+)", text, re.IGNORECASE)

        if not amount_match:
            # Fallback to any standalone number with thousand or decimal formatting
            amount_match = re.search(r"\b(\d{1,3}(?:[\.,]\d{3})+(?:[\.,]\d{2})?)\b", text)

        if not amount_match:
            raise ExtractionFailedError(
                message="No se pudo identificar el monto del comprobante",
                details={"text_snippet": text[:200]},
            )

        amount_cop = self.parse_cop_amount(amount_match.group(1))

        # 3. Extract Reference Number
        # Common patterns: 'Referencia M12345', 'Ref: 12345678', 'Comprobante 987654'
        ref_match = re.search(r"(?:referencia|ref\.?|hetero|comprobante|transacci[oó]n|aprobaci[oó]n|c[oó]digo)\s*[:#\.\s]?\s*([A-Za-z0-9\-]{4,25})", text, re.IGNORECASE)
        if not ref_match:
            # Try M-number pattern (typical in Nequi)
            ref_match = re.search(r"\b(M[0-9A-Za-z]{6,12})\b", text, re.IGNORECASE)
        if not ref_match:
            # Try 6-12 standalone digit sequence
            ref_match = re.search(r"\b(\d{6,12})\b", text)

        reference_number = ref_match.group(1).replace(" ", "").upper() if ref_match else "SIN_REFERENCIA"

        # 4. Extract Date / Timestamp
        receipt_time = datetime.now(UTC)

        return ExtractedReceiptData(
            bank_platform=platform,
            reference_number=reference_number,
            amount_cop=amount_cop,
            receipt_timestamp=receipt_time,
            concept=None,
            raw_text=text,
        )
