# -*- coding: utf-8 -*-

import logging

from fastapi import APIRouter

__author__ = 'lundberg'


logger = logging.getLogger(__name__)

status_router = APIRouter(prefix='/status')


@status_router.get('/healthy', status_code=200)
async def receive_message():
    return {'message': 'STATUS_OK'}
