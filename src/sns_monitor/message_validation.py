# -*- coding: utf-8 -*-
import base64
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import requests
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.backends.openssl.rsa import _RSAPublicKey
from cryptography.hazmat.primitives.asymmetric.padding import PKCS1v15
from cryptography.hazmat.primitives.hashes import SHA1
from cryptography.x509 import Certificate, load_pem_x509_certificate
from eduid_common.misc.timeutil import utc_now
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
    def __init__(
        self, cert_cache_seconds: int, cert_url_regex: Optional[str] = None, signature_version: Optional[str] = None
    ):
        kwargs = {}
        if cert_url_regex:
            kwargs['cert_url_regex'] = cert_url_regex
        if signature_version:
            kwargs['signature_version'] = signature_version
        super().__init__(**kwargs)
        self.cert_cache_seconds = cert_cache_seconds
        self.cached_certificates: Dict[str, CachedCertificate] = {}

    def _verify_signature(self, message: Dict[str, Any]) -> None:
        cert = None
        cert_url = message.get('SigningCertURL')
        if not cert_url:
            raise SignatureVerificationFailureException('SigningCertURL not found')

        cached_cert = self.cached_certificates.get(cert_url)
        if cached_cert:
            # If cached cert if new enough use it
            if cached_cert.added + timedelta(seconds=self.cert_cache_seconds) > utc_now():
                cert = cached_cert.cert
            else:
                # Remove the cached cert after cert_cache_seconds
                del self.cached_certificates[cert_url]

        if cert is None:
            try:
                resp = requests.get(cert_url)
                resp.raise_for_status()  # Raise HTTPError on error codes
                pem = resp.content
            except requests.exceptions.HTTPError:
                raise SignatureVerificationFailureException('Failed to fetch cert file.')
            cert = load_pem_x509_certificate(pem, default_backend())
            self.cached_certificates[cert_url] = CachedCertificate(cert=cert, added=utc_now())

        # Explicitly type public_key to please mypy
        public_key: _RSAPublicKey = cert.public_key()
        plaintext = self._get_plaintext_to_sign(message).encode()
        b64_signature = message.get('Signature')
        if not b64_signature:
            raise SignatureVerificationFailureException('Signature not found')
        signature = base64.b64decode(b64_signature)
        try:
            public_key.verify(signature=signature, data=plaintext, algorithm=SHA1(), padding=PKCS1v15())
        except InvalidSignature:
            raise SignatureVerificationFailureException('Invalid signature.')
