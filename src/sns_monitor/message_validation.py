# -*- coding: utf-8 -*-
import base64
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import requests
from cryptography import x509
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric.padding import PKCS1v15
from cryptography.hazmat.primitives.hashes import SHA1
from cryptography.x509.base import Certificate
from sns_message_validator import SignatureVerificationFailureException
from sns_message_validator.sns_message_validator import SNSMessageValidator

__author__ = 'lundberg'


@dataclass
class CachedCertificate:
    cert: Certificate
    added: datetime


# We should see if it is possible to validate the cert using a Amazon root cert
# but not even Amazon seems to do that.
# https://docs.aws.amazon.com/sns/latest/dg/sns-example-code-endpoint-java-servlet.html
#
# This validator checks the following:
# - Type is SubscriptionConfirmation, UnsubscribeConfirmation or Notification
# - SignatureVersion is 1
# - SigningCertURL matches regex ^https://sns\.[-a-z0-9]+\.amazonaws\.com/
# - Signature matches the key, value pairs of the plaintext signature (see _get_plaintext_to_sign)


class CachedSNSMessageValidator(SNSMessageValidator):
    def __init__(self, cert_url_regex: Optional[str] = None, signature_version: Optional[str] = None):
        kwargs = {}
        if cert_url_regex:
            kwargs['cert_url_regex'] = cert_url_regex
        if signature_version:
            kwargs['signature_version'] = signature_version
        super().__init__(**kwargs)
        self.cached_certificates: Dict[str, CachedCertificate] = {}

    def _verify_signature(self, message: Dict[str, Any]) -> None:
        cert_url = message.get('SigningCertURL')
        if not cert_url:
            raise SignatureVerificationFailureException('SigningCertURL not found')
        cached_cert = self.cached_certificates.get(cert_url)
        if cached_cert:
            # TODO: Check when cert was added and invalidate old ones
            cert = cached_cert.cert
        else:
            try:
                resp = requests.get(cert_url)
                resp.raise_for_status()  # Raise HTTPError on error codes
                pem = resp.content
            except requests.exceptions.HTTPError:
                raise SignatureVerificationFailureException('Failed to fetch cert file.')
            cert = x509.load_pem_x509_certificate(pem, default_backend())
            self.cached_certificates[cert_url] = CachedCertificate(cert=cert, added=datetime.now(timezone.utc))

        public_key = cert.public_key()
        plaintext = self._get_plaintext_to_sign(message).encode()
        b64_signature = message.get('Signature')
        if not b64_signature:
            raise SignatureVerificationFailureException('Signature not found')
        signature = base64.b64decode(b64_signature)
        try:
            public_key.verify(
                signature,
                plaintext,
                PKCS1v15(),
                SHA1(),
            )
        except InvalidSignature:
            raise SignatureVerificationFailureException('Invalid signature.')
