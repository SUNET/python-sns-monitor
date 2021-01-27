# -*- coding: utf-8 -*-
import json
import logging

from fastapi import HTTPException
from sns_message_validator import (
    InvalidMessageTypeException,
    InvalidCertURLException,
    InvalidSignatureVersionException,
    SignatureVerificationFailureException,
)
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from sns_monitor.message_validation import CachedSNSMessageValidator

__author__ = 'lundberg'

logger = logging.getLogger(__name__)


class VerifySNSMessageSignature(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.message_validator = CachedSNSMessageValidator()

    async def dispatch(self, request: Request, call_next):
        # Verify message signature when we have the raw body to work with
        if 'x-amz-sns-message-id' in request.headers:
            try:
                message = json.loads(await request.body())
                self.message_validator.validate_message(message=message)
            except (
                InvalidMessageTypeException,
                InvalidCertURLException,
                InvalidSignatureVersionException,
                SignatureVerificationFailureException,
                ValueError,
            ) as e:
                logger.error(f'Message validation failed: {e}')
                logger.debug(f'Headers: {request.headers}')
                logger.debug(f'Body: {await request.body()}')
                raise HTTPException(status_code=422, detail="Unprocessable Entity")

        response = await call_next(request)
        return response
