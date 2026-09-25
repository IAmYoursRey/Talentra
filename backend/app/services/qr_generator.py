import io
import qrcode
from qrcode.constants import ERROR_CORRECT_M
from ..core.config import settings


class VerificationQRGenerator:
    """
    Generates scan-reliable QR codes for CV public authenticity verification.
    Strictly encodes only the public verification URL.
    Never encodes national identifiers or private user data.
    """

    @staticmethod
    def generate_verification_url(token: str, base_url: str | None = None) -> str:
        domain = (base_url or settings.public_app_url).rstrip("/")
        return f"{domain}/verify/{token}"

    @classmethod
    def generate_qr_png_bytes(cls, token: str, base_url: str | None = None, box_size: int = 8, border: int = 2) -> bytes:
        url = cls.generate_verification_url(token, base_url)
        qr = qrcode.QRCode(
            version=None,
            error_correction=ERROR_CORRECT_M,
            box_size=box_size,
            border=border,
        )
        qr.add_data(url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="#1e1b4b", back_color="#ffffff")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
