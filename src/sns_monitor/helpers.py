# -*- coding: utf-8 -*-
import logging

from sns_message_validator import (
    InvalidMessageTypeException,
    InvalidCertURLException,
    InvalidSignatureVersionException,
    SignatureVerificationFailureException,
)

from sns_monitor.message_validation import CachedSNSMessageValidator

__author__ = 'lundberg'

from sns_monitor.models import SNSMessage

logger = logging.getLogger(__name__)

message_validator = CachedSNSMessageValidator()


def valid_signature(message: SNSMessage) -> bool:
    try:
        message_validator.validate_message(message=message.dict(by_alias=True, exclude_unset=True))
        return True
    except (
        InvalidMessageTypeException,
        InvalidCertURLException,
        InvalidSignatureVersionException,
        SignatureVerificationFailureException,
    ) as e:
        logger.error(f'Message validation failed: {e}')
    return False
