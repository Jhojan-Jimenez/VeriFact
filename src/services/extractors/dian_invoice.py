import re
from datetime import UTC, datetime

from src.api.schemas.receipt import ExtractedReceiptData
from src.core.exceptions import ExtractionFailedError
from src.domain.models import BankPlatform
from src.services.extractors.base import BaseReceiptExtractor


class DianInvoiceExtractor(BaseReceiptExtractor):
    platform = BankPlatform.DIAN_INVOICE

    def can_handle(self, text: str) -> bool:
        lower = text.lower()
        return ("dian" in lower) or ("cufe" in lower) or ("factura electr[oó]nica" in lower)

    def extract(self, text: str, qr_data: list[str] | None = None) -> ExtractedReceiptData:
        # 1. Prioritize QR data if available
        if qr_data:
            for qr in qr_data:
                if "dian.gov.co" in qr or "cufe" in qr.lower() or "numfac" in qr.lower():
                    # Parse URL params or format: NumFac=SETP990000001,ValFac=150000.00
                    num_match = re.search(r"NumFac=([^&,\s]+)", qr, re.IGNORECASE)
                    val_match = re.search(r"ValFac=([^&,\s]+)", qr, re.IGNORECASE)
                    cufe_match = re.search(r"(?:documentkey|cufe)=([a-fA-F0-9]{30,100})", qr, re.IGNORECASE)

                    ref = num_match.group(1) if num_match else (cufe_match.group(1)[:12] if cufe_match else "DIAN-QR")
                    amount = self.parse_cop_amount(val_match.group(1)) if val_match else 0

                    return ExtractedReceiptData(
                        bank_platform=self.platform,
                        reference_number=ref,
                        amount_cop=amount,
                        receipt_timestamp=datetime.now(UTC),
                        concept="Factura Electrónica DIAN",
                        raw_text=qr,
                    )

        # 2. Fallback to OCR text
        cufe_match = re.search(r"(?:cufe|factura\s*no\.?)\s*:?\s*([A-Za-z0-9\-]{5,40})", text, re.IGNORECASE)
        amount_match = re.search(r"(?:total|total\s*a\s*pagar|valor)\s*:?\s*\$\s*([\d\.,]+)", text, re.IGNORECASE)

        if not cufe_match and not amount_match:
            raise ExtractionFailedError(
                message="Could not extract DIAN electronic invoice details",
                details={"extractor": "DianInvoiceExtractor"},
            )

        reference = cufe_match.group(1).strip() if cufe_match else "DIAN-INV"
        amount_cop = self.parse_cop_amount(amount_match.group(1)) if amount_match else 0

        return ExtractedReceiptData(
            bank_platform=self.platform,
            reference_number=reference,
            amount_cop=amount_cop,
            receipt_timestamp=datetime.now(UTC),
            concept="Factura Electrónica DIAN",
            raw_text=text,
        )
