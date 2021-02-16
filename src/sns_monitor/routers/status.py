# -*- coding: utf-8 -*-

import logging

from fastapi import APIRouter, Request

__author__ = 'lundberg'


logger = logging.getLogger(__name__)

status_router = APIRouter(prefix='/status')


@status_router.get('/healthy', status_code=200)
async def receive_message(request: Request):
    logger.debug(f'{request.base_url} called')
    return {'message': 'STATUS_OK'}
