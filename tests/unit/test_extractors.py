from src.domain.models import BankPlatform
from src.services.extractors.bancolombia import BancolombiaExtractor
from src.services.extractors.base import BaseReceiptExtractor
from src.services.extractors.bre_b import BreBExtractor
from src.services.extractors.daviplata import DaviplataExtractor
from src.services.extractors.dian_invoice import DianInvoiceExtractor
from src.services.extractors.nequi import NequiExtractor


def test_cop_amount_parser():
    assert BaseReceiptExtractor.parse_cop_amount("$ 50.000,00") == 50000
    assert BaseReceiptExtractor.parse_cop_amount("$50.000") == 50000
    assert BaseReceiptExtractor.parse_cop_amount("Valor: $ 1.250.000 COP") == 1250000
    assert BaseReceiptExtractor.parse_cop_amount("15,500.00") == 15500
    assert BaseReceiptExtractor.parse_cop_amount("$ 0") == 0


def test_nequi_extractor_success():
    raw_nequi = """
    ¡Listo!
    Enviaste plata a través de Nequi
    ¿Cuánto? $ 75.000,00
    Para: Jhojan Jimenez
    Referencia: M19283746
    Fecha: 24 de Octubre de 2026
    Mensaje: ORD-1002
    """
    extractor = NequiExtractor()
    assert extractor.can_handle(raw_nequi) is True

    result = extractor.extract(raw_nequi)
    assert result.bank_platform == BankPlatform.NEQUI
    assert result.reference_number == "M19283746"
    assert result.amount_cop == 75000
    assert result.concept == "ORD-1002"


def test_daviplata_extractor_success():
    raw_daviplata = """
    DaviPlata
    Transacción exitosa
    Número de aprobación: 445566
    Valor: $ 48.000
    Fecha: 24/10/2026 11:15 AM
    Motivo: Pago de almuerzo
    """
    extractor = DaviplataExtractor()
    assert extractor.can_handle(raw_daviplata) is True

    result = extractor.extract(raw_daviplata)
    assert result.bank_platform == BankPlatform.DAVIPLATA
    assert result.reference_number == "445566"
    assert result.amount_cop == 48000


def test_bancolombia_extractor_success():
    raw_bancolombia = """
    Bancolombia
    Transferencia exitosa
    Comprobante No. 892019283
    Valor transferido: $ 180.000,00
    Costo de la transacción: $ 0
    Fecha: 24 Oct 2026 - 10:45 am
    Descripción: Compra tienda
    """
    extractor = BancolombiaExtractor()
    assert extractor.can_handle(raw_bancolombia) is True

    result = extractor.extract(raw_bancolombia)
    assert result.bank_platform == BankPlatform.BANCOLOMBIA
    assert result.reference_number == "892019283"
    assert result.amount_cop == 180000


def test_dian_qr_extractor_success():
    qr_data = ["https://catalogo-vpfe.dian.gov.co/document/searchqr?documentkey=fe01928374829103847291028374829102837482&NumFac=SETP990001&ValFac=95000.00"]
    extractor = DianInvoiceExtractor()
    assert extractor.can_handle(qr_data[0]) is True

    result = extractor.extract(text="", qr_data=qr_data)
    assert result.bank_platform == BankPlatform.DIAN_INVOICE
    assert result.reference_number == "SETP990001"
    assert result.amount_cop == 95000


def test_bre_b_extractor_success():
    raw_bre_b = """
    Transferencia Bre-B
    Transfiya / Llaves
    Código de aprobación: BRE998877
    Monto: $ 32.000
    Estado: Aprobada
    """
    extractor = BreBExtractor()
    assert extractor.can_handle(raw_bre_b) is True

    result = extractor.extract(raw_bre_b)
    assert result.bank_platform == BankPlatform.BRE_B
    assert result.reference_number == "BRE998877"
    assert result.amount_cop == 32000
