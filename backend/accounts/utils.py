import hmac
import hashlib
import base64
from django.conf import settings


def generate_esewa_signature(amount, transaction_id):
    # MUST match signed_field_names order exactly
    message = f"total_amount={amount},transaction_uuid={transaction_id},product_code={settings.ESEWA_MERCHANT_CODE}"

    print("DEBUG MESSAGE:", message.encode())

    secret_key = settings.ESEWA_SECRET_KEY.encode()

    digest = hmac.new(
        secret_key,
        message.encode(),
        hashlib.sha256
    ).digest()

    signature = base64.b64encode(digest).decode()

    print("DEBUG SIGNATURE:", signature)

    return signature
