"""PNG QR for a public page URL."""
from __future__ import annotations

import io


def page_qr_png(url: str, *, dark: bool = False) -> bytes:
    import qrcode

    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    fill = "#EEE8E2" if dark else "#050606"
    back = "#050606" if dark else "#EEE8E2"
    img = qr.make_image(fill_color=fill, back_color=back)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
