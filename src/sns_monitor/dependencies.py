# -*- coding: utf-8 -*-

import logging

from fastapi import Header, HTTPException, Request

from sns_monitor.models import MessageType

__author__ = 'lundberg'

logger = logging.getLogger(__name__)


async def verify_topic(
    request: Request, x_amz_sns_topic_arn: str = Header(...), x_amz_sns_message_type: str = Header(...)
):
    # Only check if the topic is allowed if it is a notification as we probably want to receive subscription and
    # unsubscription events
    if MessageType(x_amz_sns_message_type) is MessageType.NOTIFICATION and request.app.state.config.topic_allow_list:
        if x_amz_sns_topic_arn not in request.app.state.config.topic_allow_list:
            logger.info(f'Notification from topic {x_amz_sns_topic_arn} rejected')
            raise HTTPException(status_code=400, detail=f"Notifications from topic {x_amz_sns_topic_arn} not allowed")
