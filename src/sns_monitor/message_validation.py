# -*- coding: utf-8 -*-
import base64
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Any, Dict

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
        cached_cert = self.cached_certificates.get(cert_url)
        if cached_cert:
            # TODO: Check when cert was added and invalidate old ones
            cert = cached_cert.cert
        else:
            try:
                resp = requests.get(message.get('SigningCertURL'))
                resp.raise_for_status()  # Raise HTTPError on error codes
                pem = resp.content
            except requests.exceptions.HTTPError:
                raise SignatureVerificationFailureException('Failed to fetch cert file.')
            cert = x509.load_pem_x509_certificate(pem, default_backend())
            self.cached_certificates[cert_url] = CachedCertificate(cert=cert, added=datetime.now(timezone.utc))

        public_key = cert.public_key()
        plaintext = self._get_plaintext_to_sign(message).encode()
        signature = base64.b64decode(message.get('Signature'))
        try:
            public_key.verify(
                signature, plaintext, PKCS1v15(), SHA1(),
            )
        except InvalidSignature:
            raise SignatureVerificationFailureException('Invalid signature.')

    def validate_message(self, message: Dict[str, Any]) -> None:
        self.validate_message_type(message.get('Type'))
        self._validate_signature_version(message)
        self._validate_cert_url(message)
        self._verify_signature(message)
