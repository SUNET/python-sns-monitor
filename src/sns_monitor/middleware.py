# -*- coding: utf-8 -*-
import json
import logging

from sns_message_validator import (
    InvalidCertURLException,
    InvalidMessageTypeException,
    InvalidSignatureVersionException,
    SignatureVerificationFailureException,
)
from starlette import status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from starlette.types import Message

from sns_monitor.message_validation import CachedSNSMessageValidator

__author__ = 'lundberg'

logger = logging.getLogger(__name__)


# Hack to be able to get request body both now and later
# https://github.com/encode/starlette/issues/495#issuecomment-513138055
async def set_body(request: Request, body: bytes):
    async def receive() -> Message:
        return {'type': 'http.request', 'body': body}

    request._receive = receive


async def get_body(request: Request) -> bytes:
    body = await request.body()
    await set_body(request, body)
    return body


class VerifySNSMessageSignature(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.message_validator = CachedSNSMessageValidator()

    async def dispatch(self, request: Request, call_next):
        # Verify message signature when we have the raw body to work with
        if 'x-amz-sns-message-id' in request.headers:
            try:
                body = json.loads(await get_body(request))
                self.message_validator.validate_message(message=body)
            except (
                InvalidMessageTypeException,
                InvalidCertURLException,
                InvalidSignatureVersionException,
                SignatureVerificationFailureException,
                ValueError,
            ) as e:
                logger.error(f'Message validation failed: {e}')
                logger.debug(f'Headers: {request.headers}')
                body = await get_body(request)
                logger.debug(f'Body: {body.decode()}')
                return PlainTextResponse('Unprocessable Entity', status.HTTP_422_UNPROCESSABLE_ENTITY)

        response = await call_next(request)
        return response
