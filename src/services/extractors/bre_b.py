import re
from datetime import UTC, datetime

from src.api.schemas.receipt import ExtractedReceiptData
from src.core.exceptions import ExtractionFailedError
from src.domain.models import BankPlatform
from src.services.extractors.base import BaseReceiptExtractor


class BreBExtractor(BaseReceiptExtractor):
    platform = BankPlatform.BRE_B

    def can_handle(self, text: str) -> bool:
        lower = text.lower()
        return ("bre-b" in lower) or ("bre b" in lower) or ("transfiya" in lower) or ("llave" in lower and "transferencia" in lower)

    def extract(self, text: str, qr_data: list[str] | None = None) -> ExtractedReceiptData:
        # Reference (Identificador Bre-B / Código de transferencia)
        ref_match = re.search(r"(?:c[oó]digo|referencia|id\s*transacci[oó]n|aprobaci[oó]n)\s*:?\s*([A-Za-z0-9\-]{6,20})", text, re.IGNORECASE)
        if not ref_match:
            ref_match = re.search(r"\b([A-Z0-9]{8,12})\b", text)

        if not ref_match:
            raise ExtractionFailedError(
                message="Could not extract Bre-B / Transfiya reference number",
                details={"extractor": "BreBExtractor"},
            )
        reference_number = ref_match.group(1).strip()

        # Amount
        amount_match = re.search(r"(?:valor|monto|total)?\s*\$\s*([\d\.,]+)", text, re.IGNORECASE)
        if not amount_match:
            amount_match = re.search(r"\$\s*([\d\.,]+)", text)

        if not amount_match:
            raise ExtractionFailedError(
                message="Could not extract Bre-B payment amount",
                details={"extractor": "BreBExtractor"},
            )
        amount_cop = self.parse_cop_amount(amount_match.group(1))

        return ExtractedReceiptData(
            bank_platform=self.platform,
            reference_number=reference_number,
            amount_cop=amount_cop,
            receipt_timestamp=datetime.now(UTC),
            concept="Pago Interoperable Bre-B",
            raw_text=text,
        )
