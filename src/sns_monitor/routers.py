# -*- coding: utf-8 -*-

import logging

from fastapi import APIRouter, Depends, HTTPException

from sns_monitor.dependencies import verify_topic
from sns_monitor.models import MessageType, SNSMessage

__author__ = 'lundberg'

logger = logging.getLogger(__name__)

message_log_router = APIRouter(prefix='/messages', dependencies=[Depends(verify_topic)])


async def handle_subscription_confirmation(message: SNSMessage):
    logger.info('****************************************')
    logger.info(f'Timestamp: {message.timestamp}')
    logger.info(f'Subject: {message.subject}')
    logger.info(message.message)
    logger.info(f'Subscribe URL: {message.subscribe_url}')
    logger.info('****************************************')
    return 200, 'OK'


async def handle_unsubscribe_confirmation(message: SNSMessage):
    logger.info('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx')
    logger.info(f'Timestamp: {message.timestamp}')
    logger.info(f'Subject: {message.subject}')
    logger.info(message.message)
    logger.info('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx')
    return 200, 'OK'


async def handle_notification(message: SNSMessage):
    logger.info('----------------------------------------')
    logger.info(f'Timestamp: {message.timestamp}')
    logger.info(f'Message ID: {message.message_id}')
    logger.info(f'Topic: {message.topicArn}')
    logger.info(f'Subject: {message.subject}')
    logger.info(message.message)
    logger.info('----------------------------------------')
    return 200, 'OK'


@message_log_router.post('/')
async def receive_message(message: SNSMessage):
    if message.type is MessageType.NOTIFICATION:
        return await handle_notification(message=message)
    elif message.type is MessageType.SUBSCRIPTION_CONFIRMATION:
        return await handle_subscription_confirmation(message=message)
    elif message.type is MessageType.UNSUBSCRIBE_CONFIRMATION:
        return await handle_unsubscribe_confirmation(message=message)
    logger.error(f'Unhandled message type {message.type} received')
    raise HTTPException(status_code=422, detail="Unprocessable Entity")
