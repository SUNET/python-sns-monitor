# -*- coding: utf-8 -*-
import logging
from typing import Any, Mapping, Optional

from fastapi import FastAPI

from sns_monitor.config import SNSMonitorConfig, load_config
from sns_monitor.logging import init_logging
from sns_monitor.middleware import VerifySNSMessageSignature
from sns_monitor.routers.messages import message_log_router
from sns_monitor.routers.status import status_router

__author__ = 'lundberg'

logger = logging.getLogger(__name__)


class SNSMonitor(FastAPI):
    def __init__(self, config: SNSMonitorConfig):
        super().__init__()

        self.state.config = config
        init_logging(self.state.config)


def init_sns_monitor_api(name: str = 'sns_monitor', test_config: Optional[Mapping[str, Any]] = None) -> SNSMonitor:
    config = load_config(typ=SNSMonitorConfig, app_name=name, ns='api', test_config=test_config)
    app = SNSMonitor(config=config)
    app.include_router(message_log_router)
    app.include_router(status_router)
    app.add_middleware(VerifySNSMessageSignature, cert_cache_seconds=config.cert_cache_seconds)
    return app
