# -*- coding: utf-8 -*-
import logging
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl

__author__ = 'lundberg'

logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    SUBSCRIPTION_CONFIRMATION = 'SubscriptionConfirmation'
    UNSUBSCRIBE_CONFIRMATION = 'UnsubscribeConfirmation'
    NOTIFICATION = 'Notification'


class SNSMessage(BaseModel):
    class Config:
        arbitrary_types_allowed = True
        use_enum_values = True

    type: MessageType = Field(alias='Type')
    timestamp: datetime = Field(alias='Timestamp')
    topicArn: str = Field(alias='TopicArn')
    message_id: str = Field(alias='MessageId')
    subject: Optional[str] = Field(alias='Subject')
    message: str = Field(alias='Message')
    signature: str = Field(alias='Signature')
    signature_version: str = Field(alias='SignatureVersion')
    signing_cert_url: HttpUrl = Field(alias='SigningCertURL')
    # For type SUBSCRIPTION_CONFIRMATION
    subscribe_url: Optional[HttpUrl] = Field(alias='SubscribeURL')
    token: Optional[str] = Field(alias='Token')
    # For type NOTIFICATION
    unsubscribe_url: Optional[HttpUrl] = Field(alias='UnsubscribeURL')
