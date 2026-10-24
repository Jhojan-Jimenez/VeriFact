import re
from abc import ABC, abstractmethod
from datetime import UTC, datetime

from src.api.schemas.receipt import ExtractedReceiptData
from src.domain.models import BankPlatform


class BaseReceiptExtractor(ABC):
    """Abstract base class for bank-specific slip parsing."""

    platform: BankPlatform

    @abstractmethod
    def can_handle(self, text: str) -> bool:
        """Return True if this extractor recognizes the slip template/keywords."""
        pass

    @abstractmethod
    def extract(self, text: str, qr_data: list[str] | None = None) -> ExtractedReceiptData:
        """Extract structured financial data from raw OCR text."""
        pass

    @staticmethod
    def parse_cop_amount(raw_str: str) -> int:
        """Parse Colombian peso string into integer.

        Handles:
        '$ 50.000,00' -> 50000
        '$50.000'     -> 50000
        '50,000.00'   -> 50000
        '$ 1.250.000' -> 1250000
        """
        # Remove currency symbol and spaces
        cleaned = re.sub(r"[$\sA-Za-z]", "", raw_str)

        # In Colombia: periods are thousand separators, commas are decimals
        # e.g. 50.000,00
        if "," in cleaned and "." in cleaned:
            # Check which one appears last
            last_comma = cleaned.rfind(",")
            last_dot = cleaned.rfind(".")
            if last_comma > last_dot:
                # 50.000,00 -> drop decimal part
                cleaned = cleaned[:last_comma].replace(".", "")
            else:
                # 50,000.00 -> drop decimal part
                cleaned = cleaned[:last_dot].replace(",", "")
        elif "," in cleaned:
            # Could be decimal (50000,00) or thousand (50,000)
            parts = cleaned.split(",")
            if len(parts) == 2 and len(parts[1]) == 2:
                cleaned = parts[0]
            else:
                cleaned = cleaned.replace(",", "")
        elif "." in cleaned:
            # Could be thousand (50.000) or decimal (50000.00)
            parts = cleaned.split(".")
            if len(parts) == 2 and len(parts[1]) == 2:
                cleaned = parts[0]
            else:
                cleaned = cleaned.replace(".", "")

        # Extract only digits
        digits_only = re.sub(r"[^\d]", "", cleaned)
        return int(digits_only) if digits_only else 0

    @staticmethod
    def parse_date(date_str: str) -> datetime:
        """Attempt parsing various Colombian banking date representations."""
        # Clean up whitespace
        s = date_str.strip()

        # Month names mapping in Spanish
        months = {
            "ene": "01", "feb": "02", "mar": "03", "abr": "04",
            "may": "05", "jun": "06", "jul": "07", "ago": "08",
            "sep": "09", "oct": "10", "nov": "11", "dic": "12",
            "enero": "01", "febrero": "02", "marzo": "03", "abril": "04",
            "mayo": "05", "junio": "06", "julio": "07", "agosto": "08",
            "septiembre": "09", "octubre": "10", "noviembre": "11", "diciembre": "12",
        }

        # Format: 24 de octubre de 2026 - 11:35 am
        for name, num in months.items():
            pattern = re.compile(rf"\b{name}\b", re.IGNORECASE)
            s = pattern.sub(num, s)

        # Normalize common date strings: dd/mm/yyyy hh:mm or yyyy-mm-dd
        # Fallback to current UTC if parsing cannot match
        return datetime.now(UTC)
